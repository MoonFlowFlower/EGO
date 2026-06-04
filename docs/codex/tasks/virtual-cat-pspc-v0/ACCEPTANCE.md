# VirtualCatPSPC v0 Acceptance

## Acceptance Is Not Pytest Alone

Pytest can prove deterministic contracts and guard against regressions. It does not by itself prove the PSPC mechanism. The acceptance evidence is the combination of tests, seeded traces, metrics, and canonical reports.

## Required Reports

The lab runner must produce:

- `artifacts/virtual_cat_pspc_v0/BASELINE_REPORT.md`
- `artifacts/virtual_cat_pspc_v0/DANGER_GENERALIZATION_REPORT.md`
- `artifacts/virtual_cat_pspc_v0/MEMORY_DELETION_ABLATION.md`
- `artifacts/virtual_cat_pspc_v0/FROZEN_WORLD_MODEL_ABLATION.md`
- `artifacts/virtual_cat_pspc_v0/FROZEN_SELF_MODEL_ABLATION.md`
- `artifacts/virtual_cat_pspc_v0/NO_PREDICTION_ERROR_LEARNING_ABLATION.md`
- `artifacts/virtual_cat_pspc_v0/REPLAY_DETERMINISM_REPORT.md`

Each report must include:

- status
- seeds
- trace refs or trace hashes
- what it proves
- what it does not prove
- failure meaning
- rollback note

## Preregistered Gates

### Gate 1: Different Histories

- expected: unstable-object experience produces a more cautious future action than a safe/no-danger history on the same unseen unstable tall object.
- failure meaning: memory/history is not causally affecting planning.

### Gate 2: Dangerous-Object Generalization

- expected: learned caution transfers from a seen unstable object to an unseen object with similar instability/height/fragility features.
- failure meaning: the system learned an object-name rule or did not learn the risk feature.

### Gate 3: Memory Deletion

- expected: deleting relevant unstable-object memory reduces learned cautious behavior.
- failure meaning: memory writes are logs only, not causal support for future behavior.

### Gate 4: Frozen World Model

- expected: freezing world-model learning increases prediction error and reduces dangerous-object planning quality.
- failure meaning: the world model is not used by the planner or not updated by prediction error.

### Gate 5: Frozen Self Model

- expected: freezing self-model learning reduces risk/ability judgment and changes the action selected under the same world-risk signal.
- failure meaning: the self model is not causally involved in planning.

### Gate 6: No Prediction-Error Learning

- expected: disabling prediction-error learning prevents prediction-error reduction and reduces learned caution.
- failure meaning: the claimed learning path is not the source of behavior change.

### Gate 7: Replay Determinism

- expected: same seed and same internal state produce the same selected action and trace digest.
- failure meaning: evidence cannot be audited or replayed.

## Claim Ceiling

If all gates pass, the maximum claim is:

`VirtualCatPSPC v0 proto-self mechanism experiment local lab candidate`

This does not prove stable real user benefit, live autonomy, durable memory efficacy, EgoOperator runtime efficacy, philosophical consciousness, subjective experience, or production readiness.
