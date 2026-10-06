"""Independent verification using the original frozen U3 bootstrap routine."""
import argparse
import hashlib
import json
import sqlite3
from contextlib import closing
from u3.statistics import comparisons as original_bootstrap
from u3.common import ROOT, read, write, sha, utc
from p7.proxy import DEFAULT_BUDGET
from .corpus import OUT, rows
from .owner_resume import AMENDMENT, FAILED_ID


def statistics(judge):
    expected = read(OUT/f'RESULTS_{judge}.json')['timing']['comparisons']
    assert expected is not None
    inputs = {i['id']: i for i in rows(OUT/'INPUTS.jsonl')}
    records = rows(OUT/f'raw/{judge}/decisions.jsonl')
    grid = {(inputs[r['id']]['person'], inputs[r['id']]['arm'], inputs[r['id']]['case']['id']): r['score']
            for r in records if inputs[r['id']]['domain'] == 'timing'}
    materials = read(ROOT/'evidence/u3/B_MATERIALIZED.json')['people']
    definitions = {'phenomenon': ('N', 'R', 'active'), 'C5': ('precedent', 'N', 'active'),
                   'C1': ('feedback', 'feedback_control', 'utility'), 'C3': ('scope', 'scope_shuffled', 'utility')}
    checked = {}
    for key, (left, right, field) in definitions.items():
        people = {}
        for person, material in materials.items():
            people[person] = []
            for moment in material['test']:
                a, b = grid[person, left, moment['id']][field], grid[person, right, moment['id']][field]
                people[person].append({'R': a, 'fixed': b, 'I': b, 'N': b, 'R_SHUFFLED': b})
        # H1 of the unmodified original routine is precisely left minus right.
        actual = original_bootstrap(people)['H1']
        assert actual['difference_total'] == expected[key]['difference_total']
        assert actual['ci95'] == expected[key]['ci95']
        assert actual['passed'] == expected[key]['threshold_met']
        checked[key] = actual
    report = {'at_utc': utc(), 'judge': judge, 'method': 'Map each U5 contrast into original u3.statistics.comparisons H1; same ordered moments and paired seed',
        'original_implementation_sha256': sha(ROOT/'u3/statistics.py'), 'all_equal': True, 'contrasts': checked}
    write(OUT/f'STATISTICS_RECHECK_{judge}.json', report)
    return report


def owner_retry():
    amendment = read(AMENDMENT)
    assert sha(ROOT/'u5/owner_resume.py') == amendment['driver_sha256']
    path = OUT/'raw/D0/decisions.jsonl'
    prefix = b''.join(path.read_bytes().splitlines(keepends=True)[:amendment['before_decisions']])
    assert hashlib.sha256(prefix).hexdigest() == amendment['before_decisions_sha256']
    lines = (OUT/'raw/D0/calls.jsonl').read_bytes().splitlines(keepends=True)
    events = [json.loads(line) for line in lines]
    stop = next(n for n, e in enumerate(events) if e['event'] == 'failure' and e['input_id'] == FAILED_ID and e['attempt'] == 1)
    assert hashlib.sha256(b''.join(lines[:stop+1])).hexdigest() == amendment['before_calls_sha256']
    requests = [e for e in events if e['event'] == 'request' and e['input_id'] == FAILED_ID]
    assert [e['attempt'] for e in requests] == [1, 2]
    assert requests[0]['request'] == requests[1]['request']
    failure = next(e for e in events if e['event'] == 'response' and e['input_id'] == FAILED_ID and e['attempt'] == 1)
    final = [r for r in rows(path) if r['id'] == FAILED_ID]
    assert len(final) == 1 and final[0]['score']['valid_output']
    with closing(sqlite3.connect(DEFAULT_BUDGET.resolve().as_uri()+'?mode=ro', uri=True)) as db:
        usd, status = db.execute('SELECT usd,status FROM charges WHERE id=?', (failure['meta']['charge_id'],)).fetchone()
    assert status == 'reserved_unknown' and abs(usd-.086888)<1e-12
    value = {'at_utc': utc(), 'authorized_attempts': [1, 2], 'failed_input_id': FAILED_ID,
        'requests_identical': True, 'prior_392_decisions_byte_identical': True, 'prior_failure_log_byte_identical': True,
        'completed_outputs_for_retried_input': 1, 'retry_valid': True, 'unknown_reserve_preserved_usd': usd,
        'amendment_driver_unchanged': True}
    write(OUT/'OWNER_RETRY_RECHECK.json', value)
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--judge', choices=('D0', 'D1'), required=True)
    args = parser.parse_args()
    result = statistics(args.judge)
    if args.judge == 'D0':
        owner_retry()
    print(json.dumps({'judge': args.judge, 'original_U3_bootstrap_equal': result['all_equal']}))
