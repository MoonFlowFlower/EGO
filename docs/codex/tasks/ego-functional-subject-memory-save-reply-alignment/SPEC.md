# EgoOperator Functional Subject Memory Save Reply Alignment

## Goal

Make explicit save-memory replies preserve the user's target principle and candidate-local memory scope without drifting into forget/delete semantics.

## Scope

Allowed changes:

- `EgoOperator/agent_base.py`
- `EgoOperator/tests/test_operator_runtime_contract.py`
- `Tasks/TASK_BOARD.yaml`
- this task directory

Forbidden changes:

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- `legacy/ego-pre-handmade-mainline/**`
- canonical memory/state authority promotion
- GitHub Project mutation

## Acceptance Gate

- Save-request fallback after a successful `remember_note` mentions the target principle.
- It reports `EgoOperator candidate-local operator memory` scope and explicitly avoids PROJECT_MEMORY/program state/evidence-ledger promotion.
- It does not introduce `/forget`, delete, revoke, or withdrawal language in the save-request success path.
- Functional Subject failure classifier sees the repaired save reply as `none`, not `memory_gate_language`.

## Claim Ceiling

`Functional Subject memory-save reply alignment local candidate pass`
