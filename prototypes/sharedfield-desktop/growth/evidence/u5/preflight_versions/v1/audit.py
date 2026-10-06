"""Post-run replay/transport audit; never issues model requests."""
from collections import Counter
import json
import re
from .corpus import OUT, BASE, rows
from .run import verify, FROZEN
from .scoring import grade
from .client import Client
from u3.common import ROOT, read, write, sha, utc, cost, budget_snapshot


def audit():
    manifest = verify()
    inputs = {i['id']: i for i in rows(OUT/'INPUTS.jsonl')}
    intervals, summaries, charge_ids = [], {}, set()
    for judge in ('D0', 'D1'):
        records = rows(OUT/f'raw/{judge}/decisions.jsonl')
        by_id = {r['id']: r for r in records}
        assert len(records) == len(by_id)
        for row in records:
            assert row['score'] == grade(inputs[row['id']], row['output'])
            if row['origin'] != 'new':
                assert judge == 'D0' and row['output'] == inputs[row['id']]['historical']['output']
        client = Client.__new__(Client)
        client.config = manifest['judges'][judge]
        pending, responded = None, {}
        attempts = Counter()
        for event in rows(OUT/f'raw/{judge}/calls.jsonl'):
            if event['event'] == 'request':
                assert pending is None
                pending = event
                assert event['request'] == client.request(inputs[event['input_id']])
                attempts[event['input_id']] += 1
                assert event['attempt'] == attempts[event['input_id']] <= 2
            elif event['event'] == 'response':
                assert pending and pending['input_id'] == event['input_id']
                intervals.append((pending['unix_s'], event['unix_s'], judge, event['input_id']))
                meta = event['meta']
                if meta.get('charge_id'):
                    assert meta['charge_id'] not in charge_ids
                    charge_ids.add(meta['charge_id'])
                if not meta['error'] or meta['error'] in ('model_output_truncated', 'model_output_incomplete', 'model_decision_json'):
                    assert event['input_id'] not in responded
                    responded[event['input_id']] = meta
                pending = None
        assert pending is None, 'unknown_inflight_request'
        for row in records:
            if row['origin'] == 'new':
                assert row['id'] in responded and row['meta'] == responded[row['id']]
        assert set(responded) == {r['id'] for r in records if r['origin'] == 'new'}
        status = read(BASE/judge/'STATUS.json') if (BASE/judge/'STATUS.json').exists() else None
        summaries[judge] = {'decisions': len(records), 'new': sum(r['origin'] == 'new' for r in records),
            'reused': sum(r['origin'] != 'new' for r in records), 'requests': sum(attempts.values()),
            'retry_attempts': sum(v-1 for v in attempts.values()),
            'invalid_outputs': sum(not r['score']['valid_output'] for r in records), 'status': status,
            'mechanically_regraded': len(records), 'input_mismatches': 0, 'duplicate_final_outputs': 0}
        for name in ('calls.jsonl', 'decisions.jsonl', 'model.jsonl', 'routing.jsonl', 'STATUS.json'):
            if (BASE/judge/name).exists():
                assert sha(BASE/judge/name) == sha(OUT/'raw'/judge/name)
    intervals.sort()
    assert all(end <= right[0] for (_, end, _, _), right in zip(intervals, intervals[1:])), 'concurrent_calls'
    key_pattern = re.compile(rb'(?:sk-or-v1-|sk-proj-|Bearer )[A-Za-z0-9_-]{16,}')
    for path in OUT.rglob('*'):
        if path.is_file():
            assert not key_pattern.search(path.read_bytes()), 'credential_pattern_in_export:' + str(path)
    model_total = sum(r.get('cost_usd') or 0 for j in ('D0', 'D1') for r in rows(OUT/f'raw/{j}/model.jsonl'))
    actual = cost(BASE/'charge_ids.jsonl')
    budget = budget_snapshot()
    # Unknown reserves may exceed the returned model costs; never discard them.
    assert actual + 1e-9 >= model_total
    result = {'at_utc': utc(), 'manifest_sha256': sha(FROZEN), 'frozen_files_unchanged': True,
        'judges': summaries, 'single_concurrency': True, 'request_intervals': len(intervals),
        'exact_frozen_requests': True, 'historical_decisions_unchanged': True,
        'credential_pattern_scan_passed': True, 'cost_usd': actual, 'model_settled_cost_usd': model_total,
        'unaccounted_or_reserved_usd': actual-model_total, 'daily_budget': budget,
        'archival_files_identical_to_runs': True}
    write(OUT/'CLOSURE.json', result)
    print(json.dumps(result, ensure_ascii=False))
    return result


if __name__ == '__main__':
    audit()
