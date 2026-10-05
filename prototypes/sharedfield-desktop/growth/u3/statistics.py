"""Paired, persona-stratified bootstrap with precommitted seed and quantiles."""
import random
from .protocol import SEED, BOOTSTRAP_REPLICATES


def quantile(values, q):
    values = sorted(values)
    position = (len(values)-1)*q
    i = int(position)
    fraction = position-i
    return values[i]*(1-fraction)+values[min(i+1, len(values)-1)]*fraction


def comparisons(people, *, replicates=BOOTSTRAP_REPLICATES):
    # Each row refers to the SAME held-out moment across all arms/baseline.
    # The I/N maximum is recomputed within each resample, rather than treating
    # a winner picked on observed tests as if it were preselected.
    def contrasts(rows):
        sums = {arm: sum(r[arm] for r in rows) for arm in ('R', 'I', 'N', 'R_SHUFFLED', 'fixed')}
        return {'H1': sums['R']-sums['fixed'],
                'H2_controls': sums['R']-max(sums['I'], sums['N']),
                'H2_shuffled': sums['R']-sums['R_SHUFFLED']}
    all_rows = [r for rows in people.values() for r in rows]
    if len(people) != 3 or any(len(rows) != 24 for rows in people.values()):
        raise ValueError('incomplete_paired_test_grid')
    point = contrasts(all_rows)
    distributions = {key: [] for key in point}
    rng = random.Random(SEED+900)
    for _ in range(replicates):
        sampled = [rows[rng.randrange(len(rows))] for _, rows in sorted(people.items()) for _ in rows]
        for key, value in contrasts(sampled).items():
            distributions[key].append(value)
    return {key: {'difference_total': value, 'ci95': [quantile(distributions[key], .025),
                quantile(distributions[key], .975)], 'passed': quantile(distributions[key], .025) > 0}
            for key, value in point.items()}
