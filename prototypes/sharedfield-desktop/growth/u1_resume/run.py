"""New stores/configuration; reuse the original frozen U1 workers and scorer."""
import argparse
import copy
import json
import os
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from growthlab.records import ROOT, write_json
from u1 import run as original
from u1.plan import read, sha, verify
from .client import Client
from .library import ConventionLibrary

BASE = ROOT / 'runs/u1_resume'
OUT = ROOT / 'evidence/u1_resume'
MANIFEST = OUT / 'frozen_v1.json'


def configure():
    # Process-local injection only: historical files and fixture paths stay intact.
    original.BASE = BASE
    original.ConventionLibrary = ConventionLibrary
    original.Client = Client
    original.execute = execute


def freeze():
    if MANIFEST.exists():
        raise ValueError('freeze_exists')
    value = copy.deepcopy(read(ROOT / 'evidence/u1/frozen_v1.json'))
    verify(value)
    rows = read(BASE / 'preflight/zdr.json')
    required = {'reasoning', 'temperature', 'max_tokens', 'response_format'}
    eligible = [r for r in rows if r['model_id'] in ('deepseek/deepseek-v4-pro', 'deepseek/deepseek-v4-pro-0813')
                and required <= set(r['supported_parameters'])
                and float(r['pricing']['prompt']) <= 1e-6 and float(r['pricing']['completion']) <= 2e-6]
    eligible.sort(key=lambda r: (float(r['pricing']['prompt']) + float(r['pricing']['completion']), r['model_id'], r['tag']))
    stronger = eligible[0] if eligible else None
    config = {'model': 'deepseek/deepseek-v4.1-flash', 'route': 'wafer', 'reasoning': False,
              'minimum_start_interval_s': 2}
    value.update(freeze_version='u1-resume-v1', frozen_at_utc=datetime.now(timezone.utc).isoformat(),
                 parent_manifest_sha256=sha(ROOT / 'evidence/u1/frozen_v1.json'),
                 authorization='Owner requested model replacement/backups then continuation; original fixed route disappeared. Independent full run, not a continuation of v1 rows.',
                 configs={'main': config, 'same_reasoning': dict(config, reasoning=True),
                          'stronger': dict(model=stronger['model_id'], route=stronger['tag'], reasoning=True,
                                           minimum_start_interval_s=6) if stronger else None},
                 descriptive_stronger_skip=None if stronger else 'no_compatible_zdr_route_under_inherited_price_caps')
    value['official_metadata'] = {'source': 'https://openrouter.ai/api/v1/endpoints/zdr',
                                  'sha256': sha(BASE / 'preflight/zdr.json'), 'chosen_stronger': stronger, 'fee_for_preflight': 0}
    value['request_policy']['transport'] = 'Concurrency 1. Starts >=2s apart (stronger >=6s). One identical retry only for 429/502/503/504/connection failures; wait max(30s, Retry-After)+uniform[0,3]s. Second failure stops lane. No fallback within a lane, no content retry. Fresh ZDR validation <=60s old.'
    value['model_switch']['action'] = 'If main Ua does not pass and a complete description arm passes, create immutable switched.json before full 180-call Ua rerun with unchanged prompts/criteria. Only one switch.'
    value['implementation_changes'] = ['Reject meaning empty after normalization; no fixture contains such meaning.',
                                        'Independent raw/output directories; original workers, scripts, prompts, scoring and chain schedule reused. New transport pacing/metadata/Retry-After rules above.']
    for path in sorted((ROOT / 'u1_resume').glob('*.py')) + [OUT / 'PRE_RUN.md', ROOT / 'p7/routing.py', ROOT / 'p7/proxy.py']:
        value['source_sha256'][path.relative_to(ROOT).as_posix()] = sha(path)
    value['shared_budget']['used_at_freeze'] = occupancy()
    write_json(MANIFEST, value)
    print(sha(MANIFEST))


def occupancy():
    with sqlite3.connect((ROOT / 'runs/phase1/budget.sqlite').resolve().as_uri() + '?mode=ro', uri=True) as db:
        return db.execute('SELECT COALESCE(SUM(usd),0) FROM charges').fetchone()[0]


def execute(name, manifest_path, config_name, **args):
    folder = BASE / name
    folder.mkdir(parents=True, exist_ok=False)
    job = dict(folder=str(folder), manifest=str(manifest_path), config_name=config_name, **args)
    write_json(folder / 'job.json', job)
    env = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONIOENCODING='utf-8')
    process = subprocess.run([sys.executable, '-m', 'u1_resume.run', 'worker', str(folder / 'job.json')],
                             cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3700)
    (folder / 'stdout.txt').write_bytes(process.stdout)
    (folder / 'stderr.txt').write_bytes(process.stderr)
    if not (folder / 'result.json').exists():
        write_json(folder / 'result.json', {'pass': False, 'status': 'stopped', 'stop': 'worker_without_result', 'returncode': process.returncode})
    value = read(folder / 'result.json')
    print(json.dumps({'stage': name, 'status': value['status'], 'pass': value['pass']}), flush=True)
    return value


def report(result):
    decisions, responses, errors, resources = [], [], [], []
    for folder in ('v1', 'switched'):
        for path in sorted((BASE / folder).rglob('decisions.jsonl')):
            decisions.extend(dict(run=path.parent.relative_to(BASE).as_posix(), **json.loads(s))
                             for s in path.read_text(encoding='utf-8').splitlines())
        for path in sorted((BASE / folder).rglob('calls.jsonl')):
            for line in path.read_text(encoding='utf-8').splitlines():
                row = json.loads(line)
                if row.get('record_type') == 'response':
                    responses.append(row['meta'])
                elif row.get('record_type') == 'transport_error':
                    errors.append(row)
                elif row.get('record_type') == 'telemetry':
                    resources.append(row)
    result['accounting'] = {'successful_calls': len(responses), 'errors': len(errors),
                            'reported_usd': sum(m['cost_usd'] for m in responses if isinstance(m.get('cost_usd'), (int, float))),
                            'successful_charge_ids': [m['charge_id'] for m in responses],
                            'shared_ledger_occupancy_usd': occupancy(), 'unknown_reservations_retained': True}
    result['frozen_files_unchanged'] = True
    verify(read(MANIFEST))
    write_json(OUT / 'results.json', result)
    write_json(OUT / 'decisions.json', decisions)
    write_json(OUT / 'transport_errors.json', errors)
    write_json(OUT / 'resources.json', resources)


def run(reviewed):
    if sha(MANIFEST) != reviewed:
        raise ValueError('reviewed_hash_mismatch')
    if (OUT / 'results.json').exists() or (BASE / 'v1').exists():
        raise ValueError('existing_run_no_automatic_rerun')
    value = read(MANIFEST)
    verify(value)
    configure()
    result = {'status': 'running', 'reviewed_manifest_sha256': reviewed, 'started_utc': datetime.now(timezone.utc).isoformat()}
    active, selected, prefix = MANIFEST, 'main', 'v1'
    try:
        for label in ('main', 'same_reasoning', 'stronger'):
            result['Ua_' + label] = (execute('v1/Ua_' + label, MANIFEST, label, operation='ua', main_comparison=label == 'main')
                                    if value['configs'][label] else {'status': 'skipped', 'pass': False, 'stop': value['descriptive_stronger_skip']})
            report(result)
        if not result['Ua_main']['pass']:
            selected = next((k for k in ('same_reasoning', 'stronger') if result['Ua_' + k]['pass']), None)
            if not selected:
                result['status'] = 'STOP_UA'
                return
            active, prefix = OUT / 'switched.json', 'switched'
            if active.exists():
                raise ValueError('switch_exists')
            switched = copy.deepcopy(value)
            switched.update(freeze_version='u1-resume-switched', selected_config=selected,
                            switch_evidence={k: result[k] for k in ('Ua_main', 'Ua_same_reasoning', 'Ua_stronger')},
                            frozen_at_utc=datetime.now(timezone.utc).isoformat())
            write_json(active, switched)
            result['model_switch'] = {'selected': selected, 'manifest_sha256': sha(active)}
            result['Ua_switched'] = execute(prefix + '/Ua_main', active, selected, operation='ua', main_comparison=True)
            if not result['Ua_switched']['pass']:
                result['status'] = 'STOP_UA_SWITCHED'
                return
        store = BASE / prefix / 'ub.sqlite'
        result['Ub'] = execute(prefix + '/Ub', active, selected, operation='ub', store=str(store))
        report(result)
        if not result['Ub']['pass']:
            result['status'] = 'STOP_UB'
            return
        result['Uc'] = execute(prefix + '/Uc', active, selected, operation='uc', store=str(store),
                               ub_result=str(BASE / prefix / 'Ub/result.json'))
        report(result)
        if result['Uc']['status'] == 'stopped' and result['Uc'].get('stop') in ('budget_stop', 'ac_required', 'frozen_files_changed'):
            result['status'] = 'STOP_RESOURCE'
            return
        result['chain'] = original.run_chain(prefix, active, selected, result)
        result['status'] = 'PASS_U1' if result['chain']['pass'] and result['Uc']['pass'] else 'U1_NOT_PASSED'
    except Exception as error:
        result.update(status='stopped', stop=str(error) if isinstance(error, ValueError) else type(error).__name__)
    finally:
        result['finished_utc'] = datetime.now(timezone.utc).isoformat()
        report(result)
        print(json.dumps({'status': result['status']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['freeze', 'worker', 'run'])
    parser.add_argument('argument', nargs='?')
    args = parser.parse_args()
    if args.command == 'freeze':
        freeze()
    elif args.command == 'worker':
        configure()
        original.worker(args.argument)
    else:
        run(args.argument)
