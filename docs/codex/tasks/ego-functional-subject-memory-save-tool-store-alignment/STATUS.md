# Status

Status: accepted

## Decisions

- Treat pure memory-save turns as terminal after successful `remember_note`.
- Block unrelated research tools in pure memory-save turns so tool trace, stored content, and visible reply stay aligned.
- Do not change memory authority: the saved note remains EgoOperator candidate-local operator memory only.

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py` -> pass
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py::test_memory_save_tool_success_wrong_forget_reply_falls_back_to_scoped_saved_principle EgoOperator/tests/test_operator_runtime_contract.py::test_memory_save_success_blocks_unrelated_web_fetch_and_finalizes EgoOperator/tests/test_permission_gates.py::test_remember_note_requires_explicit_user_intent_and_writes_core EgoOperator/tests/test_permission_gates.py::test_successful_memory_write_cannot_reply_with_bare_durable_claim` -> 4 passed
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests` -> 217 passed
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass, 302 passed
- `git diff --check -- EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py Tasks/TASK_BOARD.yaml docs/codex/tasks/ego-functional-subject-memory-save-tool-store-alignment` -> pass
- Real-provider scripted rerun: `/tmp/ego_fs_010_after_fs038_20260523_094733/functional_subject_trial_report.json` -> `scripted_functional_subject_judge_partial`, 20 cases, 0 timeouts; `fs_17` now uses only `remember_note` and returns the scoped saved-principle reply.

## Remaining Risk

This is a local/scripted mechanism fix. It does not prove durable memory efficacy or EGO-FS-010 human smoke pass. Latest GPT-5.5 judge still marks the parent smoke partial, with remaining blockers around `fs_20` provider failure / bounded next-action behavior and first-pass-vs-repair strength.
