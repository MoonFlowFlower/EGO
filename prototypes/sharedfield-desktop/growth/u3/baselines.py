"""Experimental comparison policies. Never imported by companion production."""
from .protocol import FEATURES

CHOICES = ('quiet', 'reply', 'ask', 'suggest')


def action(policy, moment):
    if policy['kind'] == 'constant':
        return policy['action']
    if policy['kind'] == 'cue':
        return policy['mapping'][str(moment['markers'][policy['feature']])]
    if policy['kind'] == 'polite':
        return 'reply' if moment['markers']['busy'] or moment['markers']['topic_seen'] else 'ask'
    if policy['kind'] == 'oracle':
        return max(CHOICES, key=lambda x: moment['utilities'][x])
    raise ValueError('unknown_baseline')


def fit(learning):
    policies = {f'always_{a}': {'kind': 'constant', 'action': a} for a in CHOICES}
    for feature in FEATURES:
        mapping = {}
        for value in sorted({str(m['markers'][feature]) for m in learning}):
            matched = [m for m in learning if str(m['markers'][feature]) == value]
            mapping[value] = max(CHOICES, key=lambda a: sum(m['utilities'][a] for m in matched))
        policies['cue_' + feature] = {'kind': 'cue', 'feature': feature, 'mapping': mapping}
    policies['polite'] = {'kind': 'polite'}
    train = {name: sum(m['utilities'][action(p, m)] for m in learning) for name, p in policies.items()}
    # Frozen insertion order resolves ties; no test utilities are accepted here.
    best = max(train, key=train.get)
    return {'policies': policies, 'learning_utilities': train, 'selected': best,
            'single_cue_selected': max((n for n in train if n.startswith('cue_')), key=train.get),
            'tie_order': list(policies), 'fit_scope': 'immediate utility on learning moments only'}


def evaluate(fitted, learning, testing):
    learned = {m['id']: m for m in learning}
    all_policies = {**fitted['policies'], 'oracle': {'kind': 'oracle'}}
    results = {}
    for name, policy in all_policies.items():
        rows = []
        for m in testing:
            selected = action(policy, m)
            parent = learned[m['use_parent']]
            acquired = action(policy, parent) == 'ask' and parent['mode'] == 'ask'
            # Fixed policies get perfect literal readback of any answer they
            # obtained. This gives them no disadvantage on the use subprobe.
            bonus = int(acquired)
            rows.append({'moment_id': m['id'], 'action': selected,
                         'immediate_utility': m['utilities'][selected],
                         'information_bonus': bonus,
                         'utility': m['utilities'][selected]+bonus})
        results[name] = {'rows': rows, 'total': sum(r['utility'] for r in rows)}
    return results
