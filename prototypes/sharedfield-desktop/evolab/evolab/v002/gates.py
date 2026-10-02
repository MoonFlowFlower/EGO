"""Absolute engineering criteria; no between-arm contrast used for selection."""


def learnability(rows, seeds):
    groups = []
    for arm in ('gru_fixed', 'gru_mb_plastic'):
        for regime in ('static', 'drift'):
            subset = [r for r in rows if r['arm'] == arm and r['regime'] == regime]
            complete = len(subset) == seeds and len({r['seed'] for r in subset}) == seeds
            avg = {k: sum(r['development'][k] for r in subset)/len(subset) if subset else 0.
                   for k in ('survival', 'ate_good_fraction', 'survived_first_fraction')}
            checks = dict(complete=complete, ate_good=avg['ate_good_fraction'] >= .8)
            if regime == 'static':
                checks['survival'] = avg['survival'] >= .5
            else:
                checks['survived_first'] = avg['survived_first_fraction'] >= .5
            groups.append(dict(arm=arm, regime=regime, mean=avg, checks=checks, passed=all(checks.values())))
    return dict(groups=groups, passed=all(g['passed'] for g in groups))
