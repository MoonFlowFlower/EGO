"""Frozen four-arm study; one new process for each learning/test/deletion job."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import sys

from companion.budget import DailyLedger
from growthlab.records import ROOT
from u2.client import Client, Stop
from u2.protocol import SEED
from u2.run import GLOBAL_STOPS, exclusive, sources, verify
from u2.study import learn, test, delete, sha, write
from u2.supplement_v2.check import candidates
from .screen import BASE, OUT, SCREEN, OLD, read, old_pool, attributed_cost
from .leakage import assign, audit
from .report import report_main

FROZEN = OUT / 'FROZEN.json'
MAIN_ESTIMATE = .90


def check_pins(manifest):
    verify(manifest)
    for name, digest in manifest.get('evidence_sha256', {}).items():
        if sha(ROOT / name) != digest:
            raise Stop('frozen_evidence_changed:' + name)


def prepare():
    if FROZEN.exists(): raise Stop('main_already_frozen')
    selection = read(OUT / 'SCREEN_RESULTS.json')
    if not selection['passed']: raise Stop('screening_gate_not_passed')
    verify(read(SCREEN)); old, _ = old_pool()
    indexed = {i['id']: i for i in old + candidates()}
    selected = [indexed[i] for i in selection['selected_ids']]
    people, pairs = assign(selected)
    review = audit(people)
    if not review['passed']: raise Stop('Q_answer_leakage_or_persona_conflict')
    write(OUT / 'Q_LEAKAGE_REVIEW.json', review)
    write(OUT / 'PERSONAS_DRAFT.json', {'personas': people, 'conflicts': pairs})
    print(json.dumps({'leakage_passed': review['passed'], 'people': {p: [i['id'] for i in v] for p, v in people.items()}}, ensure_ascii=False), flush=True)


def freeze():
    if FROZEN.exists(): raise Stop('main_already_frozen')
    screen = read(SCREEN); verify(screen)
    selection = read(OUT / 'SCREEN_RESULTS.json')
    engineering = read(OUT / 'ENGINEERING_MAIN.json')
    if not selection['passed'] or not engineering['passed']: raise Stop('main_preflight_not_passed')
    draft = read(OUT / 'PERSONAS_DRAFT.json')
    people = draft['personas']
    ids = [i['id'] for values in people.values() for i in values]
    if len(set(ids)) != len(ids) or set(ids) != set(selection['selected_ids']):
        raise Stop('persona_selection_mismatch')
    old, _ = old_pool(); indexed = {i['id']: i for i in old + candidates()}
    if any(i != indexed[i['id']] for values in people.values() for i in values):
        raise Stop('candidate_changed_while_assembling')
    review = audit(people)
    if not review['passed'] or review != read(OUT / 'Q_LEAKAGE_REVIEW.json'):
        raise Stop('leakage_review_not_reproducible')
    p_ids = [i for i in selection['selected_ids'] if indexed[i]['category'] == 'P']
    random.Random(SEED + 1).shuffle(p_ids)
    pinned = sources()
    for p in [*(ROOT / 'u2/supplement_v2/candidates').glob('*.json'), ROOT / 'u2/round2/PRE_SCREEN.md', ROOT / 'u2/round2/PRE_MAIN.md']:
        pinned[p.relative_to(ROOT).as_posix()] = sha(p)
    evidence_files = [SCREEN, OUT / 'SCREEN_RESULTS.json', OUT / 'SCREEN_CLOSE.json', OUT / 'Q_LEAKAGE_REVIEW.json',
                      OUT / 'PERSONA_SEMANTIC_REVIEW.md', OUT / 'ENGINEERING_MAIN.json',
                      OLD / 'SCREEN_FREEZE.json', OLD / 'SCREEN_CLOSE.json']
    evidence_files += [p for branch in [OUT / 'raw/screen', OLD / 'raw/screen'] for p in branch.rglob('*') if p.is_file()]
    value = {**screen, 'version': 'u2-round2-main', 'frozen_at_utc': datetime.now(timezone.utc).isoformat(),
             'source_sha256': pinned, 'screen_manifest_sha256': sha(SCREEN),
             'evidence_sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in evidence_files},
             'selection': selection, 'personas': people, 'delete_ids': p_ids[:4],
             'main_arms': ['B_R', 'B_I', 'B_N', 'A_R'], 'estimated_main_usd': MAIN_ESTIMATE,
             'cost_before_main': attributed_cost(), 'cumulative_cap_usd': attributed_cost() + MAIN_ESTIMATE,
             'Q_leakage_review': review, 'descriptive_arms': 'Not run; no result-dependent addition.',
             'restarts': 'Every learn/test/delete job is a separate OS process; SQLite closes before readonly test and hashes must match.'}
    exclusive(FROZEN, value)
    print(json.dumps({'main_manifest_sha256': sha(FROZEN), 'delete_ids': p_ids[:4], 'budget': DailyLedger().snapshot()}, ensure_ascii=False), flush=True)


def export_raw():
    names = {'calls.jsonl', 'decisions.jsonl', 'consolidations.jsonl', 'routing.jsonl', 'result.json', 'learned.json', 'storage_hash.json', 'deletion_bytes.json'}
    for branch in ('main', 'delete'):
        for path in (BASE / branch).rglob('*'):
            if path.is_file() and path.name in names:
                dest = OUT / 'raw' / path.relative_to(BASE)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, dest)


def execute(name, manifest, operation, **fields):
    check_pins(manifest)
    folder = BASE / name
    folder.mkdir(parents=True, exist_ok=False)
    job = {'folder': str(folder), 'manifest_sha256': sha(FROZEN), 'operation': operation, **fields}
    write(folder / 'job.json', job)
    with (folder / 'stdout.txt').open('wb') as out, (folder / 'stderr.txt').open('wb') as err:
        try:
            p = subprocess.run([sys.executable, '-m', 'u2.round2.main', 'worker', str(folder / 'job.json')], cwd=ROOT,
                               env=dict(os.environ, PYTHONPATH=str(ROOT), PYTHONIOENCODING='utf-8'), stdout=out, stderr=err, timeout=3700)
            code = p.returncode
        except subprocess.TimeoutExpired:
            code = 'worker_timeout'
    if not (folder / 'result.json').exists():
        write(folder / 'result.json', {'status': 'stopped', 'stop': 'worker_without_result', 'returncode': code})
    result = read(folder / 'result.json')
    print(json.dumps({'lane': name, **result}, ensure_ascii=False), flush=True)
    return result


def worker(path):
    job = read(path); folder = Path(job['folder'])
    result = {'status': 'running', 'pid': os.getpid()}
    try:
        manifest = read(FROZEN); check_pins(manifest)
        if sha(FROZEN) != job['manifest_sha256']: raise Stop('main_manifest_changed')
        if job['operation'] == 'delete':
            result['deletion'] = delete(job)
        else:
            client = Client(folder, total_cap=manifest['cumulative_cap_usd'])
            if job['operation'] == 'learn': learn(job, client)
            elif job['operation'] == 'test': test(job, client)
            else: raise ValueError('unknown_operation')
        result['status'] = 'complete'
    except Exception as error:
        result.update(status='stopped', stop=str(error) if isinstance(error, (Stop, ValueError)) else type(error).__name__)
    finally:
        write(folder / 'result.json', result)


def run():
    manifest = read(FROZEN); check_pins(manifest)
    budget = DailyLedger().snapshot()
    if budget['remaining_usd'] < MAIN_ESTIMATE:
        write(OUT / 'MAIN_DEFERRED.json', {'reason': 'insufficient_daily_balance', 'budget': budget, 'needed_usd': MAIN_ESTIMATE})
        raise Stop('start_on_another_day')
    exclusive(BASE / 'main.claim', {'manifest_sha256': sha(FROZEN), 'budget': budget, 'utc': datetime.now(timezone.utc).isoformat()})
    write(OUT / 'MAIN_START.json', read(BASE / 'main.claim'))
    stopped = False
    for person, items in manifest['personas'].items():
        if stopped: break
        for arm, group in [('B', 'R'), ('B', 'I'), ('B', 'N'), ('A', 'R')]:
            name = f'main/person{person}/{arm}_{group}'
            matched = BASE / f'main/person{person}/B_R/learn/state.sqlite'
            if group == 'I' and not (matched.parent / 'learned.json').exists(): continue
            learned = execute(name + '/learn', manifest, 'learn', persona=person, arm=arm, group=group, items=items, matched_store=str(matched))
            if learned.get('stop') in GLOBAL_STOPS:
                stopped = True; break
            if learned['status'] == 'complete':
                tested = execute(name + '/test', manifest, 'test', persona=person, arm=arm, group=group, items=items, store=str(BASE / name / 'learn/state.sqlite'))
                if tested.get('stop') in GLOBAL_STOPS:
                    stopped = True; break
            export_raw()
    if not stopped:
        for person, items in manifest['personas'].items():
            selected = [i for i in items if i['id'] in manifest['delete_ids']]
            if not selected: continue
            source = BASE / f'main/person{person}/B_R'
            if not (source / 'test/result.json').exists() or read(source / 'test/result.json')['status'] != 'complete': continue
            erased = execute(f'delete/person{person}', manifest, 'delete', persona=person, arm='B', group='R', store=str(source / 'learn/state.sqlite'), delete_ids=[i['id'] for i in selected])
            if erased['status'] == 'complete':
                result = execute(f'delete/person{person}/test', manifest, 'test', persona=person, arm='B', group='R', store=str(source / 'learn/state.sqlite'), items=selected, stage='deleted')
                if result.get('stop') in GLOBAL_STOPS: break
            export_raw()
    export_raw()
    report_main(manifest)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['prepare', 'freeze', 'run', 'worker', 'report', 'export'])
    parser.add_argument('path', nargs='?')
    args = parser.parse_args()
    {'prepare': prepare, 'freeze': freeze, 'run': run, 'worker': lambda: worker(args.path),
     'report': lambda: report_main(read(FROZEN)), 'export': export_raw}[args.command]()
