# Collision record — EGO-V2-P0-METABOLISM-VIABILITY-COUPLING-001A

Layer: product engineering implementation. Mainline target: the existing
explicit/default-off V2 reducer chain. Claim ceiling: task-local repair only.

## Candidate 1 — minimal cue/action patch

- Change: subtract a tick constant, then grant energy when cue is `resource` or
  action is `forage`.
- Evidence produced: declining idle energy and occasional recovery.
- Strongest cheap match: a two-rule behavior tree.
- Leakage/hard-coding risk: critical; the cue/action leaks the intended reward
  and no environment consequence is required.
- Smallest falsifying test: forage twice without moving or use a resource cue
  when the hidden site outcome is negative.
- Expected failure: false energy gain.
- Disposition: rejected.

## Candidate 2 — strongest shortcut baseline

- Change: add a separate starvation controller or UI gate that forces
  rest/forage below a threshold.
- Evidence produced: visually plausible survival behavior.
- Strongest cheap match: clock + energy threshold + forced action table.
- Leakage/hard-coding risk: critical; it creates a second selector and replay
  can disagree with the visible path.
- Smallest falsifying test: recover the same SQLite command sequence without
  calling the UI/controller shortcut.
- Expected failure: live/replay divergence or stored-action dependence.
- Disposition: retained only as the hostile baseline explanation; not built.

## Candidate 3 — mechanism-faithful engineering repair

- Change: the existing world transition emits `food_obtained`; the existing
  reducer computes one post-outcome metabolism ledger and intersects the
  existing topology gate with a task-local critical-energy action subset.
- Evidence produced: energy accounting, a real downstream selector restriction,
  and SQLite recomputation from state plus commands.
- Strongest cheap match: the fixed survival heuristic still explains the
  behavior, so the claim remains engineering-only.
- Leakage/hard-coding risk: bounded if hidden regime and cue never enter the
  food predicate and no second path is added.
- Smallest falsifying test: positive non-forage outcome, zero-distance forage,
  negative forage outcome, trace tamper, and fresh-process replay.
- Expected failure: if outcome provenance is not environment-owned, gain leaks;
  if gating is outside the reducer, replay diverges.
- Disposition: selected.

## Selection and closure rule

Candidate 3 is the only option that strengthens the existing causal/replay
chain. Because Candidate 2 can match all visible behavior, no mechanism claim
is permitted even if Candidate 3 passes every test. A failure of environment
ownership, recomputation, or changed-path scope closes the repair as negative
evidence rather than triggering threshold tuning.
