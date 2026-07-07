from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class Summary:
    mean: float
    ci_low: float
    ci_high: float
    n: int


def bootstrap_summary(values: Iterable[float], *, seed: int = 20260707, resamples: int = 10000) -> Summary:
    arr = np.asarray(list(values), dtype=float)
    if len(arr) == 0:
        return Summary(mean=0.0, ci_low=0.0, ci_high=0.0, n=0)
    rng = np.random.Generator(np.random.PCG64(seed))
    if len(arr) == 1:
        return Summary(mean=float(arr[0]), ci_low=float(arr[0]), ci_high=float(arr[0]), n=1)
    idx = rng.integers(0, len(arr), size=(resamples, len(arr)))
    means = arr[idx].mean(axis=1)
    return Summary(
        mean=float(arr.mean()),
        ci_low=float(np.percentile(means, 2.5)),
        ci_high=float(np.percentile(means, 97.5)),
        n=int(len(arr)),
    )


def mde_80(pair_diffs: Iterable[float], n: int) -> dict:
    arr = np.asarray(list(pair_diffs), dtype=float)
    sigma = float(arr.std(ddof=1)) if len(arr) > 1 else 0.0
    value = float(2.8 * sigma / np.sqrt(n)) if n > 0 else float("inf")
    return {"sigma_pair": sigma, "n": int(n), "mde_80": value, "pass": value <= 0.05}
