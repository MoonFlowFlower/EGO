"""python -m u1.run {engineering,freeze,run}; live work requires a reviewed freeze."""
import argparse
import json
import os
import sqlite3
import statistics
import subprocess
import sys
import time
from pathlib import Path

from growthlab.forks import fork_storage
from growthlab.records import ROOT, write_json
from .conventions import ConventionLibrary
from .fixtures import teaching
from .harness import Client, Stop, byte_check, consolidate, decision, ingest, rate
from .plan import BASE, OUT, MANIFEST, freeze, read, sha, switch_manifest, verify
from .protocol import follows, keyword_score


def ua_summary(folder, expected):
    rows = [json.loads(s) for s in (folder / 'decisions.jsonl').read_text(encoding='utf-8').splitlines()] if (folder / 'decisions.jsonl').exists() else []
    table = []
    for arm in ('B', 'A'):
        for family in ('code', 'emotion', 'promise'):
            for condition in ('none', 'true', 'false'):
                selected = [r for r in rows if r['arm'] == arm and r['family'] == family and r['context']['condition'] == condition]
                if selected:
                    table.append({'arm': arm, 'family': family, 'condition': condition, **rate(selected)})
    relevant = [r for r in table if r['arm'] == 'B' and r['family'] == 'code' and r['condition'] in ('true', 'false')]
    passed = len(rows) == expected and len(relevant) == 2 and all(r['n'] == 10 and r['follows'] >= 8 for r in relevant)
    prior = [{'arm': r['arm'], 'case_id': r['case_id'], 'already_follows_without_memory': r['follows']}
             for r in rows if r['family'] == 'emotion' and r['context']['condition'] == 'none']
    return {'pass': passed, 'decisions': len(rows), 'expected': expected, 'table': table,
            'emotional_prior_audit': prior, 'claim': 'Ua tests use of supplied memory only.'}


def worker_ua(job, data, client):
    folder = Path(job['folder'])
    arms = ('B', 'A') if job['main_comparison'] else ('B',)
    for case in data['ua_cases']:
        f = data['conventions'][case['fixture_id']]
        for condition in ('none', 'true', 'false'):
            for arm in arms:
                path = folder / f"{arm}_{f['fixture_id']}_{condition}.sqlite"
                with ConventionLibrary(path) as lib:
                    if condition != 'none' and not lib.sources():
                        ids = ingest(lib, teaching(f, false=condition == 'false'))
                        meaning = f['false_meaning'] if condition == 'false' else f['meaning']
                        if arm == 'B':
                            lib.propose({'trigger': f['trigger'], 'meaning': meaning, 'source_ids': [ids[0]], 'replaces': ''}, allowed_ids=ids)
                        else:
                            lib.reflect(f"用户说的「{f['trigger']['text']}」表示「{meaning}」。这是用户教过的约定。", ids)
                    target = f['target']['true' if condition == 'none' else condition]
                    decision(lib, arm, client, case, target,
                             {'phase': 'Ua', 'config': job['config_name'], 'condition': condition, 'case_id': case['case_id'], 'arm': arm})
    return ua_summary(folder, 180 if job['main_comparison'] else 90)


def worker_ub(job, data, client):
    rows = []
    with ConventionLibrary(job['store']) as lib:
        for fixture in data['ub']:
            ids = ingest(lib, fixture['dialogue'])
            report = consolidate(lib, 'B', client, ids, {'phase': 'Ub', 'fixture_id': fixture['fixture_id']})
            correct = [c for c in lib.cards() if keyword_score(c, fixture)]
            rows.append({'fixture_id': fixture['fixture_id'], 'teaching_mode': fixture['teaching_mode'],
                         'pass': bool(correct), 'correct_card_ids': [c['card_id'] for c in correct], 'consolidation': report})
            write_json(Path(job['folder']) / 'ub_partial.json', rows)
        correct_cards = [c for c in lib.cards() if any(keyword_score(c, fixture) for fixture in data['ub'])]
    return {'pass': sum(r['pass'] for r in rows) >= 8, 'correct': sum(r['pass'] for r in rows), 'n': 10,
            'rows': rows, 'correct_cards': correct_cards}


def worker_uc(job, data, client):
    rounds = []
    ub_result = read(job['ub_result'])
    initial = {c['card_id']: c for c in ub_result['correct_cards']}
    with ConventionLibrary(job['store']) as lib:
        for round_index, dialogue in enumerate(data['uc_unrelated']):
            ingest(lib, dialogue)
            ids = [s['utterance_id'] for s in lib.sources()]
            report = consolidate(lib, 'B', client, ids, {'phase': 'Uc', 'round': round_index + 1})
            current = {c['card_id']: c for c in lib.cards()}
            changed = [i for i, card in initial.items() if i not in current or current[i] != card]
            rounds.append({'round': round_index + 1, 'pass': not changed, 'changed_or_lost': changed, 'consolidation': report})
            write_json(Path(job['folder']) / 'uc_partial.json', rounds)
    return {'pass': all(r['pass'] for r in rounds), 'initial_correct_cards': len(initial), 'rounds': rounds}


def worker_learn(job, data, client):
    dialogue = data[job['dialogue_key']] if job.get('dialogue_key') else []
    results = []
    with ConventionLibrary(job['store']) as lib:
        sessions = list(dict.fromkeys(r['session_id'] for r in dialogue))
        for session in sessions:
            batch = [r for r in dialogue if r['session_id'] == session]
            ids = ingest(lib, batch)
            results.append(consolidate(lib, job['arm'], client, ids,
                                       {'phase': job['phase'], 'group': job['group'], 'session_id': session}))
        if not sessions:
            results.append({'status': 'no_evidence_noop', 'accepted': []})
        # State counts/hash/PID verify restart without exporting another state copy.
        provenance = []
        for c in lib.cards(active_only=False):
            provenance.append({'card_id': c['card_id'], 'card_status': c['card_status'],
                               'trigger_text': c['trigger']['text'],
                               'source_ids': c['source_ids'],
                               'correction_parents': [r[0] for r in lib.store.db.execute("SELECT parent FROM deps WHERE child=? AND relation='correction'", (c['card_id'],))]})
        state = {'record_count': len(lib.rows(active_only=False)), 'active_cards': len(lib.cards()), 'provenance': provenance}
    return {'pass': True, 'consolidations': results, 'state': state, 'state_sha256': sha(job['store']), 'pid': os.getpid()}


def worker_evaluate(job, data, client):
    cases = data['chain_cases']
    if job['phase'] != 'initial':
        cases = [c for c in cases if c['split'] == 'T1']
    state_before = sha(job['store'])
    with ConventionLibrary(job['store']) as lib:
        for case in cases:
            f = data['conventions'][case['fixture_id']]
            target = f['target']['new' if job['phase'] == 'corrected' else 'true']
            decision(lib, job['arm'], client, case, target,
                     {'phase': job['phase'], 'group': job['group'], 'case_id': case['case_id']})
    rows = [json.loads(s) for s in (Path(job['folder']) / 'decisions.jsonl').read_text(encoding='utf-8').splitlines()]
    table = [{'family': family, 'split': split, **rate([r for r in rows if r['family'] == family and r['split'] == split])}
             for family in ('code', 'emotion', 'promise') for split in ('T1', 'T2')
             if any(r['family'] == family and r['split'] == split for r in rows)]
    return {'pass': True, 'n': len(rows), 'table': table, 'pid': os.getpid(),
            'state_before_sha256': state_before, 'state_after_sha256': sha(job['store'])}


def worker_delete(job, data):
    # The delete command is a local control operation; it is not sent to a model.
    needles = []
    with ConventionLibrary(job['store']) as lib:
        for row in lib.rows(active_only=False):
            body = row['body']
            for key in ('utterance_text', 'meaning', 'reflection_text'):
                if key in body:
                    needles.append(body[key])
            if 'trigger' in body:
                needles.append(body['trigger']['text'])
        if job['arm'] == 'B':
            cards = list(lib.cards())
            deleted = []
            for card in cards:
                if any(c['card_id'] == card['card_id'] for c in lib.cards()):
                    deleted.append(lib.forget(card['card_id']))
            # Include teaching/correction assistant turns. They are session
            # context derived from this controlled teaching conversation too.
            deleted.append(lib.forget_sources([s['utterance_id'] for s in lib.sources()]))
        else:
            deleted = [lib.forget_sources([s['utterance_id'] for s in lib.sources()])]
        state_count = len(lib.rows(active_only=False))
    return {'pass': True, 'commands': data['chain_deletions'], 'receipts': deleted,
            'remaining_records': state_count, 'byte_check': byte_check(job['store'], needles), 'pid': os.getpid()}


def worker(job_path):
    job = read(job_path)
    folder = Path(job['folder'])
    folder.mkdir(parents=True, exist_ok=True)
    manifest = read(job['manifest'])
    verify(manifest)
    data = read(OUT / 'scripts_v1.json')
    client = None
    result = {'pass': False, 'status': 'not_started', 'pid': os.getpid()}
    started = time.time()
    try:
        if job['operation'] == 'delete':
            result = worker_delete(job, data)
        else:
            client = Client(manifest['configs'][job['config_name']], folder)
            function = {'ua': worker_ua, 'ub': worker_ub, 'uc': worker_uc,
                        'learn': worker_learn, 'evaluate': worker_evaluate}[job['operation']]
            result = function(job, data, client)
        result['status'] = 'completed'
    except Exception as error:
        known = isinstance(error, (Stop, ValueError, RuntimeError))
        result.update(status='stopped', stop=str(error) if known else type(error).__name__)
        if job['operation'] == 'ua':
            result.update(ua_summary(folder, 180 if job['main_comparison'] else 90))
            result['pass'] = False
    finally:
        if client:
            client.close()
        try:
            verify(manifest)
            result['frozen_files_unchanged'] = True
        except Exception:
            result.update(frozen_files_unchanged=False, pass_=False, status='stopped', stop='frozen_files_changed')
            result['pass'] = False
        result.update(pid=os.getpid(), elapsed_s=time.time() - started)
        write_json(folder / 'result.json', result)
    print(json.dumps({'operation': job['operation'], 'status': result['status'], 'pass': result['pass'], 'folder': str(folder)}, ensure_ascii=False))


def execute(name, manifest_path, config_name, **args):
    folder = BASE / name
    if folder.exists():
        raise ValueError('run_folder_exists_no_rerun:' + name)
    folder.mkdir(parents=True)
    job = {'folder': str(folder), 'manifest': str(manifest_path), 'config_name': config_name, **args}
    path = folder / 'job.json'
    write_json(path, job)
    env = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONIOENCODING='utf-8')
    process = subprocess.run([sys.executable, '-m', 'u1.run', 'worker', str(path)], env=env,
                             cwd=ROOT.parent, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3700)
    (folder / 'stdout.txt').write_bytes(process.stdout)
    (folder / 'stderr.txt').write_bytes(process.stderr)
    if not (folder / 'result.json').exists():
        write_json(folder / 'result.json', {'pass': False, 'status': 'stopped', 'stop': 'worker_without_result', 'returncode': process.returncode})
    result = read(folder / 'result.json')
    print(json.dumps({'stage': name, 'status': result['status'], 'pass': result['pass']}, ensure_ascii=False), flush=True)
    return result


def load_rows(name):
    path = BASE / name / 'decisions.jsonl'
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []


def chain_summary(prefix, result):
    data = read(OUT / 'scripts_v1.json')
    rows = {group: load_rows(prefix + '/chain/' + group + '/initial') for group in ('B_R', 'B_I', 'B_N', 'A_R')}
    def scored(group, family, phase='initial', target='true'):
        source = rows[group] if phase == 'initial' else load_rows(prefix + '/chain/' + group + '/' + phase)
        selected = [r for r in source if r['family'] == family and r['split'] == 'T1']
        return {'n': len(selected), 'rate': sum(follows(r['selected'], data['conventions']['chain_' + family]['target'][target]) for r in selected) / 10}
    retention = all(scored('B_R', family)['n'] == 10 and scored('B_R', family)['rate'] >= .8 for family in ('code', 'promise'))
    causal = (scored('B_R', 'code')['rate'] >= .8
              and all(scored(g, 'code')['n'] == 10 and scored(g, 'code')['rate'] <= .2 for g in ('B_I', 'B_N')))
    corrected = {f: scored('B_R', f, 'corrected', 'new') for f in ('code', 'emotion', 'promise')}
    correction_result = result['steps']['B_R_correct_learn']
    provenance = correction_result.get('state', {}).get('provenance', [])
    provenance_by_family = {}
    for family in ('code', 'emotion', 'promise'):
        trigger_text = data['conventions']['chain_' + family]['trigger']['text']
        family_cards = [c for c in provenance if c['trigger_text'] == trigger_text]
        active = [c for c in family_cards if c['card_status'] == 'active']
        old = {c['card_id'] for c in family_cards if c['card_status'] == 'superseded'}
        provenance_by_family[family] = len(active) == 1 and all(c['correction_parents'] and set(c['correction_parents']) <= old for c in active)
    linked = all(provenance_by_family[f] for f in ('code', 'promise'))
    correction_okay = linked and all(corrected[f]['n'] == 10 and corrected[f]['rate'] >= .8 for f in ('code', 'promise'))
    deletion = {}
    for family in ('code', 'emotion', 'promise'):
        deletion[family] = {}
        for label in ('true', 'new'):
            after = scored('B_R', family, 'deleted', label)
            reference = scored('B_N', family, target=label)
            deletion[family][label] = {'after': after, 'N': reference, 'pass': after['n'] == 10 and after['rate'] <= reference['rate'] + .100000001}
    byte_pass = result['steps']['B_R_delete']['byte_check']['pass']
    delete_okay = byte_pass and all(v['pass'] for f in ('code', 'promise') for v in deletion[f].values())
    transfer = []
    for group, values in rows.items():
        for family in ('code', 'emotion', 'promise'):
            t2 = [r for r in values if r['family'] == family and r['split'] == 'T2']
            for label, subset in [('all', t2), ('retained_trigger_or_situation', t2[:5]), ('paraphrase_or_new_situation', t2[5:])]:
                transfer.append({'group': group, 'family': family, 'subset': label, **rate(subset)})
    return {'pass': retention and causal and correction_okay and delete_okay, 'retention_pass': retention,
            'causal_pass': causal, 'correction_pass': correction_okay, 'correction_provenance_pass': linked,
            'correction_rates': corrected, 'correction_provenance_by_family': provenance_by_family,
            'deletion_pass': delete_okay, 'deletion_rates': deletion,
            'deletion_byte_pass': byte_pass, 'T2_descriptive': transfer, 'Uc_pass': result['Uc']['pass']}


def run_chain(prefix, manifest_path, config_name, result):
    root = BASE / prefix / 'chain'
    root.mkdir(parents=True, exist_ok=True)
    blank = root / 'blank.sqlite'
    with ConventionLibrary(blank):
        pass
    result['steps'] = {}
    for group in ('B_R', 'B_I', 'B_N', 'A_R'):
        store = root / (group + '.sqlite')
        fork_storage(blank, store)
        arm = group[0]
        learn = execute(prefix + '/chain/' + group + '/learn', manifest_path, config_name,
                        operation='learn', store=str(store), arm=arm, group=group, phase='teaching',
                        dialogue_key='chain_teaching' if group.endswith('R') else ('chain_unrelated' if group == 'B_I' else None))
        result['steps'][group + '_learn'] = learn
        if learn['status'] != 'completed':
            return {'pass': False, 'status': 'stopped', 'stop': group + '_learning_incomplete'}
        tested = execute(prefix + '/chain/' + group + '/initial', manifest_path, config_name,
                         operation='evaluate', store=str(store), arm=arm, group=group, phase='initial')
        result['steps'][group + '_initial'] = tested
        if tested['status'] != 'completed':
            return {'pass': False, 'status': 'stopped', 'stop': group + '_testing_incomplete'}
        if learn['pid'] == tested['pid']:
            raise ValueError('process_restart_not_demonstrated')
    for group in ('B_R', 'A_R'):
        store = root / (group + '.sqlite')
        for suffix, kwargs in [
            ('correct_learn', {'operation': 'learn', 'phase': 'correction', 'dialogue_key': 'chain_corrections'}),
            ('corrected', {'operation': 'evaluate', 'phase': 'corrected'}),
            ('delete', {'operation': 'delete', 'phase': 'deletion'}),
            ('deleted', {'operation': 'evaluate', 'phase': 'deleted'}),
        ]:
            step = execute(prefix + '/chain/' + group + '/' + suffix, manifest_path, config_name,
                           store=str(store), arm=group[0], group=group, **kwargs)
            result['steps'][group + '_' + suffix] = step
            if step['status'] != 'completed':
                return {'pass': False, 'status': 'stopped', 'stop': group + '_' + suffix + '_incomplete'}
    return {'status': 'completed', **chain_summary(prefix, result)}


def report(result):
    returned = []
    shared_deltas = []
    for path in sorted(BASE.rglob('calls.jsonl')):
        if any(part.startswith('engineering') for part in path.parts):
            continue
        for line in path.read_text(encoding='utf-8').splitlines():
            row = json.loads(line)
            if row.get('record_type') == 'response':
                returned.append(row['meta'])
            if row.get('record_type') == 'transport_error':
                shared_deltas.extend(row.get('shared_ledger_delta_unattributed', []))
    known = [r['cost_usd'] for r in returned if isinstance(r.get('cost_usd'), (float, int)) and r['cost_usd'] >= 0]
    latencies = sorted(r['latency_s'] for r in returned)
    budget = ROOT / 'runs/phase1/budget.sqlite'
    db = sqlite3.connect(budget.resolve().as_uri() + '?mode=ro', uri=True)
    occupied = db.execute('SELECT COALESCE(SUM(usd),0) FROM charges').fetchone()[0]
    db.close()
    result['resources'] = {'returned_calls': len(returned), 'exact_reported_u1_cost_usd': sum(known),
                           'successful_calls_without_reported_cost': len(returned) - len(known),
                           'successful_charge_ids': [r['charge_id'] for r in returned],
                           'shared_ledger_occupancy_usd': occupied,
                           'unattributed_shared_error_delta_ids': sorted({r['charge_id'] for r in shared_deltas}),
                           'latency_median_s': statistics.median(latencies) if latencies else None,
                           'latency_p95_s': latencies[min(len(latencies)-1, int(len(latencies)*.95))] if latencies else None,
                           'cost_limit_usd': 5,
                           'cost_caveat': 'U1 exact cost is successful response cost only; failed requests retain conservative reservations. Shared error deltas can include concurrent P7 charges and are never charged to U1 in this statistic.'}
    write_json(OUT / 'results.json', result)
    compact_rows = []
    for path in sorted(BASE.rglob('decisions.jsonl')):
        if 'engineering' in path.parts:
            continue
        for line in path.read_text(encoding='utf-8').splitlines():
            row = json.loads(line)
            compact_rows.append({'run': path.parent.relative_to(BASE).as_posix(), **row})
    write_json(OUT / 'per_decision_results.json', compact_rows)
    summary = ['# U1 result', '', '**Status: ' + result['status'] + '**', '',
               'All cloud inputs/outputs, transport errors, reservations and state stores remain under ignored `growth/runs/u1/`.',
               'This report supports only the frozen synthetic protocol; it is not evidence that the companion understands its owner.', '']
    for name in ('Ua_main', 'Ua_same_reasoning', 'Ua_stronger', 'Ua_switched', 'Ub', 'Uc', 'chain'):
        value = result.get(name)
        if value is not None:
            summary.append('- ' + name + ': ' + json.dumps({k: value[k] for k in ('status', 'pass', 'stop', 'n', 'correct', 'decisions', 'expected') if k in value}, ensure_ascii=False))
    if 'Uc' in result and not result['Uc'].get('pass'):
        summary += ['', 'Uc failed or stopped. The chain is permitted by the card but its outcome carries that failure.']
    summary += ['', 'The full frozen criteria and pre-run ambiguity resolutions are in `frozen_v1.json` (or the explicitly recorded model-switch v2).']
    summary += ['', f"Reported successful U1 cost: ${sum(known):.6f}; shared ledger occupancy: ${occupied:.6f} / $5.",
                'Unknown/failed-request reservations remain occupied; no U1-only charge is inferred from a shared ledger delta.']
    (OUT / 'REPORT.md').write_text('\n'.join(summary) + '\n', encoding='utf-8')


def run(reviewed_hash):
    manifest = read(MANIFEST)
    if sha(MANIFEST) != reviewed_hash:
        raise ValueError('reviewed_manifest_hash_mismatch')
    verify(manifest)
    if (OUT / 'results.json').exists():
        raise ValueError('results_exist_no_automatic_rerun')
    result = {'status': 'running', 'reviewed_manifest_sha256': reviewed_hash,
              'claim_ceiling': manifest['claim_ceiling']}
    config_name, active_manifest, prefix = 'main', MANIFEST, 'v1'
    try:
        # Always separate these jobs: main failure never bypasses description.
        for label, description in [('main', False), ('same_reasoning', True), ('stronger', True)]:
            if manifest['configs'][label] is None:
                value = {'status': 'skipped', 'pass': False, 'stop': manifest['descriptive_stronger_skip']}
            else:
                value = execute('v1/Ua_' + label, MANIFEST, label, operation='ua', main_comparison=not description)
            result['Ua_' + label] = value
            report(result)
        if not result['Ua_main']['pass']:
            choice = next((label for label in manifest['model_switch']['priority'] if result['Ua_' + label]['pass']), None)
            if choice is None:
                result['status'] = 'STOP_UA'
                return result
            active_manifest = switch_manifest(manifest, choice, {k: result[k] for k in ('Ua_main', 'Ua_same_reasoning', 'Ua_stronger')})
            config_name, prefix = choice, 'v2'
            result['model_switch'] = {'selected': choice, 'manifest_sha256': sha(active_manifest),
                                      'reason_category': 'protocol_or_transport_stop' if result['Ua_main']['status'] == 'stopped' else 'completed_quality_gate_failed',
                                      'main_stop': result['Ua_main'].get('stop')}
            result['Ua_switched'] = execute('v2/Ua_main', active_manifest, choice, operation='ua', main_comparison=True)
            if not result['Ua_switched']['pass']:
                result['status'] = 'STOP_UA_SWITCHED'
                return result
        store = BASE / prefix / 'ub.sqlite'
        result['Ub'] = execute(prefix + '/Ub', active_manifest, config_name, operation='ub', store=str(store))
        report(result)
        if not result['Ub']['pass']:
            result['status'] = 'STOP_UB'
            return result
        result['Uc'] = execute(prefix + '/Uc', active_manifest, config_name, operation='uc', store=str(store),
                               ub_result=str(BASE / prefix / 'Ub/result.json'))
        report(result)
        if result['Uc']['status'] == 'stopped' and result['Uc'].get('stop') in ('budget_stop', 'ac_required', 'frozen_files_changed'):
            result['status'] = 'STOP_RESOURCE'
            return result
        result['chain'] = run_chain(prefix, active_manifest, config_name, result)
        result['status'] = 'PASS_U1' if result['chain']['pass'] and result['Uc']['pass'] else 'U1_NOT_PASSED'
        return result
    finally:
        verify(manifest)
        result['frozen_files_unchanged'] = True
        report(result)


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('freeze')
    sub.add_parser('engineering')
    live = sub.add_parser('run')
    live.add_argument('--reviewed-manifest-sha256', required=True)
    one = sub.add_parser('worker')
    one.add_argument('job')
    args = parser.parse_args()
    if args.command == 'freeze':
        freeze()
        print(sha(MANIFEST))
    elif args.command == 'engineering':
        from .tests import engineering
        print(json.dumps(engineering(), ensure_ascii=False, indent=2))
    elif args.command == 'worker':
        worker(args.job)
    else:
        result = run(args.reviewed_manifest_sha256)
        print(json.dumps({'status': result['status']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
