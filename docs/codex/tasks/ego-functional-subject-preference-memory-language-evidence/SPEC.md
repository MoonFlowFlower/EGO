# EgoOperator Preference and Reminder Memory-Language Evidence Repair

## Goal

Keep preference and reminder replies evidence-aligned: preference updates should produce candidate-local evidence or be described as current-session adaptation, and reminder authorization should use bounded initiative/proposal language rather than unsupported durable memory wording.

## Scope

Allowed changes:

- `EgoOperator/agent_base.py`
- `EgoOperator/memory_system.py`
- `EgoOperator/tests/test_operator_runtime_contract.py`
- `EgoOperator/tests/test_memory_system.py`
- `Tasks/TASK_BOARD.yaml`
- `.codex/project_contract.yaml`
- this task directory

Forbidden changes:

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- `legacy/ego-pre-handmade-mainline/**`
- canonical memory/state authority

## Canonical Source

- `Tasks/TASK_BOARD.yaml` task `EGO-FS-017`
- `/tmp/ego_functional_subject_real_provider_rerun_20260521b/gpt55_judge_result.json`

## Acceptance Gate

- Preference/reminder replies avoid durable memory wording without gate evidence.
- Preference update text like "我更希望...判断和取舍" creates candidate-local preference evidence.
- Reminder authorization is framed as bounded initiative/proposal/current collaboration unless a real memory write or approval exists.

## Claim Ceiling

`Functional Subject preference-memory evidence local/scripted candidate pass`
