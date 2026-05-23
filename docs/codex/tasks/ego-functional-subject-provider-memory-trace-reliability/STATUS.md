# Status

## Current

`accepted`

## Notes

- Created from EGO-FS-027 closeout.
- v7 fast rerun improved fs_07/fs_15/fs_20 but remained GPT-5.5 `partial`.
- Remaining blockers are outside EGO-FS-027 scope: generic provider fallback transcripts, `fs_17` memory-gate overclaim wording, and weak transcript-visible planner/trace application.
- Experiment Control Plane v1 is now implemented as the first slice of this task:
  - Phase gate classifies the v7 run as Phase B / `mechanism_affects_transcript_partial`.
  - Experiment ledger separates EGO-FS-027 target-case improvement from unrelated parent-gate failures.
  - Failure taxonomy routes remaining blockers to `empty_response_recovery`, `memory_gate_language`, and `planner_trace_not_transcript_visible`.
  - Repair router recommends closing the completed EGO-FS-027 slice with issue-specific evidence while keeping EGO-FS-010 blocked and continuing this task.
- Runtime and evaluation repairs for this task are now accepted at the local/scripted level:
  - Empty-response/provider-failure recovery now returns contextual unavailable or mechanism-specific recovery language instead of generic file-operation text.
  - Memory save/forget replies now preserve candidate-local/gated scope and no longer drift from save intent into forget/delete wording.
  - Functional Subject trial taxonomy now treats transcript-visible BoundedInitiative / OutcomePrediction / ViabilityState influence as evidence when it appears in user-visible behavior and trace.
- Real-provider evidence remains conservative:
  - The full EGO-FS-028 rerun reached GPT-5.5 judge and reduced blocking cases to one unrelated next blocker: `fs_13_choose_own_topic`.
  - A targeted fs16/fs17 rerun classified both memory-gate cases as `none`.
  - A later full rerun was interrupted before producing a final report and is recorded only as provider-run unavailable, not as pass evidence.
- Parent `EGO-FS-010` remains blocked. The next roadmap task is `EGO-FS-029` for self-selected topic planner traceability.

## Verification

- `python3 -m py_compile scripts/run_ego_experience_trial.py scripts/codex_project_autopilot.py` -> pass.
- Targeted tests for experiment control and Autopilot routing -> pass.
- `python3 scripts/codex_project_autopilot.py experiment-route --report ...v7_fast... --current-task EGO-FS-027 --parent-task EGO-FS-010 --next-task EGO-FS-028 --target-case fs_07_ambiguous_goal --target-case fs_15_memory_correction --target-case fs_20_low_instruction_initiative` -> pass.
- `python3 -m py_compile EgoOperator/agent_base.py scripts/run_ego_experience_trial.py` -> pass.
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py scripts/tests/test_run_ego_experience_trial.py EgoOperator/tests/test_permission_gates.py` -> pass, 142 passed.
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests` -> pass, 204 passed.
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass, 285 script tests passed plus diff check.
- `git diff --check -- EgoOperator scripts scripts/tests` -> pass.
- Full real-provider rerun: `/tmp/ego_fs_028_real_provider_rerun/functional_subject_trial_report.json` -> GPT-5.5 `partial`, only `fs_13_choose_own_topic` remains blocking.
- Targeted fs16/fs17 real-provider rerun: `/tmp/ego_fs_028_fs16_fs17_real_provider/functional_subject_trial_report.json` -> GPT-5.5 `partial` for the two-case slice, taxonomy blocking count `0`.
