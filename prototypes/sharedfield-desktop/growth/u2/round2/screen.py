"""A new one-shot claim for P49-P72/Q49-Q72; never calls original items."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from companion.budget import DailyLedger
from growthlab.records import ROOT
from u2.client import Client, Stop, append
from u2.protocol import MODEL, ROUTE, SEED, score
from u2.run import (GLOBAL_STOPS, exclusive, reconcile_budget, screen_packet,
                    sources, verify)
from u2.study import sha, write
from u2.validate import load_candidates
from u2.supplement_v2.check import candidates, check
from .selection import qualify, draw

BASE = ROOT / 'runs/u2/round2'
OUT = ROOT / 'evidence/u2/round2'
SCREEN = OUT / 'SCREEN_FREEZE.json'
OLD = ROOT / 'evidence/u2'
SCREEN_ESTIMATE = .10
LANES = [('P', 'prior'), ('P', 'ceiling'), ('Q', 'prior'), ('Q', 'ceiling')]


def read(path):
    return json.loads(Path(path).read_bytes())


def rows_at(base):
    rows = {}
    for path in sorted(Path(base).glob('*/screen.jsonl')):
        for line in path.read_text(encoding='utf-8').splitlines():
            row = json.loads(line)
            key = (row['item_id'], row['stage'])
            if key in rows:
                raise ValueError('duplicate_screen_row')
            rows[key] = row
    return rows


def old_pool():
    verify(read(OLD / 'SCREEN_FREEZE.json'))
    close = read(OLD / 'SCREEN_CLOSE.json')
    if sha(OLD / 'SCREEN_FREEZE.json') != close['screen_manifest_sha256']:
        raise Stop('original_manifest_changed')
    if sha(OLD / 'SCREEN_RESULTS.json') != close['selection_sha256']:
        raise Stop('original_selection_changed')
    # The original closed record hashes the full model input/output as well.
    for name, digest in close['raw_sha256'].items():
        if sha(OLD / name) != digest:
            raise Stop('original_raw_changed:' + name)
    kept, excluded = qualify(load_candidates(), rows_at(OLD / 'raw/screen'))
    if [i['id'] for i in kept] != close['eligible_ids']:
        raise Stop('original_pool_does_not_reproduce')
    return kept, excluded


def attributed_cost():
    path = ROOT / 'runs/u2/charge_ids.jsonl'
    ids = {json.loads(s)['id'] for s in path.read_text(encoding='utf-8').splitlines()} if path.exists() else set()
    with DailyLedger()._connect() as db:
        return sum(usd for identity, usd in db.execute('SELECT id,usd FROM charges') if identity in ids)


def export_raw():
    names = {'calls.jsonl', 'screen.jsonl', 'routing.jsonl', 'result.json'}
    for path in BASE.rglob('*'):
        if path.is_file() and path.name in names:
            dest = OUT / 'raw' / path.relative_to(BASE)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)


def freeze():
    if SCREEN.exists():
        raise Stop('screen_freeze_exists')
    kept, excluded = old_pool()
    audit = check(candidates())
    if not audit['passed']:
        raise Stop('supplement_validation_failed')
    budget = reconcile_budget()
    if budget['daily']['remaining_usd'] < SCREEN_ESTIMATE:
        raise Stop('screen_balance_insufficient')
    client = Client(BASE / 'preflight')
    metadata = client.transport.preflight()  # Read-only metadata, no model call.
    pinned = sources()
    for p in [*(ROOT / 'u2/supplement_v2/candidates').glob('*.json'), ROOT / 'u2/round2/PRE_SCREEN.md']:
        pinned[p.relative_to(ROOT).as_posix()] = sha(p)
    parent = read(OLD / 'SCREEN_FREEZE.json')
    value = {
        'version': 'u2-round2-screen', 'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
        'source_sha256': pinned, 'seed': SEED, 'model': MODEL, 'route': ROUTE,
        'decision_reasoning': False, 'consolidation_effort': 'low',
        'criteria_verbatim': parent['criteria_verbatim'],
        'candidate_ids': [i['id'] for i in candidates()], 'validation': audit,
        'old_manifest_sha256': sha(OLD / 'SCREEN_FREEZE.json'),
        'old_close_sha256': sha(OLD / 'SCREEN_CLOSE.json'),
        'old_eligible_ids': [i['id'] for i in kept], 'old_excluded': excluded,
        'old_Q_reuse_authorization': 'Owner 2026-10-05 and design 18.11: all twelve passed with less information and may be pooled unchanged.',
        'screen_policy': parent['screen_policy'], 'selection': parent['selection'],
        'stops': parent['stops'], 'claim_ceiling': parent['claim_ceiling'],
        'lanes': LANES, 'screen_estimate_usd': SCREEN_ESTIMATE,
        'cost_before_screen': attributed_cost(),
        'cumulative_cap_usd': attributed_cost() + SCREEN_ESTIMATE,
        'main_estimate_usd': .90, 'daily_budget': budget, 'official_preflight': metadata,
        'future_P_rule': 'Only if pooled P<12: freeze new situations and all unlabelled options; make one no-memory call; choose an unselected human-plausible target, then author two disclosures. Never rerun a failed old item.',
    }
    exclusive(SCREEN, value)
    print(json.dumps({'screen_manifest_sha256': sha(SCREEN), 'budget': budget['daily']}, ensure_ascii=False), flush=True)


def lane(job, client):
    for item in candidates():
        if item['category'] != job['category']:
            continue
        messages, schema, cases = screen_packet(item, job['screen_stage'])
        output, meta = client.call(messages, {'item_id': item['id'], 'stage': job['screen_stage'], 'category': item['category']}, schema=schema)
        valid = isinstance(output, dict) and set(output) == {'decisions'} and isinstance(output['decisions'], list) and len(output['decisions']) == len(cases)
        values = output['decisions'] if valid else [None] * len(cases)
        scored = [{'phase': c['phase'], **score(v, c)} for v, c in zip(values, cases)]
        append(client.folder / 'screen.jsonl', {'item_id': item['id'], 'category': item['category'], 'stage': job['screen_stage'], 'output': output, 'scores': scored, 'meta': meta})
        client.parsed(valid and all(s['valid'] for s in scored))


def worker(path):
    job = read(path)
    folder = Path(job['folder'])
    result = {'status': 'running', 'pid': os.getpid()}
    try:
        manifest = read(SCREEN)
        verify(manifest)
        lane(job, Client(folder, total_cap=manifest['cumulative_cap_usd']))
        result['status'] = 'complete'
    except Exception as error:
        result.update(status='stopped', stop=str(error) if isinstance(error, (Stop, ValueError)) else type(error).__name__)
    finally:
        write(folder / 'result.json', result)


def selection():
    manifest = read(SCREEN)
    verify(manifest)
    kept_old, excluded_old = old_pool()
    kept_new, excluded_new = qualify(candidates(), rows_at(BASE / 'screen'))
    result = draw(kept_old + kept_new)
    completed = [(BASE / f'screen/{c}_{s}/result.json') for c, s in LANES]
    complete = all(p.exists() and read(p)['status'] == 'complete' for p in completed)
    expected_rows = {(i['id'], stage) for i in candidates() for stage in ('prior', 'ceiling')}
    complete = complete and set(rows_at(BASE / 'screen')) == expected_rows
    result.update(complete=complete, eligible_ids=[i['id'] for i in kept_old + kept_new],
                  inherited_ids=[i['id'] for i in kept_old], new_eligible_ids=[i['id'] for i in kept_new],
                  excluded=[{'round': 1, **x} for x in excluded_old] + [{'round': 2, **x} for x in excluded_new])
    result['passed'] = result['passed'] and complete
    if not result['passed']:
        result['selected_ids'] = []
    result['screen_cost_usd'] = attributed_cost() - manifest['cost_before_screen']
    result['daily_budget'] = DailyLedger().snapshot()
    write(OUT / 'SCREEN_RESULTS.json', result)
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return result


def run():
    manifest = read(SCREEN)
    verify(manifest)
    exclusive(BASE / 'screen.claim', {'manifest_sha256': sha(SCREEN), 'utc': datetime.now(timezone.utc).isoformat()})
    for category, stage in LANES:
        folder = BASE / f'screen/{category}_{stage}'
        folder.mkdir(parents=True, exist_ok=False)
        job = {'folder': str(folder), 'category': category, 'screen_stage': stage}
        write(folder / 'job.json', job)
        with (folder / 'stdout.txt').open('wb') as out, (folder / 'stderr.txt').open('wb') as err:
            try:
                p = subprocess.run([sys.executable, '-m', 'u2.round2.screen', 'worker', str(folder / 'job.json')], cwd=ROOT,
                                   env=dict(os.environ, PYTHONPATH=str(ROOT), PYTHONIOENCODING='utf-8'), stdout=out, stderr=err, timeout=3700)
                code = p.returncode
            except subprocess.TimeoutExpired:
                code = 'worker_timeout'
        if not (folder / 'result.json').exists():
            write(folder / 'result.json', {'status': 'stopped', 'stop': 'worker_without_result', 'returncode': code})
        result = read(folder / 'result.json')
        export_raw()
        print(json.dumps({'lane': f'{category}_{stage}', **result}, ensure_ascii=False), flush=True)
        if result.get('stop') in GLOBAL_STOPS:
            break
    selection()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['freeze', 'run', 'worker', 'selection', 'export'])
    parser.add_argument('path', nargs='?')
    args = parser.parse_args()
    {'freeze': freeze, 'run': run, 'worker': lambda: worker(args.path), 'selection': selection, 'export': export_raw}[args.command]()
