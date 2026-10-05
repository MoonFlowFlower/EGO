"""Pure selection, shared by the offline regression and frozen second round."""
import random
from u2.protocol import SEED


def qualify(items, rows):
    kept, excluded = [], []
    for item in items:
        reasons = []
        prior = rows.get((item['id'], 'prior'))
        ceiling = rows.get((item['id'], 'ceiling'))
        if item['category'] != 'W':
            if not prior or not all(s['valid'] for s in prior['scores']):
                reasons.append('prior_missing_or_invalid')
            elif any(s['correct'] for s in prior['scores']):
                reasons.append('prior_already_target')
        if not ceiling or not all(s['valid'] and s['correct'] for s in ceiling['scores']):
            reasons.append('ceiling_missing_invalid_or_wrong')
        if reasons:
            excluded.append({'id': item['id'], 'reasons': reasons})
        else:
            kept.append(item)
    return kept, excluded


def draw(items):
    if len({i['id'] for i in items}) != len(items):
        raise ValueError('duplicate_candidate_id')
    rng = random.Random(SEED)
    selected, counts = [], {}
    for category in ('P', 'Q', 'W'):
        pool = sorted((i for i in items if i['category'] == category), key=lambda i: i['id'])
        rng.shuffle(pool)
        if category == 'P':
            selected.extend(pool[:24])
            counts['P'] = len(pool)
        else:
            key = 'should_ask' if category == 'Q' else 'applicable'
            yes, no = [i for i in pool if i[key]], [i for i in pool if not i[key]]
            counts[category] = {'yes': len(yes), 'no': len(no), 'total': len(pool)}
            n = min(12, len(yes), len(no))
            for a, b in zip(yes[:n], no[:n]):
                selected.extend([a, b])
    enough = counts['P'] >= 12 and all(min(counts[c]['yes'], counts[c]['no']) >= 6 for c in ('Q', 'W'))
    return {'counts': counts, 'passed': enough,
            'selected_ids': [i['id'] for i in selected] if enough else []}
