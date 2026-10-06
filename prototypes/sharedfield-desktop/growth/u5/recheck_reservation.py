"""Post-run audit of the owner-authorized final 20 calls; no model calls."""
import hashlib
import json

from u3.common import read, sha, utc, write
from . import owner_reservation
from . import run as runner
from .corpus import BASE, OUT, rows


def audit():
    manifest = runner.verify()
    amendment = owner_reservation.verify()
    closure = read(OUT / 'CLOSURE.json')
    commit_audit = read(OUT / 'RESERVATION_PRECALL_COMMIT_AUDIT.json')
    assert commit_audit['committed_before_request']
    for relative, digest in commit_audit['source_and_authorization_bytes_match_commit'].items():
        assert sha(OUT.parent.parent / relative) == digest

    paths = {name: OUT / f'raw/D1/{name}.jsonl' for name in ('calls', 'decisions')}
    tails = {}
    for name, path in paths.items():
        raw = path.read_bytes()
        assert raw == (BASE / f'D1/{name}.jsonl').read_bytes()
        size = amendment[f'before_{name}_bytes']
        assert hashlib.sha256(raw[:size]).hexdigest() == amendment[f'before_{name}_sha256']
        tails[name] = [json.loads(line) for line in raw[size:].splitlines()]

    before_ids = {record['id'] for record in rows(paths['decisions'])} - {
        record['id'] for record in tails['decisions']}
    expected_ids = [item for item in manifest['order']['D1'] if item not in before_ids]
    assert len(before_ids) == amendment['completed'] == 566
    assert expected_ids == [item['id'] for item in amendment['remaining_reserves']]
    assert expected_ids == [record['id'] for record in tails['decisions']]
    assert len(expected_ids) == amendment['remaining'] == 20
    requests = [event for event in tails['calls'] if event['event'] == 'request']
    assert [event['input_id'] for event in requests] == expected_ids
    assert all(event['attempt'] == 1 for event in requests)
    assert not any(event['event'] == 'failure' for event in tails['calls'])
    assert closure['judges']['D1']['status']['state'] == 'complete'
    assert closure['judges']['D1']['decisions'] == len(manifest['order']['D1']) == 586
    assert closure['exact_frozen_requests'] and closure['single_concurrency']
    assert closure['historical_decisions_unchanged'] and closure['frozen_files_unchanged']

    statistics_match = {}
    for judge in ('D0', 'D1'):
        result = read(OUT / f'RESULTS_{judge}.json')
        check = read(OUT / f'STATISTICS_RECHECK_{judge}.json')
        assert result['completed'] == result['planned']
        assert result['timing']['d5_zero_hard_gate'] and check['all_equal']
        for key, actual in check['contrasts'].items():
            expected = result['timing']['comparisons'][key]
            assert actual['difference_total'] == expected['difference_total']
            assert actual['ci95'] == expected['ci95']
            assert actual['passed'] == expected['threshold_met']
        statistics_match[judge] = True

    assert closure['cost_usd'] < manifest['dollar_cap_usd'] == 2.0
    assert owner_reservation.LIMIT == 4.0
    daily = closure['daily_budget']
    assert daily['used_usd'] < daily['limit_usd'] == 4.0
    assert abs(closure['unaccounted_or_reserved_usd'] - .342697) < 1e-10
    retry_check = read(OUT / 'OWNER_RETRY_POLICY_RECHECK.json')
    assert retry_check['completed'] == 586 and retry_check['maximum_attempts_per_input'] == 2
    assert retry_check['D0_calls_and_decisions_byte_identical']
    assert all(item['status'] == 'reserved_unknown' for item in retry_check['D1_unknown_reserves'])

    report = {
        'at_utc': utc(),
        'parent_manifest_sha256': sha(runner.FROZEN),
        'amendment_sha256': sha(owner_reservation.AMENDMENT),
        'audit_script_sha256': sha(__file__),
        'prior_566_decisions_and_calls_prefix_byte_identical': True,
        'new_decisions': len(tails['decisions']),
        'new_requests': len(requests),
        'new_failures': 0,
        'new_request_order_identical_to_authorized_remaining': True,
        'first_resumed_input': expected_ids[0],
        'remaining': 0,
        'status': closure['judges']['D1']['status'],
        'authorization_committed_before_request': commit_audit['commit'],
        'request_reservation_ceiling_usd': owner_reservation.LIMIT,
        'unchanged_projection_stop_usd': manifest['dollar_cap_usd'],
        'unchanged_daily_budget_usd': daily['limit_usd'],
        'accounted_usd': closure['cost_usd'],
        'settled_usd': closure['model_settled_cost_usd'],
        'unknown_reserves_preserved_usd': closure['unaccounted_or_reserved_usd'],
        'original_U3_statistics_match_current_results': statistics_match,
        'exact_frozen_requests_and_single_concurrency': True,
        'complete': True,
    }
    write(OUT / 'RESERVATION_COMPLETION_RECHECK.json', report)
    return report


if __name__ == '__main__':
    result = audit()
    print(json.dumps({key: result[key] for key in ('complete', 'new_decisions', 'remaining', 'accounted_usd')}))
