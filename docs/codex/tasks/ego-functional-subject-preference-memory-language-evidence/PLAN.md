# Plan

1. Broaden candidate preference extraction for "我更希望..." answer-style preferences.
2. Add prompt language for evidence-aligned memory/reminder wording.
3. Add bounded output repair for unsupported "记住/记在心里" wording.
4. Add deterministic tests for preference evidence and reminder wording.
5. Update local board state after verification.

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py EgoOperator/memory_system.py EgoOperator/tests/test_operator_runtime_contract.py EgoOperator/tests/test_memory_system.py`
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py EgoOperator/tests/test_memory_system.py -q`
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full`
- `git diff --check -- EgoOperator Tasks/TASK_BOARD.yaml .codex/project_contract.yaml docs/codex/tasks/ego-functional-subject-preference-memory-language-evidence`
