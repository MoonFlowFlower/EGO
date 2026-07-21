# Collision record: EGO-V2-P1-FACTORED-PREDICTIVE-CONTROL-001A

## Real objective and invalidating explanation

The real objective is not to make survival curves look better.  It is to test
whether separately auditable outcome prediction, value evaluation, and update
history influence the existing product decision flow.  The strongest reason
the framing may be invalid is that a compact lookup policy or the current
heuristic can match the same behavior without reusable prediction learning.

A result is falsified if predictor no-update or empirical lookup is equivalent,
heldout Brier/NLL does not improve, goal intervention changes outcome
predictions, or the effect disappears outside a memorized visible-state key.
Longer lives, attractive plans, nonzero updates, green tests, or trace
self-consistency alone remain insufficient.

## Candidate comparison

### Candidate 1: mixed one-step total score

- **Implementation:** add learned bonuses directly to the existing candidate
  score.
- **Evidence produced:** action rankings and a survival curve.
- **Cheap matching baseline:** current heuristic, a one-step shield, or tuned
  score weights.
- **Leakage/hard-coding risk:** high; fact prediction and desired value become
  inseparable, and a hand-coded death feature can impersonate learning.
- **Smallest falsifier:** change the goal while holding state/action fixed; if
  claimed outcome predictions change, the representation is not factored.
- **Expected failure:** behavior may improve without identifying a learned
  consequence model.

### Candidate 2: visible-state empirical lookup

- **Implementation:** memorize return/action statistics for observation and
  energy keys, then reuse the best action.
- **Evidence produced:** cross-life reuse on repeated visible states.
- **Cheap matching baseline:** an equal-access lookup table is the mechanism
  itself.
- **Leakage/hard-coding risk:** medium to high; near-unique state keys can make
  updates look active while providing no generalization.
- **Smallest falsifier:** heldout layouts/seeds or an equivalence-band match by
  the independent lookup control.
- **Expected failure:** memorized states do not transfer across relative paths
  or new layouts.

### Candidate 3: factored belief, predictor, value, and bounded planning

- **Implementation:** update an episode-relative belief from visible receipts;
  learn a goal-independent outcome/self predictor; apply goal/value weights in
  a separate deterministic trajectory evaluator; select one existing atomic
  action through `compute_step`.
- **Evidence produced:** separable predictions and values, online prediction
  errors, intervention-sensitive plans, full replay, learning curves, and
  independent baseline/ablation contrasts.
- **Cheap matching baseline:** lookup, predictor no-update, horizon one, no-map,
  and shield-only remain explicit challengers.
- **Leakage/hard-coding risk:** predictor could encode goal or private world
  data, or planning could silently use world transition truth.  A scanner and
  goal counterfactual positive controls must reject both.
- **Smallest falsifier:** prediction bytes differ under goal intervention;
  no-update/lookup equivalence; no heldout Brier/NLL improvement; or fresh
  process replay divergence.
- **Expected failure:** sparse observations may not identify resource-bearing
  paths within 16 lives, leaving no product headroom over simpler controls.

## Selection and locked boundary

Select Candidate 3 because it alone creates an intervention boundary between
facts and values while keeping the existing product state-transition flow.
Selection does not assert that it will beat the controls.  The first
implementation signal is a numerical unit test for predictor update plus a
goal-counterfactual separation test.  Stop rather than tune if the declared
effect gate fails.

Hard-coding, local-optimum, Zeno, leakage, weak-baseline, schema-split,
second-path, replay, and claim-inflation checks are mandatory.  The rollback is
limited to Phase B hunks.  Auto remote anchoring is forbidden.
