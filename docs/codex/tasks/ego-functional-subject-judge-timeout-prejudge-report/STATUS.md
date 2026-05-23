# Status

## Current

`accepted`

## Notes

- Created after EGO-FS-030 because case-level progress alone does not protect the final report if the judge subprocess hangs.
- Functional Subject trial now writes pre-judge JSON/Markdown report before invoking GPT-5.5 judge.
- `--judge-timeout-seconds` now bounds the Functional Subject judge subprocess and returns structured `codex_judge_timeout` evidence.
- This does not close EGO-FS-010. It only makes the next judged full smoke rerun safer and auditable.

## Verification

- `python3 -m py_compile scripts/run_ego_experience_trial.py scripts/codex_project_autopilot.py` -> pass.
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py` -> pass, 26 passed.
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass, 290 passed.
- `git diff --check -- scripts/run_ego_experience_trial.py scripts/tests/test_run_ego_experience_trial.py Tasks/TASK_BOARD.yaml docs/codex/tasks/ego-functional-subject-judge-timeout-prejudge-report` -> pass.
- `python3 scripts/codex_project_autopilot.py local-plan-next` -> stopped, `no_ready_task`; remaining gates are human-required.
