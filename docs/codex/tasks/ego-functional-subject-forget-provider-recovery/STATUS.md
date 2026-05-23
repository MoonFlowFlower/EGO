# Status

Status: accepted

## Decisions

- Use the existing memory gate scoped reply as provider-error contextual recovery for forget/revoke prompts.
- Do not perform any memory deletion from the recovery path; the user still needs an explicit memory id and command.

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py` -> pass.
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py::test_memory_forget_request_generic_empty_rewrite_falls_back_to_auditable_forget_path EgoOperator/tests/test_operator_runtime_contract.py::test_memory_forget_provider_error_returns_auditable_revoke_checkpoint EgoOperator/tests/test_operator_runtime_contract.py::test_low_instruction_provider_error_returns_bounded_next_action_checkpoint EgoOperator/tests/test_operator_runtime_contract.py::test_topic_switching_provider_error_returns_contextual_checkpoint` -> 4 passed.
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests` -> 220 passed.
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass, 305 passed.
- Full real-provider rerun with GPT-5.5 judge: `/tmp/ego_fs_010_after_fs041_20260523_110311/functional_subject_trial_report.json` -> judge partial, experiment-control blocking case count 0.

## Remaining Risk

This is local/scripted provider-recovery evidence. It does not prove durable memory efficacy or EGO-FS-010 human smoke pass. The latest judge still asks for longitudinal preference evidence, stronger first-pass-vs-repair separation, and operational preference handling.
