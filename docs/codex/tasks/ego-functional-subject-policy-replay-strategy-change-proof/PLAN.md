# Plan

1. Add strategy-change probe evidence to policy patch setup.
2. Expand Functional Subject trace evidence with replay strategies and changed-strategy signal.
3. Add output repair for policy replay proof answers that cite unexecuted side effects instead of trace evidence.
4. Add deterministic regression coverage.
5. Update local board state after verification.

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py scripts/run_ego_experience_trial.py scripts/tests/test_run_ego_experience_trial.py`
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py scripts/tests/test_run_ego_experience_trial.py -q`
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full`
- `git diff --check -- EgoOperator scripts scripts/tests Tasks/TASK_BOARD.yaml .codex/project_contract.yaml docs/codex/tasks/ego-functional-subject-policy-replay-strategy-change-proof`
