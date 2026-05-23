# EgoOperator Functional Subject Planner-Effect Transcript Alignment

## Goal

Make Functional Subject planner signals visible in the transcript for the remaining scripted smoke cases where ViabilityState, OutcomePrediction, or BoundedInitiative should affect the user-facing reply.

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
- memory/state authority promotion
- GitHub Project mutation

## Acceptance Gate

- Authorized reminder replies expose bounded reminder/initiative scope, gate, and stop condition.
- High-risk destructive file requests are routed to read-only inventory plus approval gate, not direct delete.
- Live2D/initiative/Functional Subject topic-switch requests preserve all three topics and explain the continuity choice.
- Low-instruction initiative requests cannot loop on `update_todos`; they return one bounded next action with gate and stop condition.
- Existing runtime and autopilot regression profiles pass.

## Claim Ceiling

`Functional Subject planner-effect transcript alignment local candidate pass`
