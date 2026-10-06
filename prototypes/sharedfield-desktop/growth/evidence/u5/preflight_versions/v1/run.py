"""Immutable preregistration, single caller, restart without replaying decisions."""
import argparse
from collections import Counter
import hashlib
import json
import random
import shutil
import subprocess
import sys

from companion.chatgpt_oauth import file_lock
from growthlab.records import ROOT
from u2.client import Stop
from u3.common import read, write, sha, utc, append, budget_snapshot, cost
from u4.run import RESUMABLE
from .corpus import BASE, OUT, SEED, prepare, rows, digest, validate
from .scoring import grade
from .client import Client, projection

FROZEN = OUT / 'FROZEN.json'


def freeze():
    if FROZEN.exists():
        return verify()
    assert not any((BASE / j / 'calls.jsonl').exists() for j in ('D0', 'D1'))
    tests = subprocess.run([sys.executable, '-m', 'unittest', 'u5.test_u5', '-q'], capture_output=True, text=True)
    write(OUT / 'ENGINEERING.json', {'passed': tests.returncode == 0, 'stdout': tests.stdout, 'stderr': tests.stderr,
                                   'at_utc': utc(), 'cloud_calls': 0})
    if tests.returncode:
        raise Stop('engineering_failed')
    inputs = prepare()
    order = [i['id'] for i in inputs if i['domain'] != 'noise']
    random.Random(SEED+1).shuffle(order)
    noise = [i['id'] for i in inputs if i['domain'] == 'noise']
    random.Random(SEED+2).shuffle(noise)
    by_id = {i['id']: i for i in inputs}
    plans = {'D0': order+noise, 'D1': order}
    new_order = {j: [i for i in seq if not (j == 'D0' and by_id[i]['historical'])] for j, seq in plans.items()}
    assert {j: len(v) for j, v in new_order.items()} == {'D0': 481, 'D1': 586}
    u4 = read(ROOT / 'evidence/u4/FROZEN.json')
    for manifest, names in [('evidence/u3/FROZEN.json', ['u3/protocol.py', 'u3/statistics.py', 'u3/study.py', 'u3/materials.py', 'u3/baselines.py']),
                            ('evidence/u4/FROZEN.json', ['u2/protocol.py', 'u3/f1.py', 'u4/client.py', 'u4/scoring.py'])]:
        old = read(ROOT / manifest)['source_sha256']
        for name in names:
            assert sha(ROOT / name) == old[name], name
    names = set(u4['source_sha256']) | {'u2/client.py', 'u2/study.py', 'u3/materials.py', 'growthlab/models.py',
        'growthlab/records.py', 'companion/memory.py', 'u1/conventions/core.py', 'u1_resume/library.py'}
    names.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'u5').glob('*.py'))
    evidence = {'evidence/u5/INPUTS.jsonl', 'evidence/u5/CONSTRUCTION.json', 'evidence/u5/F1B_RELEVANCE.json',
        'evidence/u5/ENGINEERING.json', 'evidence/u4/FROZEN.json', 'evidence/u4/INPUTS.jsonl',
        'evidence/u4/RESULTS.json', 'evidence/u3/FROZEN.json', 'evidence/u3/B_MATERIALIZED.json',
        'evidence/u3/BASELINES.json', 'u3/F1_MATERIALS.json', 'CODEX_KICKOFF_U5.md'}
    evidence.update(p.relative_to(ROOT).as_posix() for p in (OUT/'memories').rglob('*.json'))
    for judge in ('D0', 'D1', 'D2'):
        evidence.add(f'evidence/u4/raw/{judge}/decisions.jsonl')
    for person in ('1', '2', '3'):
        for arm in ('R', 'N'):
            for name in ('calls.jsonl', 'decisions.jsonl'):
                evidence.add(f'evidence/u3/raw/b/S0/person{person}/{arm}/test/{name}')
        for name in ('calls.jsonl', 'decisions.jsonl', 'learned.json'):
            evidence.add(f'evidence/u3/raw/b/S0/person{person}/R/learn/{name}')
    design = (ROOT/'GROWTH_DESIGN_v0.md').read_text(encoding='utf-8')
    value = {'version': 1, 'frozen_at_utc': utc(), 'seed': SEED, 'synthetic_only': True,
        'judges': {j: u4['judges'][j] for j in ('D0', 'D1')}, 'temperature': 0,
        'order': plans, 'new_order': new_order,
        'input_manifest': [{'id': i['id'], 'record_sha256': digest(i), 'messages_sha256': i['messages_sha256'],
                           'schema_sha256': i['schema_sha256'], 'content_sha256': i['message_content_sha256']} for i in inputs],
        'criteria_verbatim': design[design.index('### 25.4 '):design.index('### 25.5 ')],
        'construction_verbatim': design[design.index('### 25.3 '):design.index('### 25.4 ')],
        'f1b_thresholds': {'deleted_max_above_own_N': .10, 'retained_max_drop_from_own_before': .10},
        'statistics': {'replicates': 20000, 'seed': 2026100603+900, 'quantiles': [.025, .975],
            'unit': 'paired test moment, sample 24 within each of 3 persons, sums then contrasts',
            'order_within_person': 'original U3 B_MATERIALIZED test order',
            'phenomenon': 'N.active - R.active', 'C5': 'precedent.active - N.active',
            'C1': 'feedback.utility - feedback_control.utility', 'C3': 'scope.utility - scope_shuffled.utility',
            'positive_rule': 'CI lower bound > 0; D5 stops interpretation; absent phenomenon makes mechanisms report only'},
        'reporting_definitions': {'active': ['ask', 'repeat', 'suggest'], 'passive': ['quiet', 'reply'],
            'busy_speaking': 'valid primary action other than quiet while busy; includes normal reply',
            'invalid': 'U3 original -3 primary utility; not counted as passive or active',
            'program_speaker': 'program, with Chinese prefix （程序补充）; source lists derived in JSON without modifying canonical store API',
            'information_bonus': 'Original R acquisitions for every arm, including N. All 96 original S0 acquisitions are false.',
            'scope_width': '早上/晚上，工作日/休息日，在忙/不忙，话题提过/没提; fixed character count',
            'control_text': 'same U3 I constructor u2.study.unrelated, preserves length, position, speaker and prefix'},
        'retry': u4['retry'], 'dollar_cap_usd': 2.0, 'daily_budget': budget_snapshot(),
        'cost_projection': 'After each decision and before every request: actual total including unknown reserves plus remaining counts times observed mean by judge/domain/arm; unobserved strata use D0 .35/451, noise .01/30, D1 1.1/586. Stop when >2; no automatic budget override.',
        'original_archives_sha256': {c['archive']: c['archive_sha256'] for c in read(OUT/'CONSTRUCTION.json').values()},
        'source_sha256': {n: sha(ROOT/n) for n in sorted(names)},
        'evidence_sha256': {n: sha(ROOT/n) for n in sorted(evidence)},
        'claim_ceiling': 'Synthetic memory-only mechanism diagnostics and F1b collateral effects; no evidence she learned anything.'}
    write(FROZEN, value, exclusive=True)
    return value


def verify():
    value = read(FROZEN)
    for key in ('source_sha256', 'evidence_sha256', 'original_archives_sha256'):
        for name, expected in value[key].items():
            if sha(ROOT/name) != expected:
                raise Stop('frozen_file_changed:' + name)
    inputs = rows(OUT/'INPUTS.jsonl')
    validate(inputs)
    assert [(i['id'], digest(i)) for i in inputs] == [(i['id'], i['record_sha256']) for i in value['input_manifest']]
    return value


def load_decisions(folder):
    records = rows(folder/'decisions.jsonl')
    assert len({r['id'] for r in records}) == len(records)
    return {r['id']: r for r in records}


def export(judge):
    source, target = BASE/judge, OUT/'raw'/judge
    target.mkdir(parents=True, exist_ok=True)
    for name in ('decisions.jsonl', 'calls.jsonl', 'routing.jsonl', 'model.jsonl', 'STATUS.json'):
        if (source/name).exists():
            shutil.copyfile(source/name, target/name)
    if (BASE/'COST_STOP.json').exists():
        shutil.copyfile(BASE/'COST_STOP.json', OUT/'COST_STOP.json')


def run(judge, *, resume=False):
    manifest = verify()
    inputs = {i['id']: i for i in rows(OUT/'INPUTS.jsonl')}
    folder = BASE/judge
    folder.mkdir(parents=True, exist_ok=True)
    if (folder/'STATUS.json').exists():
        prior = read(folder/'STATUS.json')
        if prior['state'] == 'stopped' and (not resume or prior['stop'] not in RESUMABLE):
            raise Stop('stopped_lane_requires_review:' + prior['stop'])
    decisions = {j: load_decisions(BASE/j) for j in ('D0', 'D1')}
    completed = decisions[judge]
    if judge == 'D0':
        for item in inputs.values():
            if item['historical'] and item['id'] not in completed:
                row = {'id': item['id'], 'judge': judge, 'origin': 'historical_U3', **item['historical'],
                       'score': grade(item, item['historical']['output'])}
                append(folder/'decisions.jsonl', row)
                completed[item['id']] = row
    for identity, row in completed.items():
        assert row['score'] == grade(inputs[identity], row['output'])
    client = None
    try:
        for identity in manifest['order'][judge]:
            if identity in completed:
                continue
            claim = folder/'claims'/(hashlib.sha256(identity.encode()).hexdigest()+'.json')
            if claim.exists():
                prior = read(claim)
                if prior['state'] == 'calling':
                    raise Stop('uncertain_consumed_decision:' + identity)
                if not resume or prior.get('stop') not in RESUMABLE:
                    raise Stop('explicit_resume_required:' + identity)
            if client is None:
                client = Client(judge, manifest, inputs, decisions)
                for row in reversed(list(completed.values())):
                    if row['score']['valid_output']:
                        break
                    client.invalid_streak += 1
                if client.invalid_streak >= 2:
                    raise Stop('two_consecutive_invalid_outputs')
            client.check()
            write(claim, {'id': identity, 'state': 'calling', 'at_utc': utc(), 'manifest_sha256': sha(FROZEN)})
            try:
                output, meta = client.call(inputs[identity])
            except Stop as error:
                write(claim, {'id': identity, 'state': 'stopped', 'stop': str(error), 'at_utc': utc()})
                raise
            row = {'id': identity, 'judge': judge, 'origin': 'new', 'output': output, 'meta': meta,
                   'score': grade(inputs[identity], output)}
            append(folder/'decisions.jsonl', row)
            write(claim, {'id': identity, 'state': 'complete', 'at_utc': utc()})
            completed[identity] = row
            estimate = projection(manifest, inputs, decisions, cost(BASE/'charge_ids.jsonl'))
            if len(completed) % 10 == 0:
                export(judge)
                print(json.dumps({'judge': judge, 'completed': len(completed), 'planned': len(manifest['order'][judge]),
                    'actual_usd': estimate['actual_usd'], 'projected_usd': estimate['projected_total_usd']}, ensure_ascii=False), flush=True)
            client.parsed(row['score']['valid_output'])
            client.check()
        write(folder/'STATUS.json', {'state': 'complete', 'at_utc': utc(), 'completed': len(completed)})
    except Stop as error:
        write(folder/'STATUS.json', {'state': 'stopped', 'at_utc': utc(), 'completed': len(completed), 'stop': str(error)})
        print(json.dumps({'judge': judge, 'stop': str(error), 'completed': len(completed)}, ensure_ascii=False), flush=True)
    finally:
        export(judge)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('freeze', 'verify', 'run'))
    parser.add_argument('--judge', choices=('D0', 'D1'))
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if args.operation == 'run':
        assert args.judge
        with file_lock(BASE/'runner.lock'):
            run(args.judge, resume=args.resume)
    else:
        v = freeze() if args.operation == 'freeze' else verify()
        print(json.dumps({'manifest_sha256': sha(FROZEN), 'inputs': len(v['input_manifest']),
                          'new_calls': {j: len(o) for j, o in v['new_order'].items()}}))


if __name__ == '__main__':
    main()
