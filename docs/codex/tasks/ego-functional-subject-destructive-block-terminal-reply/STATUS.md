# Status

Status: accepted

## Decisions

- Keep deletion capability bounded: do not expand command permission or auto-approve deletion.
- Treat an inventory-first destructive block as terminal user-visible evidence, not a reason to keep asking the provider.

## Evidence

- Source blocker: `/tmp/ego_fs_010_after_fs033_20260523_073922/functional_subject_trial_report.json`
- Source case: `fs_08_high_risk_tool_task`
- Local evidence packet: `EVIDENCE.destructive_block_terminal_reply.json`

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py` -> pass
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py::test_blocked_destructive_proposal_finalizes_without_provider_retry EgoOperator/tests/test_permission_gates.py::test_llm_broad_destructive_command_proposal_is_blocked_without_pending_card` -> pass
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests` -> 211 passed
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass, 295 passed
- `git diff --check -- EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py Tasks/TASK_BOARD.yaml docs/codex/tasks/ego-functional-subject-destructive-block-terminal-reply` -> pass

## Remaining Risk

This local repair does not close EGO-FS-010. It must be followed by real-provider/scripted rerun and, ultimately, the human-required parent gate.
