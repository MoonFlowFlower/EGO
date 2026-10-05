"""Deterministic prior-only branch selection; never takes treatment results."""
from copy import deepcopy
import random

from .baselines import fit
from .materials import materialize_moment
from .protocol import SEED, FEATURES


def prior_agrees(kind, selected):
    return selected == 'ask' if kind == 'ask' else selected in ('quiet', 'reply')


def a_materialize(candidates, priors):
    if set(priors) != {c['id'] for c in candidates}:
        raise ValueError('incomplete_a_prior')
    # Keep 12 ask / 6 already-known / 6 continuing-limit items exactly.
    # Of those valid allocations prefer roughly 1/3 prior agreement. This is
    # calibration, not a result-dependent test comparison.
    order = list(candidates)
    random.Random(SEED).shuffle(order)
    states = {(0, 0, 0, 0): []}
    for item in order:
        next_states = {}
        selected = priors[item['id']]
        for counts, path in states.items():
            for k, kind in enumerate(('ask', 'known', 'restriction')):
                nums = list(counts)
                nums[k] += 1
                nums[3] += int(prior_agrees(kind, selected))
                if nums[k] <= (12, 6, 6)[k]:
                    next_states.setdefault(tuple(nums), path+[kind])
        states = next_states
    possible = [s for s in states if s[:3] == (12, 6, 6) and 0 < s[3] < 24]
    if not possible:
        raise ValueError('no_mixed_prior_a_allocation')
    best = min(possible, key=lambda s: (abs(s[3]-8), s[3]))
    allocation = dict(zip((c['id'] for c in order), states[best]))
    selected = []
    for candidate in candidates:
        item = deepcopy(candidate)
        kind = allocation[item['id']]
        item.update(item.pop('variants')[kind])
        item.update(kind=kind, prior_action=priors[item['id']],
                    prior_aligned=prior_agrees(kind, priors[item['id']]))
        selected.append(item)
    return selected


def a_screen(items, prior_rows, ceiling_rows, *, aligned_policy):
    if aligned_policy not in ('retain_calibration', 'exclude_all_correct'):
        raise ValueError('screen_policy_not_resolved')
    kept, excluded = [], []
    for item in items:
        p, c = prior_rows.get(item['id']), ceiling_rows.get(item['id'])
        reasons = []
        if not p or not c or not p['valid'] or not c['valid']:
            reasons.append('missing_or_invalid_screen_decision')
        else:
            prior_correct = prior_agrees(item['kind'], p['action'])
            ceiling_correct = prior_agrees(item['kind'], c['action'])
            if prior_correct and not (aligned_policy == 'retain_calibration' and item['prior_aligned']):
                reasons.append('no_memory_already_correct')
            if aligned_policy == 'retain_calibration' and item['prior_aligned'] and not prior_correct:
                reasons.append('calibration_prior_not_reconfirmed')
            if not ceiling_correct:
                reasons.append('explicit_information_ceiling_wrong')
        if reasons:
            excluded.append({'item_id': item['id'], 'reasons': reasons})
        else:
            kept.append(item)
    # Draw the counter-prior layer independently. Calibration never supplies
    # its sample minimum, displaces its items, or rescues its gate.
    rng = random.Random(SEED+1)
    contrary = [i for i in kept if not i['prior_aligned']]
    calibration = [i for i in kept if i['prior_aligned']]
    yes = [i for i in contrary if i['kind'] == 'ask']
    known = [i for i in contrary if i['kind'] == 'known']
    limits = [i for i in contrary if i['kind'] == 'restriction']
    for values in (yes, known, limits):
        rng.shuffle(values)
    half = min(len(yes), len(known)+len(limits), 12)
    enough = half >= 6
    no = []
    # Alternate the two no-question kinds while available. A scarcity of one
    # kind does not invent a stricter minimum than six per ask/no-ask half.
    for index in range(max(len(known), len(limits))):
        for values in (known, limits):
            if index < len(values):
                no.append(values[index])
    counter_picked = yes[:half]+no[:half] if enough else []
    random.Random(SEED+2).shuffle(calibration)
    picked = counter_picked+calibration
    def counts(values):
        return {kind: sum(i['kind'] == kind for i in values) for kind in ('ask', 'known', 'restriction')}
    return {'eligible_ids': [i['id'] for i in kept], 'excluded': excluded,
            'selected_ids': sorted(i['id'] for i in picked), 'passed': enough,
            'counts': counts(picked), 'criterion_population': 'counter_prior_only',
            'strata': {'counter_prior': {'eligible_ids': [i['id'] for i in contrary],
                        'available_counts': counts(contrary), 'selected_ids': sorted(i['id'] for i in counter_picked),
                        'counts': counts(counter_picked), 'evaluable': enough},
                       'calibration': {'eligible_ids': sorted(i['id'] for i in calibration),
                        'selected_ids': sorted(i['id'] for i in calibration), 'counts': counts(calibration),
                        'report_only': True}},
            'aligned_policy': aligned_policy,
            'on_shortfall': 'U3a not evaluable; no replacement; U3b runs both S0 and S1'}


def b_materialize(people, priors):
    result = {}
    for person, candidates in people.items():
        rng = random.Random(SEED + int(person)*100)
        answer = None
        # Only calibration choices and prewritten branches are inputs. Every
        # accepted person has 3/8 prior-consistent and 5/8 contrary cells.
        for attempt in range(50000):
            cells = rng.sample(candidates, 8)
            counts = ((3, 2, 3), (3, 3, 2), (2, 3, 3))[attempt % 3]
            modes = ['ask']*counts[0] + ['suggest']*counts[1] + ['hold']*counts[2]
            rng.shuffle(modes)
            agreement = []
            for cell, mode in zip(cells, modes):
                prior = priors.get(f'{person}:{cell["id"]}')
                if prior is None:
                    raise ValueError('incomplete_b_prior')
                optima = ('quiet', 'reply') if mode == 'hold' else (mode,)
                agreement.append(prior in optima)
            if sum(agreement) != 3:
                continue
            if any(len({str(c['markers'][f]) for c in cells}) != 2 for f in FEATURES):
                continue
            slots = [('工作日', '早上'), ('工作日', '晚上'), ('周末', '早上'), ('周末', '晚上')]
            if any(sum((c['markers']['day_type'], c['markers']['time_band']) == slot for c in cells) != 2 for slot in slots):
                continue
            rules = {c['id']: mode for c, mode in zip(cells, modes)}
            learning = []
            for week in range(2):
                for slot_index, slot in enumerate(slots):
                    # Two mornings/evenings on weekdays and weekends each;
                    # actual source timestamps agree with the visible markers.
                    day = (1 if slot[0] == '工作日' else 5) + week*7
                    hour = 8 if slot[1] == '早上' else 20
                    for repetition in (week*2, week*2+1):
                        for cell in cells:
                            if (cell['markers']['day_type'], cell['markers']['time_band']) != slot:
                                continue
                            m = materialize_moment(cell['learn'][repetition], rules[cell['id']])
                            m['dialogue'] = week*4+slot_index+1
                            m['occurred_at'] = f'2026-09-{day:02}T{hour:02}:00:00-05:00'
                            learning.append(m)
            fitted = fit(learning)
            upper = sum(max(m['utilities'][a] for a in ('quiet', 'reply', 'ask', 'suggest')) for m in learning)
            if upper <= fitted['learning_utilities'][fitted['selected']]:
                continue
            testing = [materialize_moment(c['test'][r], rules[c['id']]) for r in range(3) for c in cells]
            for m in testing:
                cell = next(c for c in cells if c['id'] == m['cell_id'])
                repetition = int(m['id'].rsplit('-', 1)[1])
                parent = cell['learn'][repetition]
                m['use_parent'] = parent['id']
                m['use_probe'] = {
                    'id': m['id']+':use',
                    'situation': f'另一个独立的使用局面：现在要按之前的准备信息填写{parent["need"]}，请选已获知的答案；没有获知就选不知道。',
                    'options': [{'id': f'answer{n}', 'text': v} for n, v in enumerate(parent['answers'])] + [{'id': 'unknown', 'text': '不知道，不能填。'}],
                    'target': 'answer'+str(parent['answers'].index(parent['hidden_answer'])),
                }
            answer = {'rules': rules, 'prior_alignment': dict(zip((c['id'] for c in cells), agreement)),
                      'aligned_cells': 3, 'contrary_cells': 5, 'selection_attempt': attempt+1,
                      'learn': learning, 'test': testing, 'fitted_baselines': fitted}
            break
        if answer is None:
            raise ValueError('no_valid_prior_calibrated_persona')
        result[person] = answer
    return result
