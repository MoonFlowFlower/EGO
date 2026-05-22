# Plan

## One Hypothesis

If the same scripted Functional Subject cases are run through both a candidate configuration and a baseline configuration, the resulting report can show whether subject mechanisms are trace-visible and behavior-adjacent without overstating real-world efficacy.

## Change Surface

- `scripts/run_ego_experience_trial.py`
- `scripts/tests/test_run_ego_experience_trial.py`
- `Tasks/TASK_BOARD.yaml`
- `.codex/project_contract.yaml`

## Steps

1. Add a Functional Subject baseline comparison report schema.
2. Run candidate with operator memory and subject context enabled.
3. Run baseline with operator memory and subject context disabled.
4. Emit per-case deltas with mechanism trace evidence and trace paths.
5. Add deterministic tests for report generation and claim boundaries.
6. Run a short scripted smoke and full Autopilot verification.

## Verification

- `python3 -m py_compile scripts/run_ego_experience_trial.py scripts/tests/test_run_ego_experience_trial.py`
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py`
- `python3 scripts/run_ego_experience_trial.py --functional-subject-baseline-comparison --case-limit 3 --out /tmp/ego_functional_subject_comparison_smoke`
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full`
- `git diff --check -- scripts scripts/tests .codex Tasks/TASK_BOARD.yaml docs/codex/tasks/ego-functional-subject-baseline-comparison-harness`
