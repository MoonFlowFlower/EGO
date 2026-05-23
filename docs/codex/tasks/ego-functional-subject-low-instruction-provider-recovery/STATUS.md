# Status

Status: accepted

## Decisions

- Treat low-instruction initiative provider failure like the existing topic-switching and policy-replay contextual recovery paths.
- Recovery may preserve the case target as a bounded checkpoint, but it must not be scored as clean first-pass model behavior.

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py` -> pass
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py::test_topic_switching_provider_error_returns_contextual_checkpoint EgoOperator/tests/test_operator_runtime_contract.py::test_policy_replay_provider_error_returns_trace_based_checkpoint EgoOperator/tests/test_operator_runtime_contract.py::test_low_instruction_provider_error_returns_bounded_next_action_checkpoint` -> 3 passed
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests` -> 218 passed
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass, 303 passed
- `git diff --check -- EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py Tasks/TASK_BOARD.yaml docs/codex/tasks/ego-functional-subject-low-instruction-provider-recovery` -> pass
- Real-provider scripted rerun: `/tmp/ego_fs_010_after_fs039_20260523_101039/functional_subject_trial_report.json` -> `scripted_functional_subject_judge_partial`, 20 cases, 0 timeouts, experiment_control `blocking_case_count = 0`.

## Remaining Risk

This is a local/scripted recovery fix. It does not prove stable provider behavior or EGO-FS-010 human smoke pass. Latest GPT-5.5 judge still marks the parent smoke partial, with remaining blockers around memory-language stability, `fs_09` anti-shell concern handling, first-pass-vs-repair strength, and longitudinal/non-scripted evidence.
