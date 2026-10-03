"""Revision-3 G0p (design v0.6, 10.0): reproduce sampling from the recorded seed,
rescore from raw calls with an independent oracle, and classify front errors as
the agent's own cell (SELF) or other."""
import json
import random
from collections import Counter
from pathlib import Path
from common import root, jsonl, cells, episode_name

R = root()
run = R / 'runs/phase1/revision3/g0p'
manifest = json.loads((run / 'manifest.json').read_text(encoding='utf-8'))
completed = json.loads((R / 'runs/phase1/pilot/status.json').read_text(encoding='utf-8'))['completed']
rng = random.Random(manifest['sampling_seed'])
sampled = []
for summary in completed:
    path = Path(summary.replace(chr(92), '/'))
    path = path if path.is_absolute() else R / path
    entries = [(i, row) for i, row in enumerate(jsonl(path.parent / 'trace.jsonl'), 1) if row['type'] == 'input']
    sampled += [(path.parent.name, entries[k][0]) for k in sorted(rng.sample(range(len(entries)), 10))]
print('sampling reproduced:', sampled == [(episode_name(c['source']), c['line']) for c in manifest['cases']])


def oracle(obs):
    f = cells(obs)[tuple(obs['facing'])]
    state = f.get('visible_state') or {}
    return {'material': f['material'], 'entity': f['entity'] or 'none',
            'plant_ripe': state.get('plant_ripe'), 'arrow_direction': state.get('arrow_direction', '')}


cases = {c['id']: c for c in manifest['cases']}
table = Counter()
for call in jsonl(run / 'calls.jsonl'):
    if call['type'] != 'response':
        continue
    case, fmt = call['context']['id'].rsplit('_', 1)
    obs = cases[case]['observation']
    front = json.loads(call['output'])['front']
    me = cells(obs)[(0, 0)]
    entity = None if front['entity'] == 'none' else front['entity']
    if front == oracle(obs): tag = 'OK'
    elif (front['material'], entity) == (me['material'], me['entity']): tag = 'SELF'
    else: tag = 'OTHER'
    table[(fmt, tag)] += 1
print(dict(sorted(table.items())))
same = sum(cells(c['observation'])[tuple(c['observation']['facing'])]['material']
           == cells(c['observation'])[(0, 0)]['material'] for c in manifest['cases'])
print('cases whose front material equals the underfoot material:', f'{same}/{len(cases)}')
