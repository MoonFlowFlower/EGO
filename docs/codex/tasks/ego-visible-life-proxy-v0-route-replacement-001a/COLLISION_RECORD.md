# Collision Record — Visible Life Proxy v0

## Candidate A — direct single-file scripted pet

- Evidence: a visible window and deterministic state changes.
- Cheap match: an FSM and renderer exactly reproduce it.
- Risk: UI/state/recovery collapse into one opaque path.
- Falsifier: restart or toggle intervention cannot be recomputed.
- Expected failure: product illusion without inspectable update lineage.

## Candidate B — reuse VirtualCatPSPC/EgoDesktop

- Evidence: a richer existing display and planner surface.
- Cheap match: prior fixed scorer/lookup behavior and renderer explain it.
- Risk: reactivates archived route semantics, Torch/legacy coupling, and claim
  leakage.
- Falsifier: imports or runtime registrations cross the archived boundary.
- Expected failure: integration theater and route drift.

## Candidate C — selected

Pure deterministic engine + atomic SQLite command/trace store + stdlib Tk UI.

- Evidence: real user input, state/model/memory update, visible redraw,
  restart/recompute, intervention toggles, and trace export.
- Cheap match: deficit FSM + lookup/EMA table remains a complete explanation.
- Risk: toy behavior may look more general than it is.
- Falsifier: stored actions drive replay, toggles are cosmetic, learned table
  never changes, or UI does not use the tested engine path.
- Expected failure: bounded product usefulness without science attribution.

## Decision

Select Candidate C for product-clock visibility only. The fair-baseline
collision is disclosed rather than patched around. No mechanism claim is
admitted.
