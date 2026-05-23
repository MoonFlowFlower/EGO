# EgoOperator Functional Subject Response Attribution Evidence

## Goal

Expose whether each Functional Subject trial reply came from clean first-pass behavior, an outcome-prediction gate, runtime repair, or a terminal guard, so GPT-5.5 can judge mechanism strength without conflating repair-layer success with native behavior.

## Scope

Allowed changes:

- `scripts/run_ego_experience_trial.py`
- `scripts/tests/test_run_ego_experience_trial.py`
- `Tasks/TASK_BOARD.yaml`
- this task directory

Forbidden changes:

- `EgoOperator/**` runtime behavior
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- `legacy/ego-pre-handmade-mainline/**`
- GitHub Project mutation

## Acceptance Gate

- `trace_evidence.response_attribution` includes `final_response_origin`, `repair_applied`, `repair_count`, `repair_types`, candidate reason, and external status.
- Runtime repair and terminal guard replies are not marked as clean first-pass behavior.
- GPT-5.5 judge packet includes a response-attribution contract telling the judge not to score repair output as clean first-pass Functional Subject behavior.
- Existing trial/autopilot regression tests pass.

## Claim Ceiling

`Functional Subject response-attribution evidence local workflow pass`
