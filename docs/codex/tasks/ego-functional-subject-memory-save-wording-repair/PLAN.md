# Plan

1. Add candidate-local scope metadata to successful `remember_note` tool output.
2. Add an output guard that appends scope when the final LLM reply after successful memory write lacks it.
3. Add deterministic fake-LLM regressions for bare `已记住` and generic `完成`.
4. Run targeted tests, then `autopilot_full`.
5. Update `Tasks/TASK_BOARD.yaml` to move `EGO-FS-012` to accepted and activate `EGO-FS-013` only after verification passes.

## Rollback

Revert the prompt/tool-output scope changes, output guard, tests, task doc, and board status update.
