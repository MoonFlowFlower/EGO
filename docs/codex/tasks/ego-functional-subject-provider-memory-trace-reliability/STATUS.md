# Status

## Current

`active`

## Notes

- Created from EGO-FS-027 closeout.
- v7 fast rerun improved fs_07/fs_15/fs_20 but remained GPT-5.5 `partial`.
- Remaining blockers are outside EGO-FS-027 scope: generic provider fallback transcripts, `fs_17` memory-gate overclaim wording, and weak transcript-visible planner/trace application.
- Experiment Control Plane v1 is now implemented as the first slice of this task:
  - Phase gate classifies the v7 run as Phase B / `mechanism_affects_transcript_partial`.
  - Experiment ledger separates EGO-FS-027 target-case improvement from unrelated parent-gate failures.
  - Failure taxonomy routes remaining blockers to `empty_response_recovery`, `memory_gate_language`, and `planner_trace_not_transcript_visible`.
  - Repair router recommends closing the completed EGO-FS-027 slice with issue-specific evidence while keeping EGO-FS-010 blocked and continuing this task.

## Verification

- `python3 -m py_compile scripts/run_ego_experience_trial.py scripts/codex_project_autopilot.py` -> pass.
- Targeted tests for experiment control and Autopilot routing -> pass.
- `python3 scripts/codex_project_autopilot.py experiment-route --report ...v7_fast... --current-task EGO-FS-027 --parent-task EGO-FS-010 --next-task EGO-FS-028 --target-case fs_07_ambiguous_goal --target-case fs_15_memory_correction --target-case fs_20_low_instruction_initiative` -> pass.
- Runtime behavior repairs for the routed blockers remain pending.
