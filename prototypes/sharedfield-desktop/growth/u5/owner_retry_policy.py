"""Owner-authorized second attempts; scientific freeze and budget stay intact."""
import argparse
import json
import random
import time
import urllib.error
from pathlib import Path
from unittest.mock import patch

from companion.chatgpt_oauth import ChatGPTError, file_lock
from companion.model import DecisionError
from p7.proxy import ProxyError, prepare_request
from u1_resume.client import retry_delay, TransportError
from u2.client import Stop
from u3.common import read, write, sha, utc, cost, budget_snapshot
from u4 import client as inherited
from . import run as runner
from .client import Client as FrozenClient, request_bound
from .corpus import BASE, OUT, rows

AMENDMENT = OUT / 'OWNER_RETRY_POLICY.json'
CURRENT_ID = 'b/3/feedback_control/3-14-test-2'
EXTRA_CODE = 'upstream_unavailable'


def next_attempt(events, identity):
    relevant = [e for e in events if e.get('input_id') == identity]
    requests = [e for e in relevant if e['event'] == 'request']
    if not requests:
        return 1
    if len(requests) != 1 or requests[0]['attempt'] != 1:
        raise Stop('retry_limit_reached:' + identity)
    responses = [e for e in relevant if e['event'] == 'response']
    failures = [e for e in relevant if e['event'] == 'failure']
    if len(responses) != 1 or len(failures) != 1 or failures[0]['attempt'] != 1:
        raise Stop('uncertain_consumed_decision:' + identity)
    if not responses[0]['meta'].get('error'):
        raise Stop('completed_output_must_not_replay:' + identity)
    if failures[0]['error']['code'] not in inherited.RETRY_CODES | {EXTRA_CODE}:
        raise Stop('nonretryable_failure:' + identity)
    return 2


def diagnostic_open(original, log, identity):
    def wrapped(*args, **kwargs):
        try:
            return original(*args, **kwargs)
        except Exception as error:
            # Never serialize exception text, arguments, requests or headers.
            fields = {'exception_type': type(error).__name__}
            number = getattr(error, 'errno', None)
            if isinstance(number, int):
                fields['errno'] = number
            log('transport_exception_type', input_id=identity(), **fields)
            raise
    return wrapped


class PolicyClient(FrozenClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_input_id = None
        self.deepseek.transport._open = diagnostic_open(
            self.deepseek.transport._open, self.log, lambda: self.current_input_id)

    def call(self, item):
        self.current_input_id = item['id']
        events = rows(self.folder/'calls.jsonl')
        attempt = next_attempt(events, item['id'])
        if attempt == 1:
            with patch.object(inherited, 'RETRY_CODES', inherited.RETRY_CODES | {EXTRA_CODE}):
                return super().call(item)
        request = self.request(item)
        old_request = next(e['request'] for e in events
                           if e['event'] == 'request' and e['input_id'] == item['id'])
        if old_request != request:
            raise Stop('retry_input_changed')
        # A stopped process cannot reset the attempt counter. This is attempt 2,
        # once only, including when a lane or budget stop interrupted backoff.
        last_failure = next(e for e in reversed(events)
                            if e['event'] == 'failure' and e.get('input_id') == item['id'])
        waits = [e for e in events if e['event'] == 'retry_wait'
                 and e.get('input_id') == item['id'] and e['unix_s'] >= last_failure['unix_s']]
        if waits:
            target = waits[-1]['unix_s'] + waits[-1]['delay_s']
        else:
            errors = [e for e in rows(self.folder/'routing.jsonl')
                      if e.get('outcome') in ('http_error', 'connection_error')]
            after = errors[-1].get('retry_after_s', 0) if errors else 0
            try:
                after = float(after)
            except (ValueError, TypeError):
                after = 0
            delay = retry_delay(TransportError(last_failure['error']['code'], after),
                                random.SystemRandom().uniform(0, 3))
            target = last_failure['unix_s'] + delay
        remaining = max(0, target - time.time())
        self.log('retry_wait', input_id=item['id'], delay_s=remaining,
                 same_input=True, owner_authorized_retry=True, resumed_attempt=2)
        self.wait(time.monotonic() + remaining)
        with request_bound(self.manifest['request_byte_cap']):
            reserve = prepare_request(request, model=self.config['model'],
                provider=self.deepseek.transport.policy['provider'])[2]
            self.wait(self.next_start)
            self.check()
            if self.deepseek.cost() + reserve > self.cap:
                raise Stop('estimate_reservation_stop')
            self.next_start = time.monotonic() + 2
            def observe(event, value):
                self.log(event, input_id=item['id'], attempt=2,
                         owner_authorized_retry=True, **value)
            try:
                return self.model.complete(request, observer=observe, allow_invalid=True)
            except (ProxyError, DecisionError, ChatGPTError, ValueError, TimeoutError,
                    ConnectionError, urllib.error.URLError) as error:
                code = getattr(error, 'code', type(error).__name__)
                self.log('failure', input_id=item['id'], attempt=2,
                         owner_authorized_retry=True, error={'code': code})
                raise Stop(code) from None
            finally:
                self.attribute()


def freeze():
    runner.verify()
    status = read(BASE/'D1/STATUS.json')
    assert status['completed'] == 14 and status['stop'] == EXTRA_CODE
    assert next_attempt(rows(BASE/'D1/calls.jsonl'), CURRENT_ID) == 2
    value = {'at_utc': utc(), 'parent_manifest_sha256': sha(runner.FROZEN),
        'driver_sha256': sha(__file__), 'tests_sha256': sha(Path(__file__).with_name('test_owner_retry_policy.py')),
        'owner_authorization_verbatim': '可以都重试一次',
        'owner_route_clarification_verbatim': 'U5 按冻结配置继续，以后优先 OAuth',
        'scope': 'Current and future U5 upstream_unavailable errors may get one unchanged-input retry. At most two total requests per input, including historical failed requests. No replay of successful or uncertain in-flight requests.',
        'authorized_error_code': EXTRA_CODE, 'maximum_attempts_per_input': 2,
        'current_judge': 'D1', 'current_input': CURRENT_ID, 'current_next_attempt': 2,
        'before_completed': 14, 'before_calls_sha256': sha(BASE/'D1/calls.jsonl'),
        'before_decisions_sha256': sha(BASE/'D1/decisions.jsonl'),
        'before_calls_bytes': (BASE/'D1/calls.jsonl').stat().st_size,
        'before_decisions_bytes': (BASE/'D1/decisions.jsonl').stat().st_size,
        'D0_decisions_sha256': sha(BASE/'D0/decisions.jsonl'),
        'D0_calls_sha256': sha(BASE/'D0/calls.jsonl'),
        'before_cost_usd': cost(BASE/'charge_ids.jsonl'), 'before_daily_budget': budget_snapshot(),
        'unknown_reserves_retained_usd': .18817,
        'diagnostic_logging': 'Only exception class name and integer errno. No exception text, arguments, request objects, credentials or headers.',
        'unchanged': ['all scientific inputs and seeds', 'models and routing', 'scoring and thresholds',
            'single concurrency', 'U4 timeout and backoff', 'invalid-output handling',
            'unknown reserve accounting', '$2 projection stop', '$4 shared daily budget',
            'all other retry and stop rules']}
    write(AMENDMENT, value, exclusive=True)
    return value


def verify():
    import hashlib
    value = read(AMENDMENT)
    assert value['parent_manifest_sha256'] == sha(runner.FROZEN)
    assert value['driver_sha256'] == sha(__file__)
    assert value['tests_sha256'] == sha(Path(__file__).with_name('test_owner_retry_policy.py'))
    for name in ('calls', 'decisions'):
        with (BASE/f'D1/{name}.jsonl').open('rb') as stream:
            prefix = stream.read(value[f'before_{name}_bytes'])
        assert hashlib.sha256(prefix).hexdigest() == value[f'before_{name}_sha256']
        assert value[f'D0_{name}_sha256'] == sha(BASE/f'D0/{name}.jsonl')
    runner.verify()
    return value


def run():
    verify()
    with file_lock(BASE/'runner.lock'):
        while True:
            prior = read(BASE/'D1/STATUS.json')
            if prior['state'] == 'complete':
                return
            if prior.get('stop') == EXTRA_CODE:
                manifest = runner.verify()
                completed = runner.load_decisions(BASE/'D1')
                identity = next(i for i in manifest['order']['D1'] if i not in completed)
                assert next_attempt(rows(BASE/'D1/calls.jsonl'), identity) == 2
            with patch.object(runner, 'Client', PolicyClient), patch.object(
                    runner, 'RESUMABLE', runner.RESUMABLE | {EXTRA_CODE}):
                runner.run('D1', resume=True)
            status = read(BASE/'D1/STATUS.json')
            if status.get('stop') != 'lane_wall_limit':
                return
            # The inherited one-hour wall limit segments execution; it does
            # not authorize a new model, input, budget, or failed third request.
            print(json.dumps({'lane_restart': 'D1', 'completed': status['completed']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('freeze', 'verify', 'run'))
    args = parser.parse_args()
    if args.operation == 'run':
        run()
    else:
        value = freeze() if args.operation == 'freeze' else verify()
        print(json.dumps({'amendment_sha256': sha(AMENDMENT),
            'maximum_attempts_per_input': value['maximum_attempts_per_input']}))
