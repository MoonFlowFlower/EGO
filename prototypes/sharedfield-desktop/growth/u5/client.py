"""U4 transport/retry semantics, separate U5 attribution and cost projection."""
import time
from contextlib import contextmanager
from unittest.mock import patch
from collections import defaultdict
from p7 import proxy
from u2.client import Stop
from u3.client import Client as DeepSeekClient
from u3.common import append, cost
from u4.client import Client as U4Client
from .corpus import BASE, rows


@contextmanager
def request_bound(maximum):
    # Only the single U5 runner process changes its validation ceiling. The
    # caller bound is measured from frozen requests, never from an API result.
    # All field validation, output limits, route and budget checks are retained.
    with patch.object(proxy, 'MAX_REQUEST_BYTES', maximum):
        yield


def stratum(item):
    return item['domain'] + '/' + item.get('arm', '')


def projection(manifest, inputs, decisions, actual):
    result, estimate = {}, actual
    for judge in ('D0', 'D1'):
        groups = defaultdict(list)
        for identity in manifest['new_order'][judge]:
            groups[stratum(inputs[identity])].append(identity)
        for group, ids in groups.items():
            done = [decisions.get(judge, {}).get(i) for i in ids]
            observed = [r['meta']['cost_usd'] for r in done if r is not None and r['meta'].get('cost_usd') is not None]
            rate = sum(observed) / len(observed) if observed else (.01/30 if group.startswith('noise') else .35/451 if judge == 'D0' else 1.1/586)
            remaining = sum(r is None for r in done)
            estimate += remaining * rate
            result[judge + '/' + group] = {'planned': len(ids), 'completed': len(ids)-remaining,
                                          'observed_cost_n': len(observed), 'rate_usd': rate,
                                          'remaining_estimate_usd': remaining*rate}
    return {'actual_usd': actual, 'projected_total_usd': estimate, 'strata': result,
            'stop': estimate > manifest['dollar_cap_usd']}


class Client(U4Client):
    def __init__(self, judge, manifest, inputs, decisions):
        self.judge, self.config = judge, manifest['judges'][judge]
        self.folder = BASE / judge
        self.started, self.next_start, self.sampled, self.invalid_streak = time.monotonic(), 0, 0, 0
        self.cap = manifest['dollar_cap_usd']
        self.manifest, self.inputs, self.decisions = manifest, inputs, decisions
        self.deepseek = DeepSeekClient(self.folder, base=BASE, cap=self.cap)
        self.model, self.audit = self.deepseek.model, self.deepseek.audit

    def call(self, item):
        with request_bound(self.manifest['request_byte_cap']):
            return super().call(item)

    def check(self):
        self.deepseek.check()
        estimate = projection(self.manifest, self.inputs, self.decisions, self.deepseek.cost())
        if estimate['stop']:
            from u3.common import write, utc
            write(BASE / 'COST_STOP.json', {'at_utc': utc(), **estimate})
            raise Stop('projected_cost_exceeds_2_usd_requires_owner')

    def attribute(self):
        index = BASE / 'charge_ids.jsonl'
        owned = {r.get('charge_id') for r in rows(self.folder / 'routing.jsonl')} - {None}
        seen = {r['id'] for r in rows(index)}
        for identity in sorted(owned - seen):
            append(index, {'id': identity, 'judge': self.judge})
