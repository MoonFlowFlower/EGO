"""Read-only accounting and evidence exports; never changes scoring."""
import argparse
import csv
import io
import json
from datetime import datetime, timezone
from statistics import median

from companion.budget import DailyLedger
from growthlab.records import ROOT
from u2.study import sha, write
from u2.run import exclusive, verify
from .screen import BASE, OUT, SCREEN, read, old_pool, attributed_cost, rows_at


def accounting(branches):
    paths = [p for branch in branches for p in (BASE / branch).rglob('calls.jsonl')]
    calls = [json.loads(s) for p in paths for s in p.read_text(encoding='utf-8').splitlines()]
    ids = set()
    for branch in branches:
        for p in (BASE / branch).rglob('routing.jsonl'):
            ids.update(json.loads(s).get('charge_id') for s in p.read_text(encoding='utf-8').splitlines())
    ledger = DailyLedger()
    with ledger._connect() as db:
        charges = [{'id': i, 'usd': u, 'status': s} for i, u, s in db.execute('SELECT id,usd,status FROM charges') if i in ids]
    responses = [r for r in calls if r['event'] == 'response']
    requests = [r for r in calls if r['event'] == 'request']
    times = [r['meta']['latency_s'] for r in responses]
    return {'requests': len(requests), 'responses': len(responses), 'retries': sum(r['attempt'] == 2 for r in requests),
            'failures': [r for r in calls if r['event'] == 'failure'],
            'charges': charges, 'cost_including_unknown_usd': sum(c['usd'] for c in charges),
            'unknown_reservations': sum(c['status'] == 'reserved_unknown' for c in charges),
            'latency_median_s': median(times) if times else None, 'latency_max_s': max(times) if times else None,
            'daily_budget': ledger.snapshot()}


def screen_report():
    manifest = read(SCREEN); verify(manifest); old_pool()
    result = read(OUT / 'SCREEN_RESULTS.json')
    summary = accounting(['screen'])
    rows = list(rows_at(BASE / 'screen').values())
    summary['source_hashes_verified'] = True
    summary['invalid_decisions'] = sum(not s['valid'] for r in rows for s in r['scores'])
    summary['pooled_counts'] = result['counts']
    write(OUT / 'SCREEN_AUDIT.json', summary)
    stream = io.StringIO(newline=''); writer = csv.writer(stream)
    writer.writerow(['round', 'id', 'reasons'])
    writer.writerows([r['round'], r['id'], ';'.join(r['reasons'])] for r in result['excluded'])
    (OUT / 'EXCLUDED.csv').write_text(stream.getvalue(), encoding='utf-8-sig')
    stream = io.StringIO(newline=''); writer = csv.writer(stream)
    writer.writerow(['round', 'category', 'stage', 'items', 'decisions', 'invalid', 'target_hits', 'reported_cost_usd'])
    for category in ('P', 'Q'):
        for stage in ('prior', 'ceiling'):
            group = [r for r in rows if r['category'] == category and r['stage'] == stage]
            scored = [s for r in group for s in r['scores']]
            writer.writerow([2, category, stage, len(group), len(scored), sum(not s['valid'] for s in scored), sum(s['correct'] for s in scored), sum(r['meta']['cost_usd'] or 0 for r in group)])
    (OUT / 'SCREEN_SUMMARY.csv').write_text(stream.getvalue(), encoding='utf-8-sig')
    close = {'closed_at_utc': datetime.now(timezone.utc).isoformat(), 'screen_manifest_sha256': sha(SCREEN),
             'selection_sha256': sha(OUT / 'SCREEN_RESULTS.json'), 'source_hashes_verified': True,
             'raw_sha256': {p.relative_to(OUT).as_posix(): sha(p) for p in sorted((OUT / 'raw/screen').rglob('*')) if p.is_file()},
             'screen_cost_usd': summary['cost_including_unknown_usd'], 'main_has_not_started': not (BASE / 'main.claim').exists(),
             'original_failed_items_recalled': 0, 'pooled_counts': result['counts']}
    exclusive(OUT / 'SCREEN_CLOSE.json', close)
    print(json.dumps({k: v for k, v in summary.items() if k != 'charges'}, ensure_ascii=False))


def main_report():
    from .main import FROZEN, check_pins
    manifest = read(FROZEN); check_pins(manifest)
    summary = accounting(['main', 'delete'])
    summary['source_and_screen_hashes_verified'] = True
    summary['U2_all_rounds_usd'] = attributed_cost()
    proposals = []
    for p in (BASE / 'main').rglob('consolidations.jsonl'):
        proposals.extend(json.loads(s) for s in p.read_text(encoding='utf-8').splitlines())
    summary['consolidations'] = len(proposals)
    summary['proposals_accepted'] = sum(r['accepted'] for p in proposals for r in p['results'])
    summary['proposals_rejected'] = sum(not r['accepted'] for p in proposals for r in p['results'])
    summary['proposal_rejection_reasons'] = {}
    for p in proposals:
        for r in p['results']:
            if not r['accepted']:
                reason = r['reason']
                summary['proposal_rejection_reasons'][reason] = summary['proposal_rejection_reasons'].get(reason, 0) + 1
    write(OUT / 'MAIN_AUDIT.json', summary)
    close = {'closed_at_utc': datetime.now(timezone.utc).isoformat(), 'main_manifest_sha256': sha(FROZEN),
             'source_and_screen_hashes_verified': True,
             'raw_sha256': {p.relative_to(OUT).as_posix(): sha(p) for branch in ('main', 'delete') for p in sorted((OUT / 'raw' / branch).rglob('*')) if p.is_file()},
             'main_results_sha256': sha(OUT / 'MAIN_RESULTS.json'),
             'cost_including_unknown_usd': summary['cost_including_unknown_usd']}
    exclusive(OUT / 'MAIN_CLOSE.json', close)
    print(json.dumps({k: v for k, v in summary.items() if k != 'charges'}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('phase', choices=['screen', 'main'])
    args = parser.parse_args()
    (screen_report if args.phase == 'screen' else main_report)()
