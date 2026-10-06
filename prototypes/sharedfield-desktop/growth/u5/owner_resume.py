"""Owner's one-input, one-retry amendment; original U5 freeze is untouched."""
import argparse
import json
import time
import urllib.error
from unittest.mock import patch
from companion.chatgpt_oauth import file_lock
from companion.model import DecisionError
from p7.proxy import ProxyError, prepare_request
from u2.client import Stop
from u3.common import read, write, sha, utc, cost
from . import run as runner
from .client import Client as FrozenClient, request_bound
from .corpus import BASE, OUT, rows

FAILED_ID = 'b/3/feedback_control/3-07-test-2'
AMENDMENT = OUT / 'OWNER_RETRY_ONCE.json'


def freeze_amendment():
    parent = runner.verify()
    old = read(BASE/'D0/STATUS.json')
    assert old['stop'] == 'upstream_unavailable' and old['completed'] == 392
    events = rows(BASE/'D0/calls.jsonl')
    failures = [e for e in events if e['event'] == 'failure']
    assert len(failures) == 1 and failures[0]['input_id'] == FAILED_ID and failures[0]['attempt'] == 1
    assert FAILED_ID not in {r['id'] for r in rows(BASE/'D0/decisions.jsonl')}
    item = next(i for i in rows(OUT/'INPUTS.jsonl') if i['id'] == FAILED_ID)
    adapter = FrozenClient.__new__(FrozenClient)
    adapter.config = parent['judges']['D0']
    old_request = next(e['request'] for e in events if e['event'] == 'request' and e['input_id'] == FAILED_ID)
    assert adapter.request(item) == old_request
    value = {'at_utc': utc(), 'parent_manifest_sha256': sha(runner.FROZEN),
        'owner_authorization_verbatim': '允许这条重试一次，再继续',
        'authorized_input_id': FAILED_ID, 'authorized_judge': 'D0', 'additional_attempts': 1,
        'attempt_number': 2, 'unknown_reserve_retained_usd': .086888,
        'before_calls_sha256': sha(BASE/'D0/calls.jsonl'),
        'before_decisions_sha256': sha(BASE/'D0/decisions.jsonl'),
        'before_decisions': 392, 'before_new_decisions': 257, 'before_cost_usd': cost(BASE/'charge_ids.jsonl'),
        'messages_sha256': item['messages_sha256'], 'schema_sha256': item['schema_sha256'],
        'driver_sha256': sha(__file__),
        'unchanged': ['input corpus', 'judge configurations', 'memory constructions', 'criteria', 'scores', 'seeds',
                      'cost projection and daily budget', 'all other automatic retry and stop rules'],
        'new_failure_rule': 'No automatic third attempt. Any error on this extra attempt stops; no duplicate successful output.'}
    write(AMENDMENT, value, exclusive=True)
    return value


class ResumeClient(FrozenClient):
    def call(self, item):
        if item['id'] != FAILED_ID:
            return super().call(item)
        request = self.request(item)
        with request_bound(self.manifest['request_byte_cap']):
            reserve = prepare_request(request, model=self.config['model'], provider=self.deepseek.transport.policy['provider'])[2]
            self.wait(self.next_start)
            self.check()
            if self.deepseek.cost()+reserve > self.cap:
                raise Stop('estimate_reservation_stop')
            self.next_start = time.monotonic()+2
            def observe(event, value):
                self.log(event, input_id=item['id'], attempt=2, owner_authorized_retry=True, **value)
            try:
                return self.model.complete(request, observer=observe, allow_invalid=True)
            except (ProxyError, DecisionError, ValueError, TimeoutError, ConnectionError, urllib.error.URLError) as error:
                code = getattr(error, 'code', type(error).__name__)
                self.log('failure', input_id=item['id'], attempt=2, owner_authorized_retry=True, error={'code': code})
                raise Stop(code) from None
            finally:
                self.attribute()


def resume_once():
    amendment = read(AMENDMENT)
    assert amendment['driver_sha256'] == sha(__file__)
    assert amendment['parent_manifest_sha256'] == sha(runner.FROZEN)
    assert amendment['before_calls_sha256'] == sha(BASE/'D0/calls.jsonl')
    assert amendment['before_decisions_sha256'] == sha(BASE/'D0/decisions.jsonl')
    # The owner grant itself is one-shot, separate from the scientific claim.
    with file_lock(BASE/'runner.lock'):
        write(BASE/'owner_retry_once_claim.json', {'state': 'consumed', 'at_utc': utc(),
              'amendment_sha256': sha(AMENDMENT)}, exclusive=True)
        with patch.object(runner, 'Client', ResumeClient), patch.object(runner, 'RESUMABLE', runner.RESUMABLE | {'upstream_unavailable'}):
            runner.run('D0', resume=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('freeze', 'run'))
    args = parser.parse_args()
    if args.operation == 'freeze':
        v = freeze_amendment()
        print(json.dumps({'amendment_sha256': sha(AMENDMENT), 'authorized_input': v['authorized_input_id'], 'additional_attempts': 1}))
    else:
        resume_once()
