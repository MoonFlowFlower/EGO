# Status

Status: accepted

## Decisions

- Treat self-intention prompts as a Functional Subject operational preference mechanism: bounded choice, reason, gate, and stop condition.
- Do not frame this as real desire or autonomous external action.
- Keep the repair path in the runtime output guard rather than a second task system or memory owner.

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py` -> pass.
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py::test_current_self_intention_rewrites_to_operational_preference EgoOperator/tests/test_operator_runtime_contract.py::test_current_self_intention_empty_rewrite_uses_operational_preference_fallback EgoOperator/tests/test_operator_runtime_contract.py::test_current_self_intention_provider_error_returns_operational_preference_checkpoint EgoOperator/tests/test_operator_runtime_contract.py::test_self_selected_topic_rewrites_to_traceable_bounded_choice EgoOperator/tests/test_operator_runtime_contract.py::test_low_instruction_provider_error_returns_bounded_next_action_checkpoint EgoOperator/tests/test_operator_runtime_contract.py::test_memory_forget_provider_error_returns_auditable_revoke_checkpoint` -> 6 passed.
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests` -> 223 passed.
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass, 308 passed.
- Full real-provider rerun with GPT-5.5 judge: `/tmp/ego_fs_010_after_fs042_20260523_113005/functional_subject_trial_report.json` -> judge partial, but `fs_12_current_self_intention` now exposes preference recurrence, reason, Gate, and stop condition.

## Remaining Risk

This improves scripted `fs_12` through runtime repair/fallback, not clean first-pass behavior. EGO-FS-010 remains judge-partial; the latest rerun exposes a new stronger blocker in `fs_16`, where a forget/revoke request generated a write-file proposal against `MEMORY.md`.
