"""Extract exact historical messages; reconstruct only the 13 untested U3a cases."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from companion.memory import Memory
from growthlab.records import ROOT
from u2 import protocol as u2
from u3 import protocol as u3
from u3.common import read, write, sha
from u3.study import a_store

OUT = ROOT / 'evidence/u4'
BASE = ROOT / 'runs/u4'


def rows(path):
    return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').splitlines()] if Path(path).exists() else []


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def historical(folder):
    """Join by settled call ID, not order or a context that omits test phase."""
    calls = rows(folder / 'calls.jsonl')
    requests = {}
    pending = None
    for event in calls:
        if event['event'] == 'request':
            pending = event
        elif event['event'] == 'response' and pending:
            identity = event['meta'].get('charge_id')
            if identity:
                if identity in requests:
                    raise ValueError('duplicate_historical_charge')
                requests[identity] = pending['request']
            pending = None
    result = []
    for decision in rows(folder / 'decisions.jsonl'):
        request = requests[decision['meta']['charge_id']]
        result.append((decision, request, {'kind': 'original_call',
            'calls_file': (folder / 'calls.jsonl').relative_to(ROOT).as_posix(),
            'calls_sha256': sha(folder / 'calls.jsonl'),
            'decisions_file': (folder / 'decisions.jsonl').relative_to(ROOT).as_posix(),
            'decisions_sha256': sha(folder / 'decisions.jsonl'), 'charge_id': decision['meta']['charge_id']}))
    return result


def entry(identity, domain, case, request, provenance, old=None, **fields):
    messages, schema = deepcopy(request['messages']), deepcopy(request['response_format'])
    return {'id': identity, 'domain': domain, 'case': case, **fields, 'messages': messages,
        'response_format': schema, 'messages_sha256': digest(messages), 'schema_sha256': digest(schema),
        'message_content_sha256': [hashlib.sha256(m['content'].encode()).hexdigest() for m in messages],
        'original_request': deepcopy(request), 'provenance': provenance,
        'historical': {'output': old['output'], 'meta': old['meta']} if old else None}


def build():
    u3out = ROOT / 'evidence/u3'
    u2out = ROOT / 'evidence/u2/round2'
    f1out = ROOT / 'evidence/f1'
    result = []
    material = read(u3out / 'A_MATERIALIZED.json')['items']
    eligible = read(u3out / 'A_SCREEN_RESULTS.json')['eligible_ids']
    old = {d['item_id']: (d, r, p) for d, r, p in historical(u3out / 'raw/a/test_S1')}
    missing = [i for i in material if i['id'] in eligible and i['id'] not in old]
    generated = BASE / 'reconstructed_a'
    if not generated.exists():
        a_store(generated, missing)
    created = read(generated / 'created.json')['stores']
    if set(created) != {i['id'] for i in missing}:
        raise ValueError('generated_population_changed')
    for item in material:
        if item['id'] not in eligible:
            continue
        if item['id'] in old:
            decision, request, provenance = old[item['id']]
        else:
            archive = generated / (item['id'] + '.sqlite')
            if sha(archive) != created[item['id']]['sha256']:
                raise ValueError('generated_archive_changed')
            with Memory.readonly(archive) as memory:
                messages = u3.packet(item, memory.library.sources(), 'S1')
            request = {'model': u2.MODEL, 'stream': False, 'temperature': 0, 'max_tokens': 1024,
                'reasoning': {'enabled': False}, 'messages': messages, 'response_format': u3.schema(item, 'S1')}
            decision = None
            provenance = {'kind': 'frozen_constructor', 'method': 'u3.study.a_store + Memory.readonly.library.sources + u3.protocol.packet/schema(S1)',
                'source_sha256': {name: sha(ROOT / name) for name in ('u3/study.py', 'u3/protocol.py', 'u3/A_MATERIALIZED.json') if (ROOT / name).exists()},
                'material_sha256': sha(u3out / 'A_MATERIALIZED.json'), 'archive_sha256': sha(archive),
                'source_ids': created[item['id']]['source_ids'],
                'random_id_rule': 'Original constructor generated UUIDs once; exported messages fix every source ID. No learning/model calls.'}
        result.append(entry('a/' + item['id'], 'question', item, request, provenance, decision,
                            kind='u3a', format='S1', prior_aligned=item['prior_aligned']))
    people = read(u2out / 'FROZEN.json')['personas']
    for person, items in people.items():
        questions = {i['id']: i for i in items if i['category'] == 'Q'}
        for decision, request, provenance in historical(u2out / f'raw/main/person{person}/B_R/learn'):
            item = questions[decision['item_id']]
            result.append(entry(f'q/{person}/{item["id"]}', 'question', item['question'], request, provenance, decision,
                kind='u2q', person=person, should_ask=item['should_ask'], subtype=item['subtype']))
    bmaterial = read(u3out / 'B_MATERIALIZED.json')['people']
    for person, data in bmaterial.items():
        moments = {m['id']: m for m in data['test']}
        for arm in u3.ARMS:
            for decision, request, provenance in historical(u3out / f'raw/b/S1/person{person}/{arm}/test'):
                moment = moments[decision['moment_id']]
                result.append(entry(f'b/{person}/{arm}/{moment["id"]}', 'timing', moment, request, provenance, decision,
                    person=person, arm=arm, acquired=decision['acquired_before_test'], format='S1'))
    fmaterial = read(ROOT / 'u3/F1_MATERIALS.json')['people']
    for person, data in fmaterial.items():
        cases = {(i['id'], c['phase']): (i, c) for i in data['items'] for c in i['tests']}
        for arm, folder in [('before', u2out / f'raw/main/person{person}/B_R/test'),
                            ('after', f1out / f'raw/person{person}/test'),
                            ('none', u2out / f'raw/main/person{person}/B_N/test')]:
            for decision, request, provenance in historical(folder):
                item, case = cases[(decision['item_id'], decision['phase'])]
                result.append(entry(f'f/{person}/{arm}/{item["id"]}/{case["phase"]}', 'forget', case, request, provenance, decision,
                    person=person, arm=arm, item_id=item['id'], category=item['category'], phase=case['phase'],
                    deleted=item['id'] in data['deleted_ids']))
    validate(result)
    return result


def validate(values):
    if Counter(v['domain'] for v in values) != {'question': 33, 'timing': 288, 'forget': 246}:
        raise ValueError('wrong_population')
    if len({v['id'] for v in values}) != 567:
        raise ValueError('duplicate_input_id')
    if sum(v['historical'] is None for v in values) != 13:
        raise ValueError('unexpected_missing_D0')
    for value in values:
        if digest(value['messages']) != value['messages_sha256'] or digest(value['response_format']) != value['schema_sha256']:
            raise ValueError('input_hash_mismatch')
        if value['messages'] != value['original_request']['messages'] or value['response_format'] != value['original_request']['response_format']:
            raise ValueError('changed_message_or_schema')


def prepare():
    target = OUT / 'INPUTS.jsonl'
    if target.exists():
        values = rows(target)
        validate(values)
        return values
    values = build()
    OUT.mkdir(parents=True, exist_ok=True)
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        for value in values:
            stream.write(json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n')
    return values


if __name__ == '__main__':
    values = prepare()
    print(json.dumps({'counts': dict(Counter(v['domain'] for v in values)),
        'historical_D0': sum(v['historical'] is not None for v in values), 'generated': 13,
        'inputs_sha256': sha(OUT / 'INPUTS.jsonl')}))
