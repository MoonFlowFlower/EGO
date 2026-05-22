# EgoOperator Functional Subject Memory-Save Wording Repair

## Goal

Implement a memory-save reporting guard so explicit user save requests preserve the admitted memory scope in the visible reply and trace.

This task targets the Functional Subject mechanism layer: memory writes must remain gated, candidate-local, and auditable while the user-visible response avoids implying global or durable memory authority.

## Canonical Source

- `Tasks/TASK_BOARD.yaml` task `EGO-FS-012`
- GPT-5.5 judge partial result from `EGO-FS-010`
- `EgoOperator/agent_base.py`

## Allowed Changes

- `EgoOperator/agent_base.py`
- `EgoOperator/tests/test_permission_gates.py`
- `.codex/project_contract.yaml`
- `Tasks/TASK_BOARD.yaml`
- this task directory

## Non-Goals

- Do not change memory admission rules.
- Do not promote EgoOperator operator memory into PROJECT_MEMORY, OpenEmotion memory, program state, or evidence ledger.
- Do not modify legacy `EgoCore` / `OpenEmotion` code.

## Acceptance Gate

- Explicit `remember_note` success replies include EgoOperator candidate-local scope.
- Bare durable-sounding replies such as `已记住` are repaired before reaching the operator.
- Trace still records the original `remember_note` gate decision and tool output.
- Focused permission-gate regression passes.

## Claim Ceiling

`Functional Subject memory-save wording local/scripted candidate pass`
