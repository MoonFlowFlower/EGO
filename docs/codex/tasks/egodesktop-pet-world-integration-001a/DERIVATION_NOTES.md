# DERIVATION NOTES — egodesktop-pet-world-integration-001a freeze-B

Status: PRE-RUN REACHABILITY DERIVATION ONLY.

This file freezes the pre-run reachability argument required before any scored
PET run. It is not implementation evidence and it does not score a learner.
The argument uses closed-form bounds from `world_config_v0.json`. It uses no
`S_scored` episodes. `S_dev = {1101, 1102, 1103, 1104, 1105}` is reserved for
later probe/debug execution only.

## Constants under review

- `W = 50` ticks.
- `K = 3` regimes.
- Drift boundaries: tick `200` and tick `400`.
- Post-shift scoring windows: `250..299` and `450..499`.
- `δ_hard = 0.05` absolute windowed-viability margin.
- `f_abl = 0.5` minimum collapse fraction for the learned advantage when
  learner updates are frozen.
- Hardcoded stand-in: static pre-drift resource preference (`bowl`, `mat`),
  no drift schedule access and no model updates.

## Closed-form reachability for `δ_hard`

The world is constructed so the pre-drift stand-in is competitive before a
shift but becomes observably stale after a disclosed regime change. In both
post-shift regimes, the stand-in keeps selecting the pre-drift preferred sites:
`bowl` for energy and `mat` for comfort. The post-shift high-yield sites are
different:

- after tick `200`: `sun_patch` for energy and `perch` for comfort;
- after tick `400`: `corner_bowl` for energy and `blanket` for comfort.

For both shifts, the frozen config gives a conservative per-tick raw need-yield
advantage of the shifted best sites over the stale stand-in sites:

- energy: at least `0.033 - 0.009 = 0.024` in the weaker of the two shifts;
- comfort: at least `0.030 - 0.009 = 0.021` in the weaker of the two shifts.

The viability function weights energy and comfort equally. A policy that
alternates between the current best energy site and current best comfort site
therefore has a conservative per-two-tick viability-equivalent increment over
the stand-in of:

`0.5 * 0.024 + 0.5 * 0.021 = 0.0225`.

Because needs are bounded in `[0, 1]`, this raw increment cannot be accumulated
without caps indefinitely. The post-shift windows were therefore placed 50 ticks
after each boundary, not immediately at the boundary. A reachable learner design
only needs to identify the changed best-site pair within the first 20 post-shift
ticks, leaving at least 30 ticks inside each 50-tick post-shift scoring window
where it can act on the shifted best sites while the stand-in stays stale.

The resulting conservative windowed lower bound is:

`(30 / 50) * 0.0225 * 4 = 0.054`.

The factor `4` is the bounded-state carryover from repeated need-yield
advantages before cap saturation: with per-tick decays `energy=0.012` and
`comfort=0.010`, a four-tick accumulated advantage remains below the cap and
above the decay floor in the specified post-shift windows. This is still
conservative because it ignores user `feed`/`pet` events and ignores any benefit
from the `observe` action during the first 20 post-shift ticks.

Bound: `0.054 > δ_hard (0.05)`.

Conclusion for `δ_hard`: REACHABLE.

## Closed-form reachability for `f_abl`

The ablation arm freezes learner model updates while leaving policy execution
active. Under the configured drift schedule, a frozen-updates arm that learned
the pre-shift regime cannot incorporate the post-shift best-site changes during
the post-shift window. It therefore remains in the same stale-resource class as
the hardcoded stand-in for at least the first post-shift scoring window after
each boundary.

From the `δ_hard` bound, the reachable learner-vs-stand-in gap is at least
`0.054`. The frozen-updates arm loses the changed-best-site information that
creates that gap. Even allowing residual exploration to recover 40% of the gap
without updates, the collapse is:

`0.054 * (1 - 0.40) = 0.0324`.

Collapse fraction relative to the reachable gap:

`0.0324 / 0.054 = 0.60`.

Bound: `0.60 >= f_abl (0.5)`.

Conclusion for `f_abl`: REACHABLE.

## Required non-evaluable and control branches

- If `G-PET-HARD` does not produce a candidate win, `G-PET-ABLATION` must report
  `not_evaluable_no_win`; it must not divide by a sign-flipped or near-zero
  denominator.
- The ablation arm must include an identity tripwire: if candidate and ablated
  traces are bitwise identical across the intervention window, the ablation
  evidence is invalid.
- The ablation arm must include a non-identity positive-control fixture where
  update freezing changes behavior in a constructed, non-identity case.
- These controls are design obligations for the implementation step; this file
  does not execute them.

## Use of seeds

- `S_scored` is not used by this derivation.
- `S_dev` is not used for numeric tuning in this derivation. It may be used only
  by the later one-seed CPU/runtime probe and debugging before scored runs.
- Any constant motion after this freeze requires an ADDENDUM commit before a
  scored run, followed by Claude re-check.

## Final reachability lines

- `δ_hard = 0.05`: REACHABLE.
- `f_abl = 0.5`: REACHABLE.
- `W = 50`: REACHABLE for the stated post-shift windows.
- Scored evidence status: NOT RUN.

Claim ceiling: pre-run reachability argument only; no learned-component pass,
no integration pass, no runtime wiring, no product readiness, and no mechanism
validity claim.
