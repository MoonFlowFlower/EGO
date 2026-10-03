"""Fixed-route U1 client with bounded pacing and Retry-After aware waiting."""
import json
import random
import time
import urllib.error
import urllib.request
from pathlib import Path

from growthlab import models
from growthlab.records import ROOT
from p7.proxy import _NoRedirect
from p7.routing import retry_after_seconds
from u1.harness import Client as OriginalClient, Stop


class TransportError(RuntimeError):
    def __init__(self, code, retry_after=0):
        super().__init__(code)
        self.retry_after = retry_after


def retry_delay(error, jitter):
    return max(30.0, error.retry_after) + jitter


class Client(OriginalClient):
    def __init__(self, config, folder):
        self.folder, self.config = Path(folder), config
        self.folder.mkdir(parents=True, exist_ok=True)
        self.started = time.time()
        self.previous_sample = self.invalid_streak = self.calls = 0
        self.next_start = self.metadata_at = 0
        self._open = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect()).open
        self.check_resources()
        self.cloud = models.Cloud(model=config['model'], route=config['route'],
                                  budget_path=ROOT / 'runs/phase1/budget.sqlite', limit=5)
        self.original_request = models.request_json
        models.request_json = self.request

    def wait_until(self, target):
        while time.time() < target:
            self.check_resources()
            time.sleep(min(1, max(0, target - time.time())))

    def refresh(self):
        if time.time() - self.metadata_at < 60:
            return
        req = urllib.request.Request('https://openrouter.ai/api/v1/endpoints/zdr')
        try:
            with self._open(req, timeout=20) as response:
                rows = json.load(response)['data']
        except Exception:
            raise Stop('route_preflight_unavailable') from None
        found = [r for r in rows if r.get('model_id') == self.config['model']
                 and r.get('tag') == self.config['route']]
        required = {'reasoning', 'temperature', 'max_tokens', 'response_format'}
        if not found or not all(required <= set(r.get('supported_parameters', []))
                and 0 <= float(r['pricing']['prompt']) <= 1e-6
                and 0 <= float(r['pricing']['completion']) <= 2e-6
                and float(r['pricing'].get('request', 0)) == 0 for r in found):
            raise Stop('route_preflight_rejected')
        self.metadata_at = time.time()
        self.log({'record_type': 'preflight', 'config': self.config, 'zdr_listed': True})

    def request(self, url, payload, headers=None, timeout=60):
        self.log({'record_type': 'wire_request', 'url': url, 'payload': payload})
        req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                     headers={'Content-Type': 'application/json', **(headers or {})})
        try:
            with self._open(req, timeout=60) as response:
                raw = response.read(4_000_001)
            if len(raw) > 4_000_000:
                raise TransportError('response_size_stop')
            value = json.loads(raw)
        except urllib.error.HTTPError as error:
            after = retry_after_seconds(error.headers.get('Retry-After') if error.headers else None, time.time())
            code = 'http_' + str(error.code)
            error.close()
            raise TransportError(code, after) from None
        except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
            raise TransportError(type(error).__name__) from None
        self.log({'record_type': 'wire_response', 'response': value})
        return value

    def call(self, messages, schema, context, *, sleep=False):
        tokens = 8192 if self.config['reasoning'] else (2048 if sleep else 1024)
        for attempt in (1, 2):
            self.wait_until(self.next_start)
            self.check_resources()
            self.refresh()
            before = {r[0] for r in self.cloud.db.execute('SELECT id FROM charges')}
            self.log({'record_type': 'request', 'context': context, 'attempt': attempt,
                      'messages': messages, 'response_format': schema, 'max_tokens': tokens,
                      'reasoning': self.config['reasoning'], 'config': self.config})
            started = time.perf_counter()
            self.next_start = time.time() + self.config['minimum_start_interval_s']
            try:
                output, meta = self.cloud.decide(messages, response_format=schema,
                                                 max_tokens=tokens, reasoning=self.config['reasoning'])
            except (RuntimeError, ValueError, KeyError, IndexError, TypeError) as error:
                code = str(error) if isinstance(error, (TransportError, ValueError)) else type(error).__name__
                deltas = [dict(zip(('charge_id', 'usd', 'status'), r))
                          for r in self.cloud.db.execute('SELECT id,usd,status FROM charges') if r[0] not in before]
                self.log({'record_type': 'transport_error', 'context': context, 'attempt': attempt,
                          'error': code, 'latency_s': time.perf_counter() - started,
                          'shared_ledger_delta_unattributed': deltas})
                eligible = isinstance(error, TransportError) and code in {
                    'http_429', 'http_502', 'http_503', 'http_504', 'TimeoutError', 'URLError', 'ConnectionError'}
                if not eligible or attempt == 2:
                    raise Stop(code) from None
                delay = retry_delay(error, random.SystemRandom().uniform(0, 3))
                if time.time() + delay - self.started >= 3600:
                    raise Stop('retry_after_exceeds_lane_window') from None
                self.log({'record_type': 'retry_wait', 'context': context, 'delay_s': delay,
                          'retry_after_s': error.retry_after, 'same_input': True})
                self.wait_until(time.time() + delay)
                continue
            self.calls += 1
            self.log({'record_type': 'response', 'context': context, 'attempt': attempt, 'output': output, 'meta': meta})
            return output, meta
