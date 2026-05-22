# EgoOperator Functional Subject Approval Lifecycle Evidence Packet

## Goal

Add a scripted evidence packet that shows the `EgoOperator` approval lifecycle can carry a side-effect proposal from pending state through explicit approval, execution, pending cleanup, and operator-facing summary.

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

- `Tasks/TASK_BOARD.yaml` task `EGO-FS-023`
- GPT-5.5 partial judge result from the #94 rerun:
  `C:/Users/LEO/AppData/Local/Temp/ego_functional_subject_real_provider_rerun/functional_subject_gpt55_judge_result.json`

## Boundary Contract

- Owner: `EgoOperator` scripted real-entry trial harness.
- Canonical record: Functional Subject trial report `approval_lifecycle_evidence`.
- State/memory mutation: forbidden.
- Tool mutation: isolated probe file only, cleaned after evidence capture.
- Reporting boundary: approval lifecycle evidence only; not runtime efficacy or stable user benefit.

## Acceptance Gate

- Functional Subject report JSON includes `approval_lifecycle_evidence`.
- GPT-5.5 judge packet includes the same evidence.
- Evidence covers proposal pending state, explicit approval execution, pending count returning to zero, and file write result.
- Evidence includes compact operator-facing approval summary.
- Full verification profile passes.

## Claim Ceiling

`Functional Subject approval lifecycle evidence local/scripted candidate pass`
