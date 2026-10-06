"""Freeze before spending; resume only decisions with no completed output."""
import argparse
from copy import deepcopy
import json
import random
import shutil
import time

from companion.chatgpt_oauth import file_lock
from growthlab.records import ROOT
from u2.client import Stop
from u2.protocol import MODEL, ROUTE
from u3.common import read, write, sha, utc, append, budget_snapshot
from .client import Client
from .corpus import OUT, BASE, prepare, rows, digest, validate
from .scoring import grade

SEED = 2026100524
FROZEN = OUT / 'FROZEN.json'
RESUMABLE = {'lane_wall_limit', 'daily_budget_stop', 'ac_required', 'operator_stop',
    'subscription_sharing_usage_limit_exceeded', 'subscription_sharing_usage_unavailable',
    'subscription_sharing_user_unavailable', 'chatgpt_login_required', 'invalid_grant'}


def freeze():
    if FROZEN.exists():
        return verify()
    pilot = read(ROOT / 'evidence/d17/PILOT.json')
    if not pilot['ready_for_reasoning_judge']:
        raise Stop('d17_reasoning_trial_incomplete')
    if not read(ROOT / 'evidence/d17/REVOCATION.json')['live_error']:
        raise Stop('d17_revocation_trial_missing')
    engineering = read(OUT / 'ENGINEERING.json')
    if not engineering['passed']:
        raise Stop('engineering_tests_required')
    inputs = prepare()
    historical = sorted(i['id'] for i in inputs if i['historical'])
    repeated = sorted(random.Random(SEED).sample(historical, 60))
    order = sorted(i['id'] for i in inputs)
    random.Random(SEED + 1).shuffle(order)
    design = (ROOT / 'GROWTH_DESIGN_v0.md').read_text(encoding='utf-8')
    extract = lambda first, last: design[design.index(first):design.index(last)]
    source_names = [p.relative_to(ROOT).as_posix() for p in (ROOT / 'u4').glob('*.py')]
    source_names += ['u2/protocol.py', 'u3/protocol.py', 'u3/f1.py', 'u3/statistics.py', 'u3/baselines.py',
        'u3/study.py', 'u3/client.py', 'u3/common.py', 'u1_resume/client.py', 'companion/model.py',
        'companion/chatgpt.py', 'companion/chatgpt_oauth.py', 'companion/budget.py',
        'p7/proxy.py', 'p7/routing.py', 'p7/routing_v2.py', 'p7/routing_v2.json']
    # Source changes to the new transport must never silently replace old scorers.
    for manifest, names in [('evidence/u2/round2/FROZEN.json', ['u2/protocol.py']),
                            ('evidence/u3/FROZEN.json', ['u3/protocol.py', 'u3/statistics.py', 'u3/study.py', 'u3/baselines.py']),
                            ('evidence/f1/FROZEN.json', ['u3/f1.py'])]:
        old = read(ROOT / manifest)['source_sha256']
        for name in names:
            if sha(ROOT / name) != old[name]:
                raise Stop('historical_scorer_changed:' + name)
    evidence = {'evidence/u4/INPUTS.jsonl', 'evidence/u3/BASELINES.json', 'evidence/d17/PILOT.json',
                'evidence/d17/REVOCATION.json', 'evidence/u4/ENGINEERING.json', 'evidence/u3/A_MATERIALIZED.json',
                'evidence/u3/A_SCREEN_RESULTS.json', 'evidence/u3/B_MATERIALIZED.json', 'u3/F1_MATERIALS.json'}
    for item in inputs:
        provenance = item['provenance']
        for key in ('calls_file', 'decisions_file'):
            if key in provenance:
                evidence.add(provenance[key])
    off = {'enabled': False}
    on = {'enabled': True, 'effort': 'low', 'exclude': True}
    value = {'version': 1, 'frozen_at_utc': utc(), 'seed': SEED, 'synthetic_only': True,
        'judges': {
            'D0': {'model': MODEL, 'route': ROUTE, 'reasoning': off, 'max_tokens': 1024},
            'D0_repeat': {'model': MODEL, 'route': ROUTE, 'reasoning': off, 'max_tokens': 1024},
            'D1': {'model': MODEL, 'route': ROUTE, 'reasoning': on, 'max_tokens': 8192},
            'D2': {'model': pilot['model'], 'route': 'chatgpt',
                   'reasoning': {'enabled': True, 'effort': pilot['effort']}, 'max_tokens': 8192}},
        'input_manifest': [{'id': i['id'], 'record_sha256': digest(i), 'messages_sha256': i['messages_sha256'],
                            'schema_sha256': i['schema_sha256'], 'content_sha256': i['message_content_sha256']} for i in inputs],
        'order': order, 'D0_repeat_ids': repeated,
        'D0_missing_ids': sorted(i['id'] for i in inputs if i['historical'] is None),
        'D0_missing_rule': '13 previously untested counter-prior U3a inputs require a first D0 decision; separate from the 60 repeats.',
        'question_U3a_format': 'S1 only, per original self-check condition; 21 eligible items, not just 8 originally tested.',
        'question_U2_arm': 'B_R learning ask moments, exactly 12 original full-message requests.',
        'criteria_verbatim': extract('### 24.4 ', '### 24.5 '),
        'conclusion_rules_verbatim': extract('### 24.5 ', '### 24.6 '),
        'statistics': {'implementation': 'u3.statistics.comparisons', 'replicates': 20000, 'seed': 2026100603 + 900,
                       'bootstrap_unit': 'test moment, paired across arms, stratified by persona'},
        'noise_rule': 'On the same frozen 60 historical inputs, compare action-signature disagreement with original D0. '
                      'If a judge has no greater disagreement than D0_repeat, withhold attribution; apply separately by domain and overall. '
                      'Report raw paired scores as well; the small domain subsets limit precision.',
        'reflex_rule': 'Report F1 retained P after (exact confirm option), U3a known/restriction (ask/repeat), '
                       'and U2 no-ask (relevant ask IDs), separately and pooled. Invalids reported separately; no pass threshold.',
        'd5_scope': 'Every U4 S1 test arm must have zero mechanically scored D5 selections. No relearning decisions are made.',
        'outer_adapter': {'D2': 'Leading system content becomes instructions; remaining messages become input unchanged; '
                         'response_format.json_schema becomes text.format. stream=true, store=false. '
                         'SIWC omits unsupported temperature/max_output_tokens; server sampling defaults differ from D0. '
                         'No injected Codex instructions, tools, truncation, memory or automatic fallback.',
                         'D1': 'Only reasoning=low and max_tokens=8192 change; original messages/schema/temperature unchanged.'},
        'pilot_limitations': 'Astra rejects reasoning=none; no off-mode latency distribution. Live quota not artificially exhausted. '
                             'On-mode 20/20 strict four-field JSON; revoked refresh rejection observed.',
        'retry': {'attempts': 2, 'timeout_s': 60, 'minimum_start_interval_s': 2,
                  'backoff': 'max(30, Retry-After)+uniform(0,3)', 'subscription_quota': 'no retry; stop and resume remaining only',
                  'invalid_outputs': 'score once; stop after two consecutive invalids; no corrective prompt',
                  'uncertain_interruption': 'stop on a claimed decision with no terminal record; never blindly replay'},
        'dollar_cap_usd': 1.20, 'daily_budget': budget_snapshot(),
        'D2_budget': 'subscription only; owner confirmed credits disabled or app cap below 100%; record calls/tokens/errors separately',
        'source_sha256': {name: sha(ROOT / name) for name in sorted(set(source_names))},
        'evidence_sha256': {name: sha(ROOT / name) for name in sorted(evidence)},
        'claim_ceiling': 'Distinguish judge bottlenecks from method limitations on synthetic frozen inputs; not evidence of learning.'}
    write(FROZEN, value, exclusive=True)
    return value


def verify():
    value = read(FROZEN)
    for group in ('source_sha256', 'evidence_sha256'):
        for name, expected in value[group].items():
            if sha(ROOT / name) != expected:
                raise Stop('frozen_file_changed:' + name)
    inputs = rows(OUT / 'INPUTS.jsonl')
    validate(inputs)
    if [(i['id'], digest(i)) for i in inputs] != [(i['id'], i['record_sha256']) for i in value['input_manifest']]:
        raise Stop('frozen_input_changed')
    return value


def already_completed(path):
    values = rows(path)
    if len({v['id'] for v in values}) != len(values):
        raise Stop('duplicate_completed_decision')
    return {v['id']: v for v in values}


def run_judge(judge, *, resume=False):
    manifest = verify()
    inputs = {i['id']: i for i in rows(OUT / 'INPUTS.jsonl')}
    folder = BASE / judge
    folder.mkdir(parents=True, exist_ok=True)
    if (folder / 'STATUS.json').exists():
        previous = read(folder / 'STATUS.json')
        if previous['state'] == 'stopped' and (not resume or previous.get('stop') not in RESUMABLE):
            raise Stop('stopped_lane_requires_review:' + previous.get('stop', 'unknown'))
    result_path = folder / 'decisions.jsonl'
    completed = already_completed(result_path)
    if judge == 'D0':
        for item in inputs.values():
            if item['historical'] and item['id'] not in completed:
                row = {'id': item['id'], 'judge': judge, 'origin': 'historical',
                       **item['historical'], 'score': grade(item, item['historical']['output'])}
                append(result_path, row)
        completed = already_completed(result_path)
    for identity, record in completed.items():
        if record['score'] != grade(inputs[identity], record['output']):
            raise Stop('completed_score_changed')
    sequence = manifest['D0_repeat_ids'] if judge == 'D0_repeat' else manifest['order']
    client = None
    try:
        for identity in sequence:
            if identity in completed:
                continue
            item = inputs[identity]
            claim = folder / 'claims' / (hashlib_id(identity) + '.json')
            if claim.exists():
                prior = read(claim)
                if prior['state'] == 'calling':
                    raise Stop('uncertain_consumed_decision:' + identity)
                if not resume or prior.get('stop') not in RESUMABLE:
                    raise Stop('explicit_resume_required:' + identity)
            if client is None:
                client = Client(judge, manifest['judges'][judge], cap=manifest['dollar_cap_usd'])
            # Checks before claiming distinguish a stopped runner from an unknown request.
            client.check()
            write(claim, {'id': identity, 'state': 'calling', 'at_utc': utc(), 'manifest_sha256': sha(FROZEN)})
            try:
                output, meta = client.call(item)
            except Stop as error:
                write(claim, {'id': identity, 'state': 'stopped', 'stop': str(error), 'at_utc': utc()})
                raise
            row = {'id': identity, 'judge': judge, 'origin': 'new', 'output': output, 'meta': meta, 'score': grade(item, output)}
            append(result_path, row)
            write(claim, {'id': identity, 'state': 'complete', 'at_utc': utc()})
            completed[identity] = row
            export(judge)
            print(json.dumps({'judge': judge, 'completed': len(completed), 'planned': len(sequence),
                              'id': identity, 'valid': row['score']['valid_output']}, ensure_ascii=False), flush=True)
            client.parsed(row['score']['valid_output'])
        write(folder / 'STATUS.json', {'state': 'complete', 'at_utc': utc(), 'completed': len(completed)})
    except Stop as error:
        write(folder / 'STATUS.json', {'state': 'stopped', 'at_utc': utc(), 'completed': len(completed), 'stop': str(error)})
        print(json.dumps({'judge': judge, 'stop': str(error), 'completed': len(completed)}, ensure_ascii=False), flush=True)
    finally:
        export(judge)


def hashlib_id(identity):
    import hashlib
    return hashlib.sha256(identity.encode()).hexdigest()


def export(judge):
    source, destination = BASE / judge, OUT / 'raw' / judge
    destination.mkdir(parents=True, exist_ok=True)
    for name in ('decisions.jsonl', 'calls.jsonl', 'routing.jsonl', 'model.jsonl', 'STATUS.json'):
        if (source / name).exists():
            shutil.copyfile(source / name, destination / name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('freeze', 'verify', 'run'))
    parser.add_argument('--judge', choices=('D0', 'D0_repeat', 'D1', 'D2'))
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    if args.operation != 'run':
        value = freeze() if args.operation == 'freeze' else verify()
        print(json.dumps({'manifest_sha256': sha(FROZEN), 'inputs': len(value['input_manifest'])}))
    else:
        if not args.judge:
            parser.error('--judge required')
        with file_lock(BASE / 'runner.lock'):
            run_judge(args.judge, resume=args.resume)


if __name__ == '__main__':
    main()
