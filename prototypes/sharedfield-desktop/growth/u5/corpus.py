"""Derive utterance lists from read-only S0 R archives; no model calls."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
import random
import re

from companion.memory import Memory
from growthlab.records import ROOT
from u2.study import unrelated
from u3.common import read, write, sha
from u3.f1 import DIRECTIVE, TOPICS
from u3.materials import response_table
from u3.protocol import ACTIONS, b_score, bundle_packet, compact
from u4.corpus import digest, entry, historical, rows

BASE = ROOT / 'runs/u5'
OUT = ROOT / 'evidence/u5'
SEED = 2026100525
ARMS = ('N', 'R', 'precedent', 'feedback', 'feedback_control', 'scope', 'scope_shuffled')
ARM_NAMES = dict(zip(ARMS, ('没有记忆', '原记忆', '换先例', '全反馈', '全反馈对照', '作用域标签', '打乱标签')))
NOISE_IDS = ('A02', 'A04', 'A06', 'A11', 'A12', 'A16', 'A17', 'A18', 'A20', 'A21')
NARROW = '只针对 do_not_use 里列出的话题；其他偏好照常使用。'
PREFIX = '（程序补充）'


def label(markers):
    day = {'工作日': '工作日', '周末': '休息日'}[markers['day_type']]
    return f'（当时可见：{markers["time_band"]}，{day}，{"在忙" if markers["busy"] else "不忙"}，话题{"提过" if markers["topic_seen"] else "没提"}）'


def new_row(template, identity, text, speaker):
    result = deepcopy(template)
    # Opaque deterministic IDs carry no arm or hidden semantic labels.
    result.update(utterance_id=hashlib.sha256(identity.encode()).hexdigest()[:32],
                  utterance_text=text, speaker=speaker)
    return result


def interventions(person, data, sources, learned, decisions):
    """Preserve every R row/ID except specified texts, and insert paired rows."""
    moments = data['learn']
    trace = {r['moment_id']: r for r in learned['trace']}
    chosen = {d['moment_id']: b_score(d['output'], m, 'S0')
              for d, m in zip(decisions, moments)}
    assert [d['moment_id'] for d in decisions] == [m['id'] for m in moments]
    positions = {r['utterance_id']: i for i, r in enumerate(sources)}
    starts = [positions[trace[m['id']]['context_id']] - bool(m.get('background')) for m in moments]
    assert starts[0] == 0 and starts == sorted(starts)
    arms = {a: [] for a in ARMS}
    arms['R'] = deepcopy(sources)
    audit = []
    rng = random.Random(SEED + int(person) * 100)
    for index, moment in enumerate(moments):
        group = deepcopy(sources[starts[index]:starts[index+1] if index+1 < len(starts) else len(sources)])
        t = trace[moment['id']]
        context = next(r for r in group if r['utterance_id'] == t['context_id'])
        assert context['utterance_text'] == moment['situation']
        pre = group[:1 + bool(moment.get('background'))]
        assert all(r['speaker'] == 'user' for r in pre)
        if moment.get('background'):
            assert pre[0]['utterance_text'] == moment['background']
        score = chosen[moment['id']]
        assert score['valid']
        if score['action'] == 'quiet':
            assert len(group) == len(pre)
        else:
            assert len(group) == len(pre)+2
            assert group[-2]['speaker'] == 'assistant'
            assert group[-2]['utterance_text'] == next(o['text'] for o in moment['options'] if o['id'] == score['action'])
            assert group[-1]['utterance_id'] == t['reaction_id']
            assert group[-1]['utterance_text'] == moment['reactions'][score['action']]
        action = ('ask', 'suggest')[index % 2]
        text = next(o['text'] for o in moment['options'] if o['id'] == action)
        arms['precedent'].extend(deepcopy(pre) + [
            new_row(context, f'{person}/{moment["id"]}/assistant', text, 'assistant'),
            new_row(context, f'{person}/{moment["id"]}/response', '嗯。', 'user')])
        reactions = response_table(moment['mode'], moment['hidden_answer'], moment['markers']['topic_seen'])
        assert reactions == moment['reactions']
        extra, controls = [], []
        for a in ACTIONS:
            if a == score['action']:
                continue
            option = next(o['text'] for o in moment['options'] if o['id'] == a)
            reaction = re.sub(r'答案是[^。]*。', '', reactions[a] or '')
            assert '答案是' not in reaction and moment['hidden_answer'] not in reaction
            body = f'如果选「{option}」，' + ('他不会回应' if a == 'quiet' else f'他会说：「{reaction}」')
            added = new_row(context, f'{person}/{moment["id"]}/supplement/{a}', PREFIX + body, 'program')
            control = deepcopy(added)
            control['utterance_text'] = PREFIX + unrelated(body, index * len(ACTIONS) + ACTIONS.index(a))
            assert len(added['utterance_text']) == len(control['utterance_text'])
            extra.append(added)
            controls.append(control)
        arms['feedback'].extend(deepcopy(group) + extra)
        arms['feedback_control'].extend(deepcopy(group) + controls)
        tagged, shuffled = deepcopy(group), deepcopy(group)
        donor = None
        if score['utility'] < 0:
            assert t['reaction_id'] is not None
            candidates = [m for m in moments if m['id'] != moment['id'] and m['markers'] != moment['markers']]
            donor = rng.choice(candidates)
            real, fake = label(moment['markers']), label(donor['markers'])
            assert len(real) == len(fake) and real != fake
            for r in tagged:
                if r['utterance_id'] == t['reaction_id']:
                    r['utterance_text'] = real + r['utterance_text']
            for r in shuffled:
                if r['utterance_id'] == t['reaction_id']:
                    r['utterance_text'] = fake + r['utterance_text']
        arms['scope'].extend(tagged)
        arms['scope_shuffled'].extend(shuffled)
        audit.append({'moment_id': moment['id'], 'original_action': score['action'],
            'precedent_action': action, 'supplement_count': len(extra),
            'negative_reaction': score['utility'] < 0, 'label_donor': donor['id'] if donor else None,
            'visible_markers': moment['markers'], 'donor_markers': donor['markers'] if donor else None})
    return arms, audit


def narrow_forgetting(old, person_data):
    by_id = {i['id']: i for i in person_data['items']}
    topic = by_id[old['item_id']].get('teaching_domain')
    matched = [i for i in person_data['deleted_ids'] if topic is not None and by_id[i]['teaching_domain'] == topic]
    assert len(matched) <= 1
    request = deepcopy(old['original_request'])
    assert request['messages'][0]['content'].endswith(DIRECTIVE)
    payload = json.loads(request['messages'][1]['content'])
    original_notes = payload['memory']['do_not_use']
    if matched:
        notes = [r for r in original_notes if r['topic'] == TOPICS[matched[0]]]
        assert len(notes) == 1
        payload['memory']['do_not_use'] = notes
        request['messages'][0]['content'] += NARROW
    else:
        del payload['memory']['do_not_use']
        request['messages'][0]['content'] = request['messages'][0]['content'][:-len(DIRECTIVE)]
    # The original serializer is compact: replacing this field changes no other byte.
    assert compact(json.loads(old['messages'][1]['content'])) == old['messages'][1]['content']
    request['messages'][1]['content'] = compact(payload)
    return request, {'id': old['id'], 'item_id': old['item_id'], 'person': old['person'],
                     'teaching_domain': topic, 'deleted': old['deleted'], 'related': bool(matched),
                     'matched_deleted_ids': matched, 'notes_remaining': len(matched)}


def build():
    values, relevance, construction = [], [], {}
    u4 = rows(ROOT / 'evidence/u4/INPUTS.jsonl')
    fmaterial = read(ROOT / 'u3/F1_MATERIALS.json')['people']
    for old in u4:
        if old['domain'] == 'forget' and old['arm'] == 'after':
            request, relation = narrow_forgetting(old, fmaterial[old['person']])
            relevance.append(relation)
            values.append(entry(old['id'].replace('/after/', '/F1b/'), 'forget', old['case'], request,
                {'u4_id': old['id'], 'source': 'evidence/u4/INPUTS.jsonl'},
                person=old['person'], arm='F1b', item_id=old['item_id'], category=old['category'],
                phase=old['phase'], deleted=old['deleted'], related=relation['related']))
    assert Counter((r['deleted'], r['related']) for r in relevance) == {(True, True): 18, (False, False): 64}
    people = read(ROOT / 'evidence/u3/B_MATERIALIZED.json')['people']
    for person, data in people.items():
        learned_path = ROOT / f'evidence/u3/raw/b/S0/person{person}/R/learn/learned.json'
        archive = ROOT / f'runs/u3/b/S0/person{person}/R/learn/state.sqlite'
        learned = read(learned_path)
        before = sha(archive)
        assert before == learned['sha256']
        with Memory.readonly(archive) as memory:
            sources = memory.library.sources()
        assert before == sha(archive)
        original = {d['moment_id']: (d, r, p) for d, r, p in historical(ROOT / f'evidence/u3/raw/b/S0/person{person}/R/test')}
        for d, r, p in original.values():
            assert json.loads(r['messages'][1]['content'])['utterances'] == sources
        learning = [d for d, _, _ in historical(ROOT / f'evidence/u3/raw/b/S0/person{person}/R/learn')]
        arms, audit = interventions(person, data, sources, learned, learning)
        construction[person] = {'archive': archive.relative_to(ROOT).as_posix(), 'archive_sha256': before,
            'source_list_sha256': digest(sources), 'acquisitions': learned['acquisitions'],
            'audit': audit, 'arm_sizes': {a: len(s) for a, s in arms.items()}}
        for arm, utterances in arms.items():
            write(OUT / f'memories/person{person}/{arm}.json', utterances, exclusive=True)
        no_memory = {d['moment_id']: (d, r, p) for d, r, p in historical(ROOT / f'evidence/u3/raw/b/S0/person{person}/N/test')}
        for moment in data['test']:
            messages, schema = bundle_packet(moment, sources, 'S0')
            template = deepcopy(next(iter(original.values()))[1])
            template.update(messages=messages, response_format=schema)
            if moment['id'] in original:
                assert template == original[moment['id']][1]
            for arm in ARMS:
                request = deepcopy(template)
                body = json.loads(request['messages'][1]['content'])
                body['utterances'] = arms[arm]
                request['messages'][1]['content'] = compact(body)
                past = original.get(moment['id']) if arm == 'R' else no_memory.get(moment['id']) if arm == 'N' else None
                if past:
                    assert request == past[1]
                acquired = bool(learned['acquisitions'].get(moment['use_parent']))
                if past:
                    # This batch has zero R acquisitions; no historical score changes.
                    assert acquired == past[0]['acquired_before_test']
                values.append(entry(f'b/{person}/{arm}/{moment["id"]}', 'timing', moment, request,
                    past[2] if past else {'kind': 'program_derived', 'archive_sha256': before,
                        'constructor': 'u3.protocol.bundle_packet(S0), replace utterances only'},
                    past[0] if past else None, person=person, arm=arm, acquired=acquired, format='S0'))
    for old in u4:
        if old['id'] in {'a/' + i for i in NOISE_IDS}:
            assert old['prior_aligned'] is False and old['case']['kind'] != 'ask'
            for replicate in (1, 2, 3):
                values.append(entry(f'noise/{old["case"]["id"]}/{replicate}', 'noise', old['case'],
                    old['original_request'], {'u4_id': old['id'], 'source': 'evidence/u4/INPUTS.jsonl'},
                    kind='u3a', format='S1', replicate=replicate))
    validate(values)
    return values, relevance, construction


def validate(values):
    assert Counter(v['domain'] for v in values) == {'forget': 82, 'timing': 504, 'noise': 30}
    assert len({v['id'] for v in values}) == 616
    assert sum(v['historical'] is not None for v in values) == 135
    for v in values:
        assert v['original_request']['temperature'] == 0
        assert v['messages'] == v['original_request']['messages']
        assert v['response_format'] == v['original_request']['response_format']
        assert digest(v['messages']) == v['messages_sha256']
        assert digest(v['response_format']) == v['schema_sha256']
    for arm in ARMS:
        assert sum(v['domain'] == 'timing' and v['arm'] == arm for v in values) == 72


def prepare():
    target = OUT / 'INPUTS.jsonl'
    if target.exists():
        values = rows(target)
        validate(values)
        return values
    values, relevance, construction = build()
    write(OUT / 'F1B_RELEVANCE.json', relevance, exclusive=True)
    write(OUT / 'CONSTRUCTION.json', construction, exclusive=True)
    with target.open('x', encoding='utf-8', newline='\n') as stream:
        for v in values:
            stream.write(compact(v) + '\n')
    return values
