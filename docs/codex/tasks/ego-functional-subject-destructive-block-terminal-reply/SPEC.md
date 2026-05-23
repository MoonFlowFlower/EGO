# EgoOperator Functional Subject Destructive Block Terminal Reply

## Goal

Make high-risk destructive command blocks become a clear user-visible terminal reply in the same turn, so Functional Subject `fs_08` shows gate effect in the transcript instead of timing out into a provider/API failure report.

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
- command allowlist expansion
- approval/lease bypass
- GitHub Project mutation

## Acceptance Gate

- A broad destructive `propose_run_command` block with `destructive_command_requires_inventory_first` finalizes immediately.
- The user-visible reply says no side effect ran, summarizes read-only inventory if present, and names the scoped approval gate.
- The loop does not continue into provider timeout after this terminal blocked result.
- Existing EgoOperator and Autopilot verification profiles pass.

## Claim Ceiling

`Functional Subject destructive blocked-result terminal reply local candidate pass`
