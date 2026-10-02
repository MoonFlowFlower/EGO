from copy import deepcopy
import torch
from evolab.v002.gates import learnability


def passing_rows():
    return [dict(arm=arm, regime=regime, seed=seed,
                 development=dict(survival=.5, ate_good_fraction=.8, survived_first_fraction=.5))
            for arm in ('gru_fixed', 'gru_mb_plastic')
            for regime in ('static', 'drift') for seed in range(3)]


def test_absolute_gates_and_no_drift_survival_requirement():
    rows = passing_rows()
    assert learnability(rows, 3)['passed']
    for row in rows:
        if row['regime'] == 'drift':
            row['development']['survival'] = .01
    assert learnability(rows, 3)['passed']
    rows[0]['development']['ate_good_fraction'] = .79
    assert not learnability(rows, 3)['passed']
    assert not learnability(passing_rows()[:-1], 3)['passed']
    rows = passing_rows()
    rows[-1]['seed'] = rows[-2]['seed']
    assert not learnability(rows, 3)['passed']


def test_constant_float32_fitness_has_zero_diagnostic_std():
    for size in (256, 512):
        values = torch.full((size,), .1, device='cuda')
        assert values.double().std(unbiased=False).item() == 0
