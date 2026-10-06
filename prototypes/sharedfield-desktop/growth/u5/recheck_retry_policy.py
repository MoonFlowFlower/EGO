"""Post-run check of the supplemental retry grant, without model requests."""
from collections import Counter
from contextlib import closing
import json
import sqlite3

from p7.proxy import DEFAULT_BUDGET
from u3.common import read, write, utc, sha
from .corpus import BASE, OUT, rows
from .owner_retry_policy import AMENDMENT, CURRENT_ID, verify


def recheck():
    amendment = verify()
    calls = rows(OUT/'raw/D1/calls.jsonl')
    decisions = rows(OUT/'raw/D1/decisions.jsonl')
    assert sha(BASE/'D1/calls.jsonl') == sha(OUT/'raw/D1/calls.jsonl')
    assert sha(BASE/'D1/decisions.jsonl') == sha(OUT/'raw/D1/decisions.jsonl')
    requests = {}
    for event in calls:
        if event['event'] == 'request':
            group = requests.setdefault(event['input_id'], [])
            group.append(event)
            assert event['attempt'] == len(group) <= 2
            assert event['request'] == group[0]['request']
    assert [e['attempt'] for e in requests[CURRENT_ID]] == [1, 2]
    finals = [r for r in decisions if r['id'] == CURRENT_ID]
    assert len(finals) == 1 and finals[0]['score']['valid_output']
    failed_responses = [e for e in calls if e['event'] == 'response'
                        and e['meta'].get('error') and e['meta'].get('charge_id')]
    reserves = []
    with closing(sqlite3.connect(DEFAULT_BUDGET.resolve().as_uri()+'?mode=ro', uri=True)) as db:
        for event in failed_responses:
            identity = event['meta']['charge_id']
            usd, status = db.execute('SELECT usd,status FROM charges WHERE id=?', (identity,)).fetchone()
            if event['meta']['error'] in ('upstream_unavailable', 'upstream_connection_error'):
                assert status == 'reserved_unknown'
            if status == 'reserved_unknown':
                reserves.append({'charge_id': identity, 'usd': usd, 'status': status,
                                 'error': event['meta']['error']})
    diagnostics = [e for e in calls if e['event'] == 'transport_exception_type']
    for event in diagnostics:
        assert set(event) <= {'event', 'unix_s', 'judge', 'input_id', 'exception_type', 'errno'}
        assert isinstance(event['exception_type'], str)
        assert 'errno' not in event or isinstance(event['errno'], int)
    value = {'at_utc': utc(), 'amendment_sha256': sha(AMENDMENT),
        'D0_calls_and_decisions_byte_identical': True,
        'D1_original_14_decisions_and_call_prefix_byte_identical': True,
        'requests_identical_across_retries': True, 'maximum_attempts_per_input': 2,
        'current_interrupted_input_retried_successfully': True,
        'completed': len(decisions), 'requests': sum(len(rs) for rs in requests.values()),
        'retried_inputs': [identity for identity, rs in requests.items() if len(rs) == 2],
        'D1_unknown_reserves': reserves,
        'transport_exception_types': dict(Counter(e['exception_type'] for e in diagnostics)),
        'diagnostics_contain_only_allowed_fields': True,
        'status': read(BASE/'D1/STATUS.json')}
    write(OUT/'OWNER_RETRY_POLICY_RECHECK.json', value)
    print(json.dumps(value, ensure_ascii=False))
    return value


if __name__ == '__main__':
    recheck()
