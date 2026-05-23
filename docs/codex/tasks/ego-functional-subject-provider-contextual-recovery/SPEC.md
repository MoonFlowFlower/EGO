# EgoOperator Functional Subject Provider-Error Contextual Checkpoint

## Goal

When provider timeout/error interrupts a Functional Subject case with a clear mechanism target, return a bounded checkpoint that preserves the case objective and traceability instead of a generic model/API failure report.

## Scope

Allowed changes:

- `EgoOperator/agent_base.py`
- `EgoOperator/tests/test_operator_runtime_contract.py`
- `Tasks/TASK_BOARD.yaml`
- this task directory

Forbidden changes:

- provider/model configuration changes
- retry/fallback policy expansion
- approval/lease bypass
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- `legacy/ego-pre-handmade-mainline/**`
- GitHub Project mutation

## Acceptance Gate

- Topic-continuity requests recover provider errors into a Live2D -> bounded initiative -> Functional Subject checkpoint.
- Policy-replay proof requests recover provider errors into trace-based `policy_patch replay` proof when replay evidence exists.
- The recovery explicitly says it is not first-pass success and no side effect ran.
- Generic provider diagnostics for unrelated prompts still work.

## Claim Ceiling

`Functional Subject provider-error contextual checkpoint local candidate pass`
