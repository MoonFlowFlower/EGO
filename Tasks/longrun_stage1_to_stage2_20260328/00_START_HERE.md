# Stage1 to Stage2 Long-Run Batch

## Goal

Use a file-driven long-run batch to push the system from `Stage 1` to a formal `Stage 2` admission decision without relying on raw chat history.

## Ground Truth

Read these first:

1. `OpenEmotion/roadmap/SELF_AWARE_NORMALIZATION_RULES_20260328.md`
2. `OpenEmotion/roadmap/self_aware_normalized_state.json`
3. `OpenEmotion/docs/archive/mvp11/MVP11_5_STAGE_OVERVIEW.md`
4. `OpenEmotion/docs/archive/mvp11/MVP11_5_READINESS_CRITERIA.md`
5. `runtime/RUN_STATE.json`
6. `runtime/SESSION_HANDOFF.md`

## Execution Model

- Use `02_QUEUE.yaml` to decide the next step.
- Use `runtime/RUN_STATE.json` as the source of truth for current progress.
- After each step:
  - update `runtime/RUN_STATE.json`
  - write a step report under `reports/`
  - update `runtime/SESSION_HANDOFF.md` if continuing
- Stop immediately if `04_STOP_RULES.md` says to stop.

## Batch End States

Only two terminal outcomes are allowed:

- `promoted_to_stage2`
- `stage1_blocker_complete_stop`

Reaching neither means the batch is still in progress.
