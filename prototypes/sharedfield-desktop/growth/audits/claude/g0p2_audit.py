"""G0p2 (design v0.7, 10.0): QA rescore and the spurious arrow_direction check;
live front_seen errors versus the latest change event's front.after; positive
"tree in front" claims; knowing `do` on bare ground."""
import json
import re
from collections import Counter
from common import root, jsonl, cells

R = root()
run = R / 'runs/phase1/revision3_round2/g0p2'
manifest = json.loads((run / 'manifest.json').read_text(encoding='utf-8'))
cases = {c['id']: c for c in manifest['cases']}
NAMES = {(1, 0): 'right', (-1, 0): 'left', (0, 1): 'down', (0, -1): 'up'}


def oracle(obs):
    f = cells(obs)[tuple(obs['facing'])]
    state = f.get('visible_state') or {}
    return {'material': f['material'], 'entity': f['entity'] or 'none',
            'plant_ripe': state.get('plant_ripe'), 'arrow_direction': state.get('arrow_direction', '')}


table = Counter()
for call in jsonl(run / 'calls.jsonl'):
    if call['type'] != 'response' or call['context'].get('stage') != 'qa':
        continue
    case, fmt = call['context']['id'].rsplit('_', 1)
    obs = cases[case]['observation']
    front = json.loads(call['output'])['front']
    ok = front == oracle(obs)
    table[(fmt, 'n')] += 1
    table[(fmt, 'front_ok')] += ok
    if not ok and front['arrow_direction'] == NAMES[tuple(obs['facing'])]:
        table[(fmt, 'arrow_direction_equals_facing')] += 1
print('QA:', dict(sorted(table.items())))

POSITIVE = re.compile(r'(facing (a|the) tree|tree (is )?(directly )?in front|chop the tree in front|front is (a )?tree)', re.I)
NEGATIVE = re.compile(r"(no tree|not a tree|isn't a tree|without a tree)", re.I)
live = Counter()
for episode in sorted((run / 'episodes').iterdir()):
    current = assessment = None
    for row in jsonl(episode / 'trace.jsonl'):
        if row['type'] == 'input':
            current = json.loads(row['messages'][1]['content'])
        elif row['type'] == 'front_assessment':
            assessment = row
            truth = row['expected']['material']
            changed = [c for c in current.get('previous_changes', []) if c['effects'].get('front')]
            latest = changed[-1]['effects']['front']['after']['material'] if changed else None
            try:
                seen = json.loads(row['output'])['front_seen']['material']
            except (ValueError, KeyError, TypeError):
                seen = None
            trap = latest is not None and latest != truth
            live['n'] += 1
            live['trap'] += trap
            live['error'] += seen != truth
            live['error_in_trap_and_copied'] += seen != truth and trap and seen == latest
        elif row['type'] == 'decision':
            out = json.loads(assessment['output'])
            truth = assessment['expected']
            live['valid'] += 1
            reason = out.get('reason', '')
            if POSITIVE.search(reason) and not NEGATIVE.search(reason):
                live['tree_claims'] += 1
                live['tree_claims_false'] += truth['material'] != 'tree'
            if (out.get('action') == 'do' and assessment['correct'] and truth['entity'] == 'none'
                    and truth['material'] in ('grass', 'sand', 'path')):
                live['knowing_do_on_bare_ground'] += 1
print('live:', dict(live))
