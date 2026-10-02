from dataclasses import dataclass, replace, asdict
from ..config import Config as LegacyConfig, SEED_DOMAINS as LEGACY_DOMAINS


@dataclass(frozen=True)
class Config(LegacyConfig):
    view_size: int = 5
    initial_energy: float = .6

    @property
    def input_size(self):
        return self.view_size ** 2 * 5 + 9


# Purpose domains are disjoint from 001A, including pilot initialization/mutation.
DOMAINS = dict(LEGACY_DOMAINS, f1=410000, pilot_train=420000,
               pilot_dev=430000, formal_train=440000, formal_dev=450000,
               holdout_002a=940000, f0=460000)


def ladder(level, poison_cost):
    assert level in range(4)
    c = Config(move_cost=0., poison_cost=poison_cost)
    if level >= 1:
        c = replace(c, view_size=7)
    if level >= 2:
        c = replace(c, sigma=.05, population=512)
    if level >= 3:
        c = replace(c, initial_energy=1.)
    return c
