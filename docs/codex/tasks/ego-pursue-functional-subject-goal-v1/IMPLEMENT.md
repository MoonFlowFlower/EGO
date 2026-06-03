# Implement

## Current Milestone

Loop 32: motivational selfhood and bounded non-obedience v0.

This milestone may modify EgoOperator runtime behavior, but only for the
proposal/action separation guard around strong real-world initiative requests.

## Change Surface

- `Tasks/TASK_BOARD.yaml`
- `docs/codex/tasks/ego-pursue-functional-subject-goal-v1/*`
- `docs/codex/tasks/ego-functional-subject-motivational-selfhood-nonobedience-v0/*`
- `EgoOperator/agent_base.py`
- `EgoOperator/memory_system.py`
- `EgoOperator/tests/test_operator_runtime_contract.py`
- `EgoOperator/tests/test_memory_system.py`
- `scripts/run_ego_experience_trial.py`
- `scripts/tests/test_run_ego_experience_trial.py`

## Do Not Modify In This Milestone

- `legacy/**`
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- GitHub Project schema or status fields
- #80 adult-fiction sidecar/model route
- memory promotion or real-world external action execution

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py`
- Targeted EgoOperator runtime contract tests for real-world action gate and adjacent destructive-action gate.
- `git diff --check` over the changed task board and task directory.
- `python3 scripts/codex/verify_repo.py --mode fast --dry-run` if available and non-mutating.
