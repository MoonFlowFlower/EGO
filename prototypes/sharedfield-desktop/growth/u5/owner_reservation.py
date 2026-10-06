"""Owner-authorized $4 reservation headroom, unchanged $2 projection gate."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

from p7.proxy import prepare_request
from p7.routing_v2 import configuration
from u3.common import read, write, sha, utc, cost
from . import owner_retry_policy as policy
from . import run as runner
from .client import projection, request_bound
from .corpus import BASE, OUT, rows

LIMIT = 4.0
PROPOSAL = OUT/'RESERVATION_PROPOSAL.json'
AMENDMENT = OUT/'OWNER_RESERVATION_LIMIT.json'


class ReservationClient(policy.PolicyClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.manifest['dollar_cap_usd'] == 2.0
        self.cap = LIMIT
        self.deepseek.cap = LIMIT
        # Client.check() still projects with the original manifest's $2 gate.
        # The shared transport ledger still enforces the original $4/day.


def proposal():
    manifest = runner.verify()
    policy.verify()
    status = read(BASE/'D1/STATUS.json')
    assert status['stop'] == 'estimate_reservation_stop' and status['completed'] == 566
    inputs = {i['id']: i for i in rows(OUT/'INPUTS.jsonl')}
    decisions = {j: runner.load_decisions(BASE/j) for j in ('D0', 'D1')}
    remaining = [i for i in manifest['order']['D1'] if i not in decisions['D1']]
    adapter = runner.Client.__new__(runner.Client)
    adapter.config = manifest['judges']['D1']
    with request_bound(manifest['request_byte_cap']):
        reserves = [{'id': i, 'reserve_usd': prepare_request(adapter.request(inputs[i]),
            model=adapter.config['model'], provider=configuration()['policy']['provider'])[2]}
            for i in remaining]
    actual = cost(BASE/'charge_ids.jsonl')
    estimate = projection(manifest, inputs, decisions, actual)['projected_total_usd']
    value = {'at_utc': utc(), 'state': 'awaiting_owner', 'remaining': len(remaining),
        'parent_manifest_sha256': sha(runner.FROZEN), 'retry_policy_sha256': sha(policy.AMENDMENT),
        'driver_sha256': sha(__file__), 'tests_sha256': sha(Path(__file__).with_name('test_owner_reservation.py')),
        'before_calls_sha256': sha(BASE/'D1/calls.jsonl'),
        'before_decisions_sha256': sha(BASE/'D1/decisions.jsonl'),
        'before_calls_bytes': (BASE/'D1/calls.jsonl').stat().st_size,
        'before_decisions_bytes': (BASE/'D1/decisions.jsonl').stat().st_size,
        'completed': 566, 'accounted_usd': actual, 'projected_usd': estimate,
        'next_input_id': remaining[0], 'next_reserve_usd': reserves[0]['reserve_usd'],
        'next_accounted_plus_reserve_usd': actual + reserves[0]['reserve_usd'],
        'remaining_reserves': reserves,
        'projected_total_plus_largest_remaining_reserve_usd': estimate + max(r['reserve_usd'] for r in reserves),
        'proposed_request_reservation_ceiling_usd': LIMIT,
        'unchanged_projection_stop_usd': 2.0, 'unchanged_daily_budget_usd': 4.0,
        'scope': f'Only the conservative per-request reservation headroom changes from $2 to ${LIMIT:g}. Total actual-plus-remaining projection above $2 still stops before the next request. Existing unknown reserves remain included. Inputs, judges, scoring, retry limits and concurrency are unchanged.'}
    write(PROPOSAL, value, exclusive=True)
    return value


def approve(quote):
    value = read(PROPOSAL)
    archive = OUT/'preflight_versions/reservation_2_05_proposal'
    assert value['driver_sha256'] == sha(archive/'owner_reservation.py')
    assert value['tests_sha256'] == sha(archive/'test_owner_reservation.py')
    assert value['before_calls_sha256'] == sha(BASE/'D1/calls.jsonl')
    assert value['before_decisions_sha256'] == sha(BASE/'D1/decisions.jsonl')
    value.update(state='owner_authorized', owner_authorization_verbatim=quote, authorized_at_utc=utc(),
        original_proposal_sha256=sha(PROPOSAL), proposed_driver_sha256=value['driver_sha256'],
        proposed_tests_sha256=value['tests_sha256'], proposal_scope=value['scope'],
        driver_sha256=sha(__file__), tests_sha256=sha(Path(__file__).with_name('test_owner_reservation.py')),
        authorized_request_reservation_ceiling_usd=LIMIT,
        scope='Owner authorized the request reservation ceiling at $4 instead of the proposed $2.05. The original $2 total projection stop and $4 shared daily ledger remain unchanged; no input, judge, scoring or retry changes.')
    write(AMENDMENT, value, exclusive=True)
    return value


def verify():
    import hashlib
    value = read(AMENDMENT)
    assert value['state'] == 'owner_authorized'
    assert value['authorized_request_reservation_ceiling_usd'] == LIMIT
    assert value['original_proposal_sha256'] == sha(PROPOSAL)
    archive = OUT/'preflight_versions/reservation_2_05_proposal'
    assert value['proposed_driver_sha256'] == sha(archive/'owner_reservation.py')
    assert value['proposed_tests_sha256'] == sha(archive/'test_owner_reservation.py')
    assert value['parent_manifest_sha256'] == sha(runner.FROZEN)
    assert value['retry_policy_sha256'] == sha(policy.AMENDMENT)
    assert value['driver_sha256'] == sha(__file__)
    assert value['tests_sha256'] == sha(Path(__file__).with_name('test_owner_reservation.py'))
    for name in ('calls', 'decisions'):
        with (BASE/f'D1/{name}.jsonl').open('rb') as stream:
            prefix = stream.read(value[f'before_{name}_bytes'])
        assert hashlib.sha256(prefix).hexdigest() == value[f'before_{name}_sha256']
    policy.verify()
    return value


def run():
    verify()
    with patch.object(policy, 'PolicyClient', ReservationClient), patch.object(
            runner, 'RESUMABLE', runner.RESUMABLE | {'estimate_reservation_stop'}):
        policy.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('proposal', 'approve', 'verify', 'run'))
    parser.add_argument('--authorization')
    args = parser.parse_args()
    if args.operation == 'run':
        run()
    elif args.operation == 'approve':
        assert args.authorization
        print(json.dumps(approve(args.authorization), ensure_ascii=False))
    else:
        value = proposal() if args.operation == 'proposal' else verify()
        print(json.dumps({'remaining': value['remaining'], 'projected_usd': value['projected_usd'],
            'reservation_ceiling_usd': value.get('authorized_request_reservation_ceiling_usd', value['proposed_request_reservation_ceiling_usd']),
            'projection_stop_usd': value['unchanged_projection_stop_usd']}))
