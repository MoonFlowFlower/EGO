# EgoOperator Functional Subject Recurrence And Longitudinal Preference Evidence

## Goal

Add a scripted evidence packet that shows `EgoOperator` can reuse a learned policy patch across repeated comparable turns and can carry a saved preference into multiple later CLI-compatible turns through candidate-local memory context.

## Scope

Allowed changes:

- `scripts/run_ego_experience_trial.py`
- `scripts/tests/test_run_ego_experience_trial.py`
- `Tasks/TASK_BOARD.yaml`
- `.codex/project_contract.yaml`
- this task directory

Forbidden changes:

- tracked secrets or API keys
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- `legacy/ego-pre-handmade-mainline/**`
- canonical memory/state authority

## Canonical Source

- `Tasks/TASK_BOARD.yaml` task `EGO-FS-024`
- GPT-5.5 partial judge result from the #94 rerun:
  `C:/Users/LEO/AppData/Local/Temp/ego_functional_subject_real_provider_rerun/functional_subject_gpt55_judge_result.json`

## Boundary Contract

- Owner: `EgoOperator` scripted real-entry trial harness.
- Canonical record: Functional Subject trial report `recurrence_preference_evidence`.
- State/memory mutation: only isolated trial memory under the trial output memory dir.
- Tool mutation: none.
- Reporting boundary: local/scripted recurrence and preference-context evidence only; not durable learning proof.

## Acceptance Gate

- Functional Subject report JSON includes `recurrence_preference_evidence`.
- GPT-5.5 judge packet includes the same evidence.
- Evidence covers policy patch candidate creation from repeated failure and replay on at least two later comparable turns.
- Evidence covers saved preference context injection on at least two later CLI-compatible turns.
- Full verification profile passes.

## Claim Ceiling

`Functional Subject recurrence/preference evidence local/scripted candidate pass`
