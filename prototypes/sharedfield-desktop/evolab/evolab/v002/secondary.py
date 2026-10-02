"""Descriptive censored recovery estimates. Never used by W/L/V or H1-H3."""
from collections import defaultdict
from fractions import Fraction


def recovery_km(durations, observed):
    """Product-limit median; tied observed events precede removal of censors.

    Formula reference: https://itl.nist.gov/div898/handbook/apr/section2/apr215.htm
    Mortality and new switches can be informative censoring, so this is only
    descriptive, not an estimate of counterfactual recovery after death.
    """
    if len(durations) != len(observed):
        raise ValueError('Duration/event lengths differ')
    groups = defaultdict(lambda: [0, 0])
    for time, event in zip(durations, observed):
        if time < 0:
            raise ValueError('Recovery duration cannot be negative')
        groups[time][0 if event else 1] += 1
    n = len(durations)
    risk = n
    survival = Fraction(1)
    median = None
    curve = []
    for time, (events, censored) in sorted(groups.items()):
        survival *= Fraction(risk-events, risk)
        curve.append(dict(time=time, at_risk=risk, recovered=events,
                          censored=censored, not_yet_recovered=float(survival)))
        if median is None and survival <= Fraction(1, 2):
            median = time
        risk -= events+censored
    return dict(switches=n, recovered=sum(bool(x) for x in observed),
                censored=n-sum(bool(x) for x in observed),
                censored_fraction=(n-sum(bool(x) for x in observed))/n if n else None,
                km_median_steps=median,
                median_status='no_switches' if not n else ('reached' if median is not None else 'not_reached'),
                curve=curve)
