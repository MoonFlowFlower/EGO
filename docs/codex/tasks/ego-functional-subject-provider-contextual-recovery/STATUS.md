# Status

Status: accepted

## Decisions

- Keep this as contextual recovery, not a provider retry/fallback expansion.
- Do not mark recovered checkpoint replies as clean first-pass success; EGO-FS-035 attribution handles the evidence boundary.

## Source

- GPT-5.5 judge partial after `/tmp/ego_fs_010_after_fs035_20260523_082742/functional_subject_trial_report.json`
- Blockers: `fs_10_topic_switching` provider timeout and `fs_19_repeated_failure_learning` provider timeout visible reply.

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py` -> pass
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py::test_topic_switching_provider_error_returns_contextual_checkpoint EgoOperator/tests/test_operator_runtime_contract.py::test_policy_replay_provider_error_returns_trace_based_checkpoint EgoOperator/tests/test_operator_runtime_contract.py::test_provider_429_in_tool_loop_returns_chinese_error_not_nollm_fallback` -> pass
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests` -> 213 passed
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass, 298 passed
- `git diff --check -- EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py Tasks/TASK_BOARD.yaml docs/codex/tasks/ego-functional-subject-provider-contextual-recovery` -> pass

## Remaining Risk

This improves provider-error recovery for two Functional Subject cases. It does not prove provider stability, durable behavior, or human-observable benefit.
