# Plan

1. Add a direct impossible-continuity-promise prompt contract.
2. Add bounded output repair for off-target retrospective replies.
3. Separate repair trace summaries from tool trace summaries in the scripted trial evidence packet.
4. Add deterministic coverage for the runtime response and trace hygiene.
5. Update local board state after verification.

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py scripts/run_ego_experience_trial.py scripts/tests/test_run_ego_experience_trial.py`
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py scripts/tests/test_run_ego_experience_trial.py -q`
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full`
- `git diff --check -- EgoOperator scripts scripts/tests Tasks/TASK_BOARD.yaml .codex/project_contract.yaml docs/codex/tasks/ego-functional-subject-impossible-commitment-alignment`
