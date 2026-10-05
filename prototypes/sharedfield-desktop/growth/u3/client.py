"""U2 request/retry contract, with an isolated U3 cost index and stop file."""
import json
import os
import random
import time
import urllib.error
from pathlib import Path

from companion.budget import DailyLedger, DAILY_LIMIT
from companion.model import Model, DecisionError
from growthlab.models import read_key
from growthlab.records import telemetry
from p7.proxy import AuditLog, DEFAULT_BUDGET, ProxyError, prepare_request
from p7.routing_v2 import RoutedTransportV2
from u1_resume.client import retry_delay, TransportError
from u2.client import Stop, append
from .common import BASE, cost
from .protocol import MODEL, ROUTE, ESTIMATE_USD


class Client:
    def __init__(self, folder, *, cap=ESTIMATE_USD, base=BASE):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.base, self.cap = Path(base), cap
        self.started = time.monotonic()
        self.next_start = self.sampled = self.invalid_streak = 0
        key = read_key()
        self.audit = AuditLog(self.folder, (key,))
        self.transport = RoutedTransportV2(api_key=key, mode='pinned', route_index=0,
            budget_path=DEFAULT_BUDGET, limit=DAILY_LIMIT, log_dir=self.folder)
        self.transport.timeout = 60
        self.transport.ledger = DailyLedger(DEFAULT_BUDGET)
        self.transport.set_audit(self.audit)
        if (self.transport.model, self.transport.route) != (MODEL, ROUTE):
            raise Stop('model_route_changed')
        self.model = Model(self.transport, self.audit)

    def log(self, event, **fields):
        self.audit.write('calls.jsonl', {'event': event, 'unix_s': time.time(), 'pid': os.getpid(), **fields})

    def cost(self):
        return cost(self.base / 'charge_ids.jsonl', self.transport.ledger.path)

    def check(self):
        if (self.base / 'STOP').exists():
            raise Stop('operator_stop')
        if time.monotonic() - self.started >= 3600:
            raise Stop('lane_wall_limit')
        if self.cost() > self.cap:
            raise Stop('actual_exceeded_estimate')
        if time.monotonic() - self.sampled >= 30:
            info = telemetry()
            self.sampled = time.monotonic()
            self.log('telemetry', **info)
            if info['ac_online'] is not True:
                raise Stop('ac_required')

    def wait(self, target):
        while time.monotonic() < target:
            self.check()
            time.sleep(min(.5, target-time.monotonic()))

    def call(self, messages, context, *, schema):
        request = {'model': MODEL, 'stream': False, 'temperature': 0, 'max_tokens': 1024,
                   'reasoning': {'enabled': False}, 'response_format': schema, 'messages': messages}
        _, _, reserve = prepare_request(request, model=MODEL, provider=self.transport.policy['provider'])
        for attempt in (1, 2):
            self.wait(self.next_start)
            self.check()
            if self.cost() + reserve > self.cap:
                raise Stop('estimate_reservation_stop')
            self.next_start = time.monotonic() + 2
            def observe(event, value):
                self.log(event, context=context, attempt=attempt, **value)
            try:
                output, meta = self.model.complete(request, observer=observe, allow_invalid=True)
            except (ProxyError, DecisionError, ValueError, TimeoutError, ConnectionError, urllib.error.URLError) as error:
                code = getattr(error, 'code', type(error).__name__)
                self.log('failure', context=context, attempt=attempt, error=code)
                retryable = code in {'upstream_http_429', 'upstream_http_502', 'upstream_http_503',
                    'upstream_http_504', 'upstream_connection_error', 'TimeoutError', 'ConnectionError', 'URLError'}
                if not retryable or attempt == 2:
                    raise Stop(code) from None
                after = 0
                routing = self.folder / 'routing.jsonl'
                if routing.exists():
                    for line in reversed(routing.read_text(encoding='utf-8').splitlines()):
                        row = json.loads(line)
                        if row.get('outcome') in ('http_error', 'connection_error'):
                            after = row.get('retry_after_s', 0)
                            break
                delay = retry_delay(TransportError(code, after), random.SystemRandom().uniform(0, 3))
                self.log('retry_wait', context=context, delay_s=delay, same_input=True)
                self.wait(time.monotonic()+delay)
                continue
            finally:
                # Attribute only IDs from this client's routing audit, including
                # unknown reserves. Never claim another process's ledger delta.
                routing = self.folder / 'routing.jsonl'
                seen = set()
                index = self.base / 'charge_ids.jsonl'
                if index.exists():
                    seen = {json.loads(s)['id'] for s in index.read_text(encoding='utf-8').splitlines()}
                if routing.exists():
                    owned = {json.loads(s).get('charge_id') for s in routing.read_text(encoding='utf-8').splitlines()} - {None}
                    for identity in sorted(owned-seen):
                        append(index, {'id': identity})
            if self.cost() > self.cap:
                raise Stop('actual_exceeded_estimate')
            return output, meta

    def parsed(self, valid):
        self.invalid_streak = 0 if valid else self.invalid_streak+1
        if self.invalid_streak >= 2:
            raise Stop('two_consecutive_invalid_outputs')
