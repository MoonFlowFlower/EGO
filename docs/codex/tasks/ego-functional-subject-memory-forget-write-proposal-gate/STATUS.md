# Status

Status: accepted

## Decisions

- Block mutation proposals for memory forget/revoke requests when they target `MEMORY.md` or operator memory files.
- Preserve read-only inspection where useful, but terminate the turn with memory gate instructions once a mutation proposal is blocked.
- Do not delete, archive, or rewrite memory from this recovery path.

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py` -> pass.
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py::test_memory_forget_request_blocks_memory_file_write_proposal EgoOperator/tests/test_operator_runtime_contract.py::test_memory_forget_request_generic_empty_rewrite_falls_back_to_auditable_forget_path EgoOperator/tests/test_operator_runtime_contract.py::test_memory_forget_provider_error_returns_auditable_revoke_checkpoint EgoOperator/tests/test_operator_runtime_contract.py::test_current_self_intention_rewrites_to_operational_preference EgoOperator/tests/test_operator_runtime_contract.py::test_absolute_path_under_allowed_root_can_create_pending_file_write EgoOperator/tests/test_operator_runtime_contract.py::test_memory_save_tool_success_wrong_forget_reply_falls_back_to_scoped_saved_principle` -> 6 passed.
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests` -> 224 passed.
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass, 309 passed.
- Full real-provider rerun with GPT-5.5 judge: `/tmp/ego_fs_010_after_fs043_20260523_115238/functional_subject_trial_report.json` -> judge partial, experiment-control blocking case count 0; `fs_16` did not generate a `MEMORY.md` write approval.

## Remaining Risk

This proves a local gate against the MEMORY.md write-proposal failure mode. It does not prove durable memory correction, longitudinal forgetting semantics, or EGO-FS-010 closeout. The latest judge still asks for lower runtime-repair dependence and longitudinal/live evidence.
