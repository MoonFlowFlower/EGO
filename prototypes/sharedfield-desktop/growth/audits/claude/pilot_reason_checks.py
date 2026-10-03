"""Revision-2 pilot decision reasons (design v0.6, 10.0): self-position claims,
nearest-tree distance when a reason says "tree in front", imagined-front test,
and near-identical consecutive reasons. Rough keyword checks, not a gate."""
import json
import re
from collections import Counter
from difflib import SequenceMatcher
from common import root, jsonl, cells, reason_of, action_of

EPISODES = ('B_F1_teach_practice_0_a1', 'B_F1_auto_practice_0_a2', 'B_F2_train_practice_0_a1')
POSITION = re.compile(r'I am (?:now )?at \((-?\d+), ?(-?\d+)\)')
FRONT_WORDS = re.compile(r'(in front|front of me|facing|directly|adjacent|next to)', re.I)

base = root() / 'runs/phase1/pilot/episodes'
for name in EPISODES:
    rows = jsonl(base / name / 'trace.jsonl')
    inputs = [r for r in rows if r['type'] == 'input']
    decisions = [r for r in rows if r['type'] == 'decision']
    reasons = [reason_of(d) for d in decisions]
    claims = [POSITION.search(x) for x in reasons]
    nonorigin = sum(1 for m in claims if m and (m.group(1), m.group(2)) != ('0', '0'))
    near = sum(1 for a, b in zip(reasons, reasons[1:]) if SequenceMatcher(None, a, b).ratio() >= 0.9)
    dist, imagined = Counter(), Counter()
    for inp, d, reason in zip(inputs, decisions, reasons):
        if action_of(d) != 'do' or not re.search('tree', reason, re.I) or not FRONT_WORDS.search(reason):
            continue
        obs = json.loads(inp['messages'][1]['content'])['observation']
        grid = cells(obs)
        fx, fy = obs['facing']
        trees = [(c['dx'], c['dy']) for c in obs['cells'] if c['material'] == 'tree']
        if (fx, fy) in trees:
            dist['front_is_tree'] += 1
            continue
        dist[f"nearest_tree={min((abs(x) + abs(y) for x, y in trees), default=None)}"] += 1
        m = POSITION.search(reason)
        if m and (m.group(1), m.group(2)) != ('0', '0'):
            px, py = int(m.group(1)), int(m.group(2))
            imagined['n'] += 1
            imagined['imagined_front_tree'] += grid.get((px + fx, py + fy), {}).get('material') == 'tree'
    print(name, {'decisions': len(decisions), 'position_claims': sum(1 for m in claims if m),
                 'non_origin': nonorigin, 'near_identical_pairs': f'{near}/{len(reasons) - 1}'})
    print('   do + tree-in-front claims by nearest tree distance:', dict(sorted(dist.items())))
    print('   non-origin claims, imagined position + facing hits a tree:', dict(imagined))
