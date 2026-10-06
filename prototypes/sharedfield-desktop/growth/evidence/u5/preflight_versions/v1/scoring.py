"""Original U3 utility/parse functions, prespecified U5 paired contrasts."""
import random
from growthlab.records import ROOT
from u3.common import read
from u3.protocol import b_score, parse, SEED as U3_SEED, BOOTSTRAP_REPLICATES
from u3.statistics import quantile
from u3.f1 import verdict
from u4.scoring import grade as u4_grade
from .corpus import ARMS

ACTIVE = ('ask', 'repeat', 'suggest')


def grade(item, output):
    if item['domain'] != 'timing':
        return u4_grade(item, output)
    case = item['case']
    envelope = (isinstance(output, dict) and set(output) == {'decisions'} and
                isinstance(output['decisions'], list) and len(output['decisions']) == 2)
    opening, use = output['decisions'] if envelope else (None, None)
    primary, probe = b_score(opening, case, 'S0'), parse(use, case['use_probe'], 'S0')
    bonus = int(item['acquired'] and probe['valid'] and probe['action'] == case['use_probe']['target'])
    return {**primary, 'immediate_utility': primary['utility'], 'utility': primary['utility'] + bonus,
        'information_bonus': bonus, 'use_valid': probe['valid'], 'use_action': probe['action'],
        'valid_output': primary['valid'] and probe['valid'], 'signature': [primary['action'], probe['action']],
        'active': primary['action'] in ACTIVE, 'passive': primary['action'] in ('quiet', 'reply'),
        'busy_speaking': case['markers']['busy'] and primary['valid'] and primary['action'] != 'quiet',
        'appropriate_suggest': case['mode'] == 'suggest' and primary['action'] == 'suggest'}


def bootstrap(people, *, replicates=BOOTSTRAP_REPLICATES):
    assert len(people) == 3 and all(len(r) == 24 for r in people.values())
    def contrasts(rows):
        return {
            'phenomenon': sum(r['N']['active'] - r['R']['active'] for r in rows),
            'C5': sum(r['precedent']['active'] - r['N']['active'] for r in rows),
            'C1': sum(r['feedback']['utility'] - r['feedback_control']['utility'] for r in rows),
            'C3': sum(r['scope']['utility'] - r['scope_shuffled']['utility'] for r in rows)}
    point = contrasts([r for group in people.values() for r in group])
    distributions = {k: [] for k in point}
    rng = random.Random(U3_SEED + 900)
    for _ in range(replicates):
        sampled = [rs[rng.randrange(len(rs))] for _, rs in sorted(people.items()) for _ in rs]
        for key, value in contrasts(sampled).items():
            distributions[key].append(value)
    return {k: {'difference_total': v, 'ci95': [quantile(distributions[k], .025), quantile(distributions[k], .975)],
                'threshold_met': quantile(distributions[k], .025) > 0} for k, v in point.items()}


def timing(values):
    totals = {}
    for arm in ARMS:
        records = [r for r in values if r['input']['arm'] == arm]
        scores = [r['score'] for r in records]
        total = sum(s['utility'] for s in scores)
        totals[arm] = {'n': len(scores), 'active': sum(s['active'] for s in scores),
            'passive': sum(s['passive'] for s in scores), 'd5': sum(s['d5'] for s in scores),
            'invalid': sum(not s['valid_output'] for s in scores), 'utility': total,
            'information_bonus': sum(s['information_bonus'] for s in scores),
            'busy_speaking': sum(s['busy_speaking'] for s in scores),
            'busy_n': sum(r['input']['case']['markers']['busy'] for r in records),
            'appropriate_suggest': sum(s['appropriate_suggest'] for s in scores),
            'suggest_n': sum(r['input']['case']['mode'] == 'suggest' for r in records),
            'difference_from_fixed_18': total - 18 if len(scores) == 72 else None}
    complete = len(values) == 504 and all(t['n'] == 72 for t in totals.values())
    gate = not any(t['d5'] for t in totals.values())
    intervals, interpretation = None, 'incomplete_no_conclusion'
    if not gate:
        interpretation = 'D5_stop_all_interpretation_for_this_judge'
    elif complete:
        people = {}
        for person in ('1', '2', '3'):
            selected = [r for r in values if r['input']['person'] == person]
            grid = {a: {r['input']['case']['id']: r['score'] for r in selected if r['input']['arm'] == a} for a in ARMS}
            assert all(set(grid[a]) == set(grid['R']) for a in ARMS)
            order = [m['id'] for m in read(ROOT/'evidence/u3/B_MATERIALIZED.json')['people'][person]['test']]
            people[person] = [{a: grid[a][m] for a in ARMS} for m in order]
        intervals = bootstrap(people)
        phenomenon = intervals['phenomenon']['threshold_met']
        interpretation = 'mechanisms_evaluable' if phenomenon else 'phenomenon_absent_mechanisms_report_only'
        for key in ('C5', 'C1', 'C3'):
            intervals[key]['established'] = intervals[key]['threshold_met'] if phenomenon else None
    return {'complete': complete, 'd5_zero_hard_gate': gate, 'arms': totals,
            'comparisons': intervals, 'interpretation': interpretation, 'fixed_baseline': 18}


def forgetting(values, references):
    pairs = []
    for v in values:
        item = v['input']
        def key(arm):
            return f'f/{item["person"]}/{arm}/{item["item_id"]}/{item["phase"]}'
        pairs.append({**v['score'], 'deleted': item['deleted'], 'category': item['category'],
                      'before_correct': references[key('before')]['score']['correct'],
                      'N_correct': references[key('none')]['score']['correct'],
                      'u4_after_correct': references[key('after')]['score']['correct']})
    deleted, retained = ([p for p in pairs if p['deleted']], [p for p in pairs if not p['deleted']])
    result = verdict(deleted, retained, complete=len(pairs) == 82, bytes_pass=True)
    result['bytes_scope'] = 'Input intervention only; original F1 deletion evidence inherited, no new deletion claim.'
    for name, group in [('deleted', deleted), ('retained', retained)]:
        result[name].update(before_correct=sum(p['before_correct'] for p in group),
            N_correct=sum(p['N_correct'] for p in group), u4_after_correct=sum(p['u4_after_correct'] for p in group))
    result['retained_by_category'] = {c: {'n': sum(p['category'] == c for p in retained),
        'correct': sum(p['correct'] for p in retained if p['category'] == c),
        'before_correct': sum(p['before_correct'] for p in retained if p['category'] == c),
        'u4_after_correct': sum(p['u4_after_correct'] for p in retained if p['category'] == c)} for c in ('P', 'Q', 'W')}
    return result
