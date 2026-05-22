# Plan

1. Add a prompt contract for ambiguous selfhood goals.
2. Add a bounded output repair guard when the model replies with clarification only.
3. Add deterministic fake-LLM regression coverage.
4. Update local board status after verification.

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py`
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py -q`
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full`
- `git diff --check -- EgoOperator Tasks/TASK_BOARD.yaml .codex/project_contract.yaml docs/codex/tasks/ego-functional-subject-ambiguous-selfhood-goal-slice`
