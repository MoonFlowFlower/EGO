"""One-shot staged U3. Completed stages can be read; failed lanes never replay."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from growthlab.records import ROOT
from .client import Client, Stop
from .common import BASE, OUT, read, write, sha, utc, pins, verify, budget_snapshot, cost, append
from .materials import build
from .protocol import SEED, MODEL, ROUTE, ESTIMATE_USD, CRITERIA, A_GATE_SCOPE, ARMS, packet, schema, parse, a_format_result
from .selection import a_materialize, a_screen, b_materialize
from .study import decide, a_store, a_test, learn, fork_store, b_test

FROZEN = OUT / 'FROZEN.json'
MATERIALS = ROOT / 'u3/MATERIALS.json'
POLICY = ROOT / 'u3/SCREEN_POLICY.json'
GLOBAL_STOPS = {'operator_stop', 'actual_exceeded_estimate', 'estimate_reservation_stop',
                'daily_budget_stop', 'ac_required'}
EXPORT_NAMES = {'job.json', 'result.json', 'calls.jsonl', 'model.jsonl', 'routing.jsonl',
                'decisions.jsonl', 'scores.jsonl', 'learned.json', 'storage_hash.json', 'claim.json'}


def rows(path):
    path = Path(path)
    return [json.loads(s) for s in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []


def prepare():
    if FROZEN.exists():
        raise Stop('already_frozen')
    value = build()
    if MATERIALS.exists() and read(MATERIALS) != value:
        raise Stop('materials_differ_review_before_replacing')
    if not MATERIALS.exists():
        write(MATERIALS, value, exclusive=True)
    if not POLICY.exists():
        write(POLICY, {'status': 'pending_owner_answer', 'aligned_policy': None,
              'question': '顺先验校准题是否保留并分层报告，仍须通过使用上限？'}, exclusive=True)
    print(json.dumps({'a_candidates': len(value['a']), 'b_prior_cells_per_person': 16,
          'b_selected_learn_per_person': 32, 'b_selected_test_per_person': 24,
          'budget': budget_snapshot(), 'paid_calls': 0}, ensure_ascii=False))


def freeze():
    if FROZEN.exists():
        raise Stop('already_frozen')
    policy = read(POLICY)
    if policy.get('status') != 'owner_resolved' or policy.get('aligned_policy') not in ('retain_calibration', 'exclude_all_correct'):
        raise Stop('screen_policy_requires_owner_answer')
    engineering = read(OUT / 'ENGINEERING.json')
    if not engineering['passed']:
        raise Stop('engineering_not_passed')
    if engineering.get('code_sha256') != {p: h for p, h in pins().items() if p.endswith('.py')}:
        raise Stop('engineering_checked_different_source')
    if read(MATERIALS) != build():
        raise Stop('material_generator_mismatch')
    value = {'version': 'u3-v2-prepaid-strata-clarification', 'frozen_at_utc': utc(), 'source_sha256': pins(),
             'seed': SEED, 'model': MODEL, 'route': ROUTE, 'temperature': 0,
             'reasoning': False, 'max_tokens': 1024, 'criteria_verbatim': CRITERIA,
             'u3a_gate_scope_verbatim': A_GATE_SCOPE,
             'estimate_usd': ESTIMATE_USD, 'screen_policy': policy,
             'evidence_sha256': {'evidence/u3/ENGINEERING.json': sha(OUT / 'ENGINEERING.json')},
             'stops': 'U2: single concurrency; >=2s between starts; 429/502/503/504 or connection only one same-input retry; second failure stops lane; two invalid outputs stop lane; 3600 seconds per lane; no replay/replacement/content retry.',
             'preregistration': 'All alternative branches, reactions and deterministic prior-only selection code frozen before ANY paid call. Materialization adds a derived hash manifest; it does not edit this source.',
             'claim_ceiling': 'Synthetic learning of when to speak beyond fixed rules only; no subjective agency.'}
    superseded = OUT / 'preflight_versions/v1/FROZEN.json'
    if superseded.exists():
        value['superseded_prepaid_manifest_sha256'] = sha(superseded)
    write(FROZEN, value, exclusive=True)
    print(json.dumps({'frozen_sha256': sha(FROZEN), 'budget': budget_snapshot()}, ensure_ascii=False))


def export():
    for path in BASE.rglob('*'):
        if path.is_file() and path.name in EXPORT_NAMES:
            dest = OUT / 'raw' / path.relative_to(BASE)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)


def recorded(path, value):
    path = Path(path)
    if path.exists():
        if read(path) != value:
            raise Stop('derived_record_changed:' + path.name)
    else:
        write(path, value, exclusive=True)


def phase_freeze(name, paths):
    value = {'source_manifest_sha256': sha(FROZEN),
             'evidence_sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in paths}}
    recorded(OUT / name, value)


def verify_phase(path):
    phase = read(path)
    if phase['source_manifest_sha256'] != sha(FROZEN):
        raise Stop('phase_source_manifest_changed')
    for name, digest in phase['evidence_sha256'].items():
        if sha(ROOT / name) != digest:
            raise Stop('phase_evidence_changed:' + name)


def execute(name, operation, **fields):
    manifest = read(FROZEN)
    verify(manifest)
    folder = BASE / name
    if folder.exists():
        result = read(folder / 'result.json') if (folder / 'result.json').exists() else {'status': 'interrupted'}
        if result['status'] != 'complete':
            raise Stop('consumed_lane_cannot_resume:' + name)
        for relative, digest in result['file_sha256'].items():
            if sha(folder / relative) != digest:
                raise Stop('completed_lane_changed:' + name)
        return result
    folder.mkdir(parents=True, exist_ok=False)
    job = {'folder': str(folder), 'operation': operation, 'manifest_sha256': sha(FROZEN), **fields}
    phase = ('B_MAIN_FREEZE.json' if operation in ('b_learn', 'b_test', 'fork') else
             'A_MAIN_FREEZE.json' if operation in ('a_store', 'a_test') else
             'A_SCREEN_FREEZE.json' if operation == 'a_screen' else None)
    if phase:
        verify_phase(OUT / phase)
        job['phase_freeze'] = str(OUT / phase)
        job['phase_freeze_sha256'] = sha(OUT / phase)
    write(folder / 'job.json', job, exclusive=True)
    with (folder / 'stdout.txt').open('wb') as out, (folder / 'stderr.txt').open('wb') as err:
        try:
            p = subprocess.run([sys.executable, '-m', 'u3.run', 'worker', str(folder / 'job.json')],
                cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT), PYTHONIOENCODING='utf-8'),
                stdout=out, stderr=err, timeout=3700)
            code = p.returncode
        except subprocess.TimeoutExpired:
            code = 'worker_timeout'
    if not (folder / 'result.json').exists():
        write(folder / 'result.json', {'status': 'stopped', 'stop': 'worker_without_result', 'returncode': code})
    result = read(folder / 'result.json')
    export()
    print(json.dumps({'lane': name, 'status': result['status'], 'stop': result.get('stop')}, ensure_ascii=False), flush=True)
    if result.get('stop') in GLOBAL_STOPS:
        raise Stop(result['stop'])
    return result


def worker(jobpath):
    job = read(jobpath)
    folder = Path(job['folder'])
    # Guard the worker itself too, not only the orchestrator. A direct CLI
    # invocation must never replay a charged lane after interruption/completion.
    if (folder / 'claim.json').exists() or (folder / 'result.json').exists():
        raise Stop('worker_claim_already_consumed')
    write(folder / 'claim.json', {'at_utc': utc(), 'pid': os.getpid(), 'job_sha256': sha(jobpath)}, exclusive=True)
    result = {'status': 'running', 'pid': os.getpid()}
    try:
        manifest = read(FROZEN)
        verify(manifest)
        if sha(FROZEN) != job['manifest_sha256']:
            raise Stop('manifest_changed')
        if job.get('phase_freeze'):
            if sha(job['phase_freeze']) != job['phase_freeze_sha256']:
                raise Stop('phase_manifest_changed')
            verify_phase(job['phase_freeze'])
        op = job['operation']
        if op == 'a_store':
            a_store(folder / 'stores', job['items'])
        elif op == 'fork':
            fork_store(job)
        else:
            client = Client(folder)
            if op == 'probe':
                for item in job['cases']:
                    decide(client, item, [], 'S0', {'item_id': item['id'], 'stage': job['stage']})
            elif op == 'a_screen':
                for item in job['items']:
                    sources = [] if job['stage'] == 'prior' else [{'utterance_id': 'ceiling', 'speaker': 'user',
                              'occurred_at': '2026-09-02T18:00:00-05:00', 'session_id': 'ceiling', 'utterance_text': item['ceiling']}]
                    decide(client, item, sources, 'S0', {'item_id': item['id'], 'stage': job['stage']})
            elif op == 'a_test':
                a_test(job, client)
            elif op == 'b_learn':
                learn(job, client)
            elif op == 'b_test':
                b_test(job, client)
            else:
                raise ValueError('unknown_operation')
        result['status'] = 'complete'
    except Exception as error:
        result.update(status='stopped', stop=str(error) if isinstance(error, (Stop, ValueError)) else type(error).__name__)
    finally:
        result['file_sha256'] = {p.relative_to(folder).as_posix(): sha(p) for p in folder.rglob('*')
                                 if p.is_file() and p.name in EXPORT_NAMES | {'state.sqlite', 'created.json'} and p.name != 'result.json'}
        # Every A store is covered too; they are inputs to a future process.
        result['file_sha256'].update({p.relative_to(folder).as_posix(): sha(p) for p in folder.rglob('*.sqlite')})
        write(folder / 'result.json', result)


def require_complete(result):
    if result['status'] != 'complete':
        raise Stop('stage_incomplete:' + result.get('stop', 'unknown'))


def a_run(materials, manifest):
    require_complete(execute('a/prior_probe', 'probe', cases=materials['a'], stage='a_prior_probe'))
    prior_rows = rows(BASE / 'a/prior_probe/decisions.jsonl')
    if not all(r['valid'] for r in prior_rows):
        raise Stop('invalid_a_calibration_no_replacement')
    items = a_materialize(materials['a'], {r['item_id']: r['action'] for r in prior_rows})
    recorded(OUT / 'A_MATERIALIZED.json', {'items': items, 'prior_result_sha256': sha(BASE / 'a/prior_probe/result.json'),
             'source_manifest_sha256': sha(FROZEN)})
    phase_freeze('A_SCREEN_FREEZE.json', [OUT / 'A_MATERIALIZED.json',
                 *sorted((OUT / 'raw/a/prior_probe').rglob('*.json*'))])
    for stage in ('prior', 'ceiling'):
        require_complete(execute('a/screen_'+stage, 'a_screen', items=items, stage=stage))
    screen_rows = [{r['item_id']: r for r in rows(BASE / f'a/screen_{stage}/decisions.jsonl')} for stage in ('prior', 'ceiling')]
    screened = a_screen(items, *screen_rows, aligned_policy=manifest['screen_policy']['aligned_policy'])
    recorded(OUT / 'A_SCREEN_RESULTS.json', screened)
    phase_freeze('A_MAIN_FREEZE.json', [OUT / 'A_MATERIALIZED.json', OUT / 'A_SCREEN_RESULTS.json',
                 *sorted((OUT / 'raw/a/screen_prior').rglob('*.json*')),
                 *sorted((OUT / 'raw/a/screen_ceiling').rglob('*.json*'))])
    selected = [i for i in items if i['id'] in screened['selected_ids']]
    results, scored_by_format = {}, {}
    if selected:
        require_complete(execute('a/store', 'a_store', items=selected))
        for fmt in ('S0', 'S1'):
            completed = execute('a/test_'+fmt, 'a_test', items=selected, format=fmt, store_dir=str(BASE / 'a/store/stores'))
            scored = rows(BASE / f'a/test_{fmt}/scores.jsonl')
            scored_by_format[fmt] = {r['item_id']: r for r in scored}
            results[fmt] = a_format_result(scored,
                complete=completed['status'] == 'complete' and len(scored) == len(selected),
                screen_evaluable=screened['passed'])
    else:
        results = {fmt: {**a_format_result([], complete=True, screen_evaluable=False),
                        'reason': 'screening_shortfall'} for fmt in ('S0', 'S1')}
    formats = ['S1'] if results['S1']['passed'] else ['S0', 'S1']
    paired_calibration = sorted(i['id'] for i in selected if i['prior_aligned'] and
                                all(i['id'] in scored_by_format.get(fmt, {}) for fmt in ('S0', 'S1')))
    calibration_comparison = {'paired_n': len(paired_calibration),
        'correct': {fmt: sum(scored_by_format[fmt][identity]['correct'] for identity in paired_calibration)
                    for fmt in ('S0', 'S1')},
        's1_regressed_ids': [identity for identity in paired_calibration
            if scored_by_format['S0'][identity]['correct'] and not scored_by_format['S1'][identity]['correct']],
        's1_improved_ids': [identity for identity in paired_calibration
            if not scored_by_format['S0'][identity]['correct'] and scored_by_format['S1'][identity]['correct']]}
    value = {'formats': results, 'b_formats': formats, 'screen_passed': screened['passed'],
             'calibration_comparison': calibration_comparison,
             'screen_manifest_sha256': sha(OUT / 'A_SCREEN_RESULTS.json')}
    recorded(OUT / 'A_RESULTS.json', value)
    return formats


def b_run(materials, formats):
    cases = []
    for person, cells in materials['b'].items():
        for cell in cells:
            case = dict(cell['probe'])
            case['id'] = person+':'+cell['id']
            cases.append(case)
    require_complete(execute('b/prior_probe', 'probe', cases=cases, stage='b_prior_probe'))
    prior_rows = rows(BASE / 'b/prior_probe/decisions.jsonl')
    if not all(r['valid'] for r in prior_rows):
        raise Stop('invalid_b_calibration_no_replacement')
    people = b_materialize(materials['b'], {r['item_id']: r['action'] for r in prior_rows})
    recorded(OUT / 'B_MATERIALIZED.json', {'people': people, 'formats': formats,
             'prior_result_sha256': sha(BASE / 'b/prior_probe/result.json'), 'source_manifest_sha256': sha(FROZEN)})
    phase_freeze('B_MAIN_FREEZE.json', [OUT / 'B_MATERIALIZED.json', OUT / 'A_RESULTS.json',
                 *sorted((OUT / 'raw/b/prior_probe').rglob('*.json*'))])
    for fmt in formats:
        for person, data in people.items():
            prefix = f'b/{fmt}/person{person}'
            learned = execute(prefix+'/R/learn', 'b_learn', person=data, persona=person, format=fmt, arm='R')
            if learned['status'] != 'complete':
                continue
            original = BASE / prefix / 'R/learn/state.sqlite'
            for arm in ARMS:
                if arm != 'R':
                    forked = execute(prefix+f'/{arm}/learn', 'fork', related_store=str(original), persona=person, format=fmt, arm=arm)
                    if forked['status'] != 'complete':
                        continue
                execute(prefix+f'/{arm}/test', 'b_test', person=data, persona=person, format=fmt, arm=arm,
                        store=str(BASE / prefix / arm / 'learn/state.sqlite'))


def run():
    manifest = read(FROZEN)
    verify(manifest)
    current_cost = cost()
    budget = budget_snapshot()
    remaining_estimate = max(0, ESTIMATE_USD-current_cost)
    if budget['remaining_usd']+1e-12 < remaining_estimate:
        write(OUT / 'DEFERRED.json', {'at_utc': utc(), 'reason': 'insufficient_daily_balance',
              'budget': budget, 'remaining_estimate_usd': remaining_estimate, 'paid_calls_started_now': 0})
        raise Stop('start_on_another_day')
    if current_cost > ESTIMATE_USD:
        raise Stop('actual_exceeded_estimate')
    # Separate orchestration lock complements the global production model lock.
    lock_path = BASE / 'orchestrator.lock'
    BASE.mkdir(parents=True, exist_ok=True)
    import msvcrt
    with lock_path.open('a+b') as stream:
        if stream.tell() == 0:
            stream.write(b'0'); stream.flush()
        stream.seek(0)
        try:
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError:
            raise Stop('u3_already_running') from None
        try:
            if not (OUT / 'START.json').exists():
                write(OUT / 'START.json', {'at_utc': utc(), 'budget': budget, 'manifest_sha256': sha(FROZEN)}, exclusive=True)
            materials = read(MATERIALS)
            formats = a_run(materials, manifest)
            b_run(materials, formats)
            from .report import report
            report()
        finally:
            export()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('prepare', 'freeze', 'run', 'worker', 'export', 'report', 'budget'))
    parser.add_argument('path', nargs='?')
    args = parser.parse_args()
    try:
        if args.command == 'worker': worker(args.path)
        elif args.command == 'report':
            from .report import report
            report()
        elif args.command == 'budget': print(json.dumps(budget_snapshot(), ensure_ascii=False))
        else: {'prepare': prepare, 'freeze': freeze, 'run': run, 'export': export}[args.command]()
    except Stop as error:
        if args.command == 'run':
            append(OUT / 'STOPS.jsonl', {'at_utc': utc(), 'reason': str(error), 'cost_usd': cost()})
        print(json.dumps({'status': 'stopped', 'reason': str(error)}, ensure_ascii=False), flush=True)
        raise SystemExit(2)


if __name__ == '__main__':
    main()
