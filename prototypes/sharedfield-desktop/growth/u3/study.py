"""Synthetic conversations through the canonical store, isolated fresh tests."""
from copy import deepcopy
import json
import os
from pathlib import Path
import random
import sqlite3

from companion.memory import Memory
from u2.study import unrelated
from .common import read, write, sha, append
from .protocol import (SEED, packet, schema, parse, a_score, b_score, bundle_packet)


def decide(client, case, sources, fmt, context):
    output, meta = client.call(packet(case, sources, fmt), context, schema=schema(case, fmt))
    result = {**context, **parse(output, case, fmt), 'output': output, 'meta': meta}
    append(client.folder / 'decisions.jsonl', result)
    client.parsed(result['valid'])
    return result


def put(memory, text, dialogue, speaker='user', *, occurred_at=None):
    return memory.library.utterance(text, session_id=f'u3:dialogue:{dialogue}', speaker=speaker,
                                    occurred_at=occurred_at or f'2026-09-{dialogue:02}T18:00:00-05:00')


def a_store(path, items):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=False)
    stores = {}
    for item in items:
        dbpath = path / (item['id']+'.sqlite')
        with Memory(dbpath) as memory:
            ids = [put(memory, text, 1) for text in item['teaching']]
        stores[item['id']] = {'path': str(dbpath), 'sha256': sha(dbpath), 'source_ids': ids}
    write(path / 'created.json', {'pid': os.getpid(), 'stores': stores})


def a_test(job, client):
    created = read(Path(job['store_dir']) / 'created.json')
    if created['pid'] == os.getpid():
        raise ValueError('fresh_process_required')
    checks = []
    try:
        for item in job['items']:
            entry = created['stores'][item['id']]
            path = Path(entry['path'])
            before = sha(path)
            if before != entry['sha256']:
                raise ValueError('a_archive_changed')
            with Memory.readonly(path) as memory:
                row = decide(client, item, memory.library.sources(), job['format'], {'item_id': item['id'], 'stage': 'a_test', 'format': job['format']})
            row.update(a_score(row['output'], item, job['format']), kind=item['kind'], prior_aligned=item['prior_aligned'])
            append(client.folder / 'scores.jsonl', row)
            checks.append({'item_id': item['id'], 'before': before, 'after': sha(path), 'unchanged': before == sha(path)})
    finally:
        write(client.folder / 'storage_hash.json', {'checks': checks, 'learning_pid': created['pid'],
              'testing_pid': os.getpid(), 'unchanged': all(c['unchanged'] for c in checks)})
    if not all(c['unchanged'] for c in checks):
        raise ValueError('test_mutated_archive')


def learn(job, client):
    folder = Path(job['folder'])
    path = folder / 'state.sqlite'
    if path.exists():
        raise ValueError('existing_store_no_replay')
    fmt = job['format']
    reactions, acquisitions, trace = [], {}, []
    with Memory(path) as memory:
        for moment in job['person']['learn']:
            if moment.get('background'):
                put(memory, moment['background'], moment['dialogue'], occurred_at=moment['occurred_at'])
            context_id = put(memory, moment['situation'], moment['dialogue'], occurred_at=moment['occurred_at'])
            row = decide(client, moment, memory.library.sources(), fmt,
                         {'moment_id': moment['id'], 'stage': 'b_learn', 'format': fmt, 'persona': job['persona'], 'arm': 'R'})
            score = b_score(row['output'], moment, fmt)
            row.update(score)
            append(folder / 'scores.jsonl', row)
            selected = row['action']
            acquisition = bool(row['valid'] and selected == 'ask' and moment['mode'] == 'ask')
            acquisitions[moment['id']] = acquisition
            response_id = None
            if selected and selected != 'quiet':
                text = next(o['text'] for o in moment['options'] if o['id'] == selected)
                put(memory, text, moment['dialogue'], 'assistant', occurred_at=moment['occurred_at'])
                reaction = moment['reactions'][selected]
                if reaction is not None:
                    response_id = put(memory, reaction, moment['dialogue'], occurred_at=moment['occurred_at'])
                    reactions.append(response_id)
            trace.append({'moment_id': moment['id'], 'context_id': context_id,
                          'reaction_id': response_id, 'acquired': acquisition})
        counts = [{'speaker': s['speaker'], 'characters': len(s['utterance_text']),
                   'utf8_bytes': len(s['utterance_text'].encode())} for s in memory.library.sources()]
    write(folder / 'learned.json', {'pid': os.getpid(), 'format': fmt, 'arm': 'R', 'persona': job['persona'],
          'reaction_ids': reactions, 'acquisitions': acquisitions, 'trace': trace,
          'lengths': counts, 'sha256': sha(path)})


def fork_store(job):
    folder = Path(job['folder'])
    path = folder / 'state.sqlite'
    if path.exists():
        raise ValueError('existing_store_no_replay')
    arm = job['arm']
    original = Path(job['related_store'])
    learned = read(original.parent / 'learned.json')
    if sha(original) != learned['sha256']:
        raise ValueError('related_archive_changed')
    with Memory.readonly(original) as source:
        rows = source.library.sources()
    changed, mapping, lengths = [], [], []
    reaction_ids = learned['reaction_ids']
    texts = {s['utterance_id']: s['utterance_text'] for s in rows}
    shuffled = list(reaction_ids)
    random.Random(SEED+int(job['persona'])*10+(job['format'] == 'S1')).shuffle(shuffled)
    shuffled_text = dict(zip(reaction_ids, (texts[i] for i in shuffled)))
    with Memory(path) as target:
        if arm != 'N':
            for index, row in enumerate(rows):
                text = row['utterance_text']
                if arm == 'I':
                    text = unrelated(text, index)
                elif arm == 'R_SHUFFLED' and row['utterance_id'] in shuffled_text:
                    text = shuffled_text[row['utterance_id']]
                    mapping.append({'destination': row['utterance_id'], 'from': shuffled[reaction_ids.index(row['utterance_id'])]})
                identity = target.library.utterance(text, session_id=row['session_id'],
                    speaker=row['speaker'], occurred_at=row['occurred_at'])
                changed.append(identity)
                lengths.append({'speaker': row['speaker'], 'characters': len(text), 'utf8_bytes': len(text.encode())})
    if arm == 'I' and lengths != learned['lengths']:
        raise ValueError('irrelevant_length_mismatch')
    # Shuffling keeps the acquired response inventory but breaks the local
    # event/response relation; no fresh model call or new answer is inserted.
    acquisitions = learned['acquisitions'] if arm == 'R_SHUFFLED' else {}
    write(folder / 'learned.json', {'pid': os.getpid(), 'arm': arm, 'format': job['format'],
          'persona': job['persona'], 'acquisitions': acquisitions, 'lengths': lengths,
          'matched_lengths': arm != 'I' or lengths == learned['lengths'],
          'shuffle_mapping': mapping, 'sha256': sha(path), 'cloud_calls': 0})


def b_test(job, client):
    path = Path(job['store'])
    learned = read(path.parent / 'learned.json')
    if learned['pid'] == os.getpid():
        raise ValueError('fresh_process_required')
    before = sha(path)
    if before != learned['sha256']:
        raise ValueError('learned_archive_changed')
    try:
        with Memory.readonly(path) as memory:
            sources = memory.library.sources()
            for moment in job['person']['test']:
                messages, envelope = bundle_packet(moment, sources, job['format'])
                context = {'moment_id': moment['id'], 'persona': job['persona'],
                           'format': job['format'], 'arm': job['arm'], 'stage': 'b_test'}
                output, meta = client.call(messages, context, schema=envelope)
                valid_envelope = isinstance(output, dict) and set(output) == {'decisions'} and isinstance(output['decisions'], list) and len(output['decisions']) == 2
                opening, use = output['decisions'] if valid_envelope else (None, None)
                primary = b_score(opening, moment, job['format'])
                used = parse(use, moment['use_probe'], job['format'])
                acquired = bool(learned['acquisitions'].get(moment['use_parent']))
                use_correct = used['valid'] and used['action'] == moment['use_probe']['target']
                bonus = int(acquired and use_correct)
                row = {**context, **primary, 'output': output, 'meta': meta,
                       'immediate_utility': primary['utility'], 'information_bonus': bonus,
                       'utility': primary['utility']+bonus, 'use_valid': used['valid'],
                       'acquired_before_test': acquired, 'use_correct': use_correct,
                       'use_parent': moment['use_parent'], 'use_target': moment['use_probe']['target'],
                       'mode': moment['mode'], 'markers': moment['markers']}
                append(client.folder / 'decisions.jsonl', row)
                client.parsed(primary['valid'] and used['valid'])
    finally:
        after = sha(path)
        write(client.folder / 'storage_hash.json', {'before': before, 'after': after,
              'unchanged': before == after, 'learning_pid': learned['pid'], 'testing_pid': os.getpid(),
              'sqlite_mode': 'ro+query_only'})
        if before != after:
            raise ValueError('test_mutated_archive')
