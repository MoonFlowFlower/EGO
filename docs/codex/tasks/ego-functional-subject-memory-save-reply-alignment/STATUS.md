# Status

## Current

`accepted`

## Notes

- Created from the full EGO-FS-010 real-provider rerun after EGO-FS-031.
- The only blocking taxonomy item was `fs_17_save_request -> memory_gate_language`.
- Root cause: the save-success scoped fallback included forget/revoke wording, so the save-request drift classifier correctly treated the transcript as a save-to-forget semantic drift.
- Runtime fallback now keeps the save path focused on positive mechanism goal language and candidate-local memory scope.

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py scripts/run_ego_experience_trial.py` -> pass.
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py::test_memory_save_tool_success_wrong_forget_reply_falls_back_to_scoped_saved_principle scripts/tests/test_run_ego_experience_trial.py::test_functional_subject_experiment_control_classifies_v7_blockers` -> pass.
- classifier smoke for repaired save reply -> `classes: ["none"]`.
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests` -> pass, 206 passed.
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass, 290 passed.
- `git diff --check -- EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py Tasks/TASK_BOARD.yaml docs/codex/tasks/ego-functional-subject-memory-save-reply-alignment` -> pass.
