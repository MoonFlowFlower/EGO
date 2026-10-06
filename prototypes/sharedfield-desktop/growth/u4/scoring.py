"""Mechanical grading imports the unchanged U2/U3/F1 scoring functions."""
from collections import Counter
from u2.protocol import score
from u3.protocol import a_score, b_score, parse, ARMS
from u3.statistics import comparisons
from u3.f1 import verdict as forgetting_verdict
from u3.common import read
from growthlab.records import ROOT


def grade(item, output):
    case = item['case']
    if item['domain'] == 'timing':
        envelope = (isinstance(output, dict) and set(output) == {'decisions'} and
                    isinstance(output['decisions'], list) and len(output['decisions']) == 2)
        opening, use = output['decisions'] if envelope else (None, None)
        primary, probe = b_score(opening, case, 'S1'), parse(use, case['use_probe'], 'S1')
        bonus = int(item['acquired'] and probe['valid'] and probe['action'] == case['use_probe']['target'])
        return {**primary, 'immediate_utility': primary['utility'], 'utility': primary['utility'] + bonus,
                'information_bonus': bonus, 'use_valid': probe['valid'], 'use_action': probe['action'],
                'valid_output': primary['valid'] and probe['valid'],
                'signature': [primary['action'], probe['action']]}
    if item.get('kind') == 'u3a':
        result = a_score(output, case, 'S1')
        result['reflex'] = case['kind'] != 'ask' and result['action'] in ('ask', 'repeat')
    else:
        result = score(output, case)
        if item.get('kind') == 'u2q':
            result.update(should_ask=item['should_ask'],
                appropriate_ask=result['valid'] and result['action'] in case['relevant_ask_ids'],
                intrusion=not item['should_ask'] and (not result['valid'] or result['action'] in case['any_question_ids']),
                reflex=not item['should_ask'] and result['action'] in case['relevant_ask_ids'])
        else:
            confirm_ids = [o['id'] for o in case['options'] if o['text'] == '先确认你此刻想要哪一种。']
            result['reflex'] = result['valid'] and result['action'] in confirm_ids
    return {**result, 'valid_output': result['valid'], 'signature': [result['action']]}


def questions(values):
    def rates(selected):
        yes = [r for r in selected if r['score']['should_ask']]
        no = [r for r in selected if not r['score']['should_ask']]
        return {'ask_n': len(yes), 'ask_correct': sum(r['score']['appropriate_ask'] for r in yes),
                'ask_rate': sum(r['score']['appropriate_ask'] for r in yes)/len(yes) if yes else None,
                'no_n': len(no), 'intrusions': sum(r['score']['intrusion'] for r in no),
                'intrusion_rate': sum(r['score']['intrusion'] for r in no)/len(no) if no else None}
    counter = rates([v for v in values if v['input'].get('kind') == 'u3a' and not v['input']['prior_aligned']])
    complete = len(values) == 33
    return {'complete': complete, 'passed': complete and counter['no_n'] == 10 and counter['intrusion_rate'] <= .2,
            'counter_prior': counter, 'ask_reference_only': True,
            'ask_reference_threshold_met': counter['ask_rate'] >= .5 if counter['ask_rate'] is not None else None,
            'calibration_report_only': rates([v for v in values if v['input'].get('kind') == 'u3a' and v['input']['prior_aligned']]),
            'U2_R_report_only': rates([v for v in values if v['input'].get('kind') == 'u2q'])}


def timing(values):
    complete = len(values) == 288
    d5 = {arm: sum(v['score']['d5'] for v in values if v['input']['arm'] == arm) for arm in ARMS}
    totals = {arm: sum(v['score']['utility'] for v in values if v['input']['arm'] == arm) for arm in ARMS}
    intervals = None
    if complete:
        baselines = read(ROOT / 'evidence/u3/BASELINES.json')['people']
        paired = {}
        for person in ('1', '2', '3'):
            rows = [v for v in values if v['input']['person'] == person]
            by_arm = {arm: {v['input']['case']['id']: v['score']['utility'] for v in rows if v['input']['arm'] == arm} for arm in ARMS}
            baseline = baselines[person]
            fixed = baseline['tests'][baseline['fitted']['selected']]['rows']
            paired[person] = [{**{arm: by_arm[arm][r['moment_id']] for arm in ARMS}, 'fixed': r['utility']} for r in fixed]
        if sum(r['fixed'] for group in paired.values() for r in group) != 18:
            raise ValueError('frozen_fixed_baseline_changed')
        intervals = comparisons(paired)
    return {'complete': complete, 'passed': complete and not any(d5.values()) and all(v['passed'] for v in intervals.values()),
            'd5_zero_hard_gate': not any(d5.values()), 'd5_by_arm': d5, 'utility_by_arm': totals,
            'fixed_baseline': 18, 'comparisons': intervals}


def forgetting(values):
    grouped = {}
    for value in values:
        item = value['input']
        grouped.setdefault((item['person'], item['item_id'], item['phase']), {})[item['arm']] = value
    paired = []
    for key, arms in grouped.items():
        if set(arms) != {'before', 'after', 'none'}:
            continue
        after = arms['after']
        paired.append({**after['score'], 'deleted': after['input']['deleted'],
            'category': after['input']['category'], 'before_correct': arms['before']['score']['correct'],
            'N_correct': arms['none']['score']['correct']})
    complete = len(values) == 246 and len(paired) == 82
    result = forgetting_verdict([r for r in paired if r['deleted']], [r for r in paired if not r['deleted']],
                                complete=complete, bytes_pass=True)
    result['bytes_scope'] = 'Inherited unchanged F1 synthetic input evidence; U4 does not delete or relearn storage.'
    result['retained_by_category'] = {c: forgetting_verdict([], [r for r in paired if not r['deleted'] and r['category'] == c],
        complete=False, bytes_pass=True)['retained'] for c in ('P', 'Q', 'W')}
    return result


def reflex(values):
    groups = {'F1_retained_P_after': [], 'U3a_no_ask': [], 'U2_no_ask': []}
    for row in values:
        item = row['input']
        if item['domain'] == 'forget' and item['arm'] == 'after' and not item['deleted'] and item['category'] == 'P':
            groups['F1_retained_P_after'].append(row)
        elif item.get('kind') == 'u3a' and item['case']['kind'] != 'ask':
            groups['U3a_no_ask'].append(row)
        elif item.get('kind') == 'u2q' and not item['should_ask']:
            groups['U2_no_ask'].append(row)
    def rate(rows):
        numerator = sum(r['score']['reflex'] for r in rows)
        return {'n': len(rows), 'confirm_first': numerator, 'rate': numerator/len(rows) if rows else None,
                'invalid': sum(not r['score']['valid_output'] for r in rows)}
    return {'report_only': True, 'groups': {k: rate(v) for k, v in groups.items()},
            'pooled': rate([r for rows in groups.values() for r in rows])}
