"""Single concurrency, original U2 retry contract and F1's nonnegative wait."""
from copy import deepcopy
import json
import random
import time
import urllib.error

from companion.chatgpt import Transport, QUOTA
from companion.chatgpt_oauth import ChatGPTError
from companion.model import Model, DecisionError
from growthlab.records import telemetry
from p7.proxy import AuditLog, ProxyError, prepare_request
from u1_resume.client import retry_delay, TransportError
from u3.client import Client as DeepSeekClient
from u3.common import append
from .corpus import BASE

RETRY_CODES = {'upstream_http_429', 'upstream_http_502', 'upstream_http_503', 'upstream_http_504',
    'upstream_connection_error', 'TimeoutError', 'ConnectionError', 'URLError',
    'chatgpt_http_429', 'chatgpt_http_502', 'chatgpt_http_503', 'chatgpt_http_504',
    'chatgpt_connection_error', 'subscription_sharing_usage_unavailable', 'subscription_sharing_user_unavailable'}


class Client:
    def __init__(self, judge, config, *, cap):
        self.judge, self.config = judge, config
        self.folder = BASE / judge
        self.started, self.next_start, self.sampled, self.invalid_streak = time.monotonic(), 0, 0, 0
        self.cap = cap
        if config['route'] == 'chatgpt':
            self.deepseek = None
            self.audit = AuditLog(self.folder)
            self.model = Model(Transport(config['model'], synthetic=True), self.audit, route='chatgpt')
        else:
            self.deepseek = DeepSeekClient(self.folder, base=BASE, cap=cap)
            self.model, self.audit = self.deepseek.model, self.deepseek.audit

    def log(self, event, **fields):
        self.audit.write('calls.jsonl', {'event': event, 'unix_s': time.time(), 'judge': self.judge, **fields})

    def check(self):
        from u2.client import Stop
        if (BASE / 'STOP').exists():
            raise Stop('operator_stop')
        if time.monotonic() - self.started >= 3600:
            raise Stop('lane_wall_limit')
        if self.deepseek:
            self.deepseek.check()
        elif time.monotonic() - self.sampled >= 30:
            info = telemetry(); self.sampled = time.monotonic()
            self.log('telemetry', **info)
            if info['ac_online'] is not True:
                raise Stop('ac_required')

    def wait(self, target):
        while True:
            self.check()
            remaining = target - time.monotonic()
            if remaining <= 0:
                return
            time.sleep(min(.5, remaining))

    def request(self, item):
        result = deepcopy(item['original_request'])
        result.update(model=self.config['model'], reasoning=deepcopy(self.config['reasoning']),
                      max_tokens=self.config['max_tokens'])
        if result['messages'] != item['messages'] or result['response_format'] != item['response_format']:
            raise ValueError('immutable_input_changed')
        return result

    def attribute(self):
        if not self.deepseek:
            return
        from .corpus import rows
        index = BASE / 'charge_ids.jsonl'
        owned = {r.get('charge_id') for r in rows(self.folder / 'routing.jsonl')} - {None}
        seen = {r['id'] for r in rows(index)}
        for identity in sorted(owned - seen):
            append(index, {'id': identity, 'judge': self.judge})

    def call(self, item):
        from u2.client import Stop
        request = self.request(item)
        reserve = prepare_request(request, model=self.config['model'],
            provider=self.deepseek.transport.policy['provider'])[2] if self.deepseek else 0
        for attempt in (1, 2):
            self.wait(self.next_start); self.check()
            if self.deepseek and self.deepseek.cost() + reserve > self.cap:
                raise Stop('estimate_reservation_stop')
            self.next_start = time.monotonic() + 2
            def observe(event, value):
                self.log(event, input_id=item['id'], attempt=attempt, **value)
            try:
                return self.model.complete(request, observer=observe, allow_invalid=True)
            except (ProxyError, DecisionError, ChatGPTError, ValueError, TimeoutError, ConnectionError, urllib.error.URLError) as error:
                code = getattr(error, 'code', type(error).__name__)
                self.log('failure', input_id=item['id'], attempt=attempt,
                         error=error.evidence() if isinstance(error, ChatGPTError) else {'code': code})
                # A subscription quota is a pause, never a transient 429 retry.
                if code == QUOTA or code not in RETRY_CODES or attempt == 2:
                    raise Stop(code) from None
                after = getattr(error, 'retry_after', 0) or 0
                if self.deepseek:
                    from .corpus import rows
                    errors = [r for r in rows(self.folder / 'routing.jsonl') if r.get('outcome') in ('http_error', 'connection_error')]
                    after = errors[-1].get('retry_after_s', 0) if errors else 0
                try:
                    after = float(after)
                except (ValueError, TypeError):
                    after = 0
                delay = retry_delay(TransportError(code, after), random.SystemRandom().uniform(0, 3))
                self.log('retry_wait', input_id=item['id'], delay_s=delay, same_input=True)
                self.wait(time.monotonic() + delay)
            finally:
                self.attribute()

    def parsed(self, valid):
        from u2.client import Stop
        self.invalid_streak = 0 if valid else self.invalid_streak + 1
        if self.invalid_streak >= 2:
            raise Stop('two_consecutive_invalid_outputs')
