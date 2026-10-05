"""Item-level author audit, not runtime behavior rules or a model grader.

The pairs name potential answer leakage or contradictory authored facts. They
constrain only assignment to three synthetic people, never eligibility/scores.
"""
import random
from u2.protocol import SEED

# Reviewed against all 70 inherited and all 48 supplemental candidates before
# any main learning/testing. Different people have physically separate stores.
PAIRS = [
    ('Q03', 'W18', '耳机/外放：隐藏答案与本人入耳式约定相矛盾'),
    ('Q08', 'Q58', '住宿必须分开：另一题的回答会透露同类条件'),
    ('Q15', 'W30', '手部受伤：另一条教学提前提供关键身体限制'),
    ('Q15', 'W42', '手术恢复限制：避免用另一身体限制代替待问事实'),
    ('Q44', 'Q70', '高处住宿：两个可能回答给出相近的个人取向'),
    ('Q50', 'Q72', '温水：两个隐藏答案同义'),
    ('Q51', 'W41', '自己的床铺无香：直接同义答案，即使晚于提问也会污染后测'),
    ('Q52', 'W28', '用餐室内：另一约定可绕过尚未知的露天限制'),
    ('Q55', 'W03', '食物刺激性：避免怕辣成为不吃生蒜的替代线索'),
    ('Q59', 'P02', '保留不完美：避免手作痕迹偏好泄漏保留瑕疵影像的答案'),
    ('Q59', 'P71', '保留修改痕迹：可迁移为不删坏照片，须分人'),
    ('Q60', 'P63', '手接触光滑表面：同一触感偏好可提前提供答案'),
    ('Q60', 'W30', '手伤：避免受伤限制替代手掌触感偏好'),
    ('Q71', 'W09', '调饮加奶：另有本人口味，避免未知答案与已有约定混淆'),
    ('P01', 'P53', '预知结局与悬而未决结尾同时教学有冲突'),
    ('P03', 'P30', '独处人声与独处日常轻声适用范围容易冲突'),
    ('P03', 'W08', '专注杂响与独自读书安静有重叠'),
    ('P51', 'W01', '日常放凉与恢复期温热食物有重叠'),
    ('P52', 'W26', '睡前紧张剧情与睡前一小时避刺激有冲突'),
    ('P72', 'P30', '杂活听人声与独处轻声适用范围容易重叠'),
]


def conflicting_pairs(items):
    indexed = {i['id']: i for i in items}
    pairs = {(min(a, b), max(a, b)): reason for a, b, reason in PAIRS if a in indexed and b in indexed}
    # Frozen times are 09:00..16:00 on one day. A persistent busy condition
    # must not silently turn another Q's predeclared "ask now" into an intrusion.
    busy_ends = {'Q65': 14, 'Q66': 17, 'Q67': 16, 'Q68': 15}
    for busy, end in busy_ends.items():
        if busy not in indexed:
            continue
        for q in items:
            if q.get('should_ask') is True and 8 + q['question_dialogue'] < end:
                pairs[(min(busy, q['id']), max(busy, q['id']))] = '持续忙碌与另一题的提问时机重叠，不能同人'
    return [{'a': a, 'b': b, 'reason': reason} for (a, b), reason in sorted(pairs.items())]


def stratum(item):
    return item['category'] + (str(item['should_ask']) if item['category'] == 'Q' else str(item['applicable']) if item['category'] == 'W' else '')


def assign(items):
    """Deterministic backtracking; retain every selected item exactly once.

    Balance P, W halves, and Q total across people. Persistent busy Q may force
    Q subtypes to different people; global Q halves remain the frozen draw.
    No model outcome is read by this function.
    """
    indexed = {i['id']: i for i in items}
    pairs = conflicting_pairs(items)
    neighbors = {i: set() for i in indexed}
    for p in pairs:
        neighbors[p['a']].add(p['b']); neighbors[p['b']].add(p['a'])
    rng = random.Random(SEED + 2)
    order = sorted(indexed); rng.shuffle(order)
    priority = {i: n for n, i in enumerate(order)}
    assigned, people = {}, {str(p): [] for p in range(1, 4)}
    # Category capacities are fixed independently of conflicts/outcomes.
    counts = {c: sum(i['category'] == c for i in items) for c in ('P', 'Q', 'W')}
    maximum = {c: (counts[c] + 2) // 3 for c in counts}
    nodes = 0
    def search():
        nonlocal nodes
        nodes += 1
        if nodes > 300000:
            raise ValueError('assignment_search_limit')
        if len(assigned) == len(items):
            return True
        pending = [i for i in indexed if i not in assigned]
        identity = max(pending, key=lambda i: (len({assigned[n] for n in neighbors[i] if n in assigned}), len(neighbors[i]), -priority[i]))
        item = indexed[identity]; category = item['category']
        choices = sorted(people, key=lambda p: (sum(stratum(indexed[i]) == stratum(item) for i in people[p]), len(people[p]), p))
        for person in choices:
            if any(assigned.get(n) == person for n in neighbors[identity]):
                continue
            if sum(indexed[i]['category'] == category for i in people[person]) >= maximum[category]:
                continue
            assigned[identity] = person; people[person].append(identity)
            if search(): return True
            people[person].pop(); del assigned[identity]
        return False
    if not search():
        raise ValueError('cannot_assemble_three_people_without_leakage')
    # Preserve selected order within each category, as in the original study.
    result = {p: [i for i in items if assigned[i['id']] == p] for p in people}
    return result, pairs


def audit(people):
    items = [i for values in people.values() for i in values]
    assigned = {i['id']: p for p, values in people.items() for i in values}
    pairs = conflicting_pairs(items)
    failures = [p for p in pairs if assigned[p['a']] == assigned[p['b']]]
    rows = []
    for person, group in people.items():
        for q in [i for i in group if i['category'] == 'Q']:
            matches = []
            for other in group:
                if other['id'] == q['id']: continue
                texts = [m['text'] for s in other['teaching'] for m in s['messages']]
                texts += [other.get('hidden_answer', '')]
                if any(q['hidden_answer'] in text for text in texts): matches.append(other['id'])
            rows.append({'persona': person, 'Q_id': q['id'], 'hidden_answer': q['hidden_answer'],
                         'other_ids_reviewed': [i['id'] for i in group if i['id'] != q['id']],
                         'exact_answer_matches': matches,
                         'semantic_conflicts_same_person': [p for p in failures if q['id'] in (p['a'], p['b'])]})
    return {'passed': not failures and not any(r['exact_answer_matches'] for r in rows),
            'method': 'Pre-main Codex author semantic review plus exact-text check. All other teaching and possible Q answers are checked through all eight dialogues, including evidence after the question but before testing. Not a model judge and not a score.',
            'pairs_separated': pairs, 'unseparated_pairs': failures, 'Q_rows': rows,
            'limit': 'Manual semantic review can miss distant implications; lexical matching alone is not claimed to prove independence.'}
