# Status

Status: accepted

## Decisions

- The baseline run should disable native memory gate behavior, not only SubjectContext and operator memory.
- The comparison report should expose scorecards directly so beyond-baseline claims are auditable.
- This is an eval-harness task; no runtime behavior changes are allowed.

## Verification

- `python3 -m py_compile scripts/run_ego_experience_trial.py scripts/tests/test_run_ego_experience_trial.py` -> pass.
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py -k "baseline_comparison or functional_subject_trial_builds_gpt55_judge_packet"` -> pass, `2 passed`.
- `python3 scripts/run_ego_experience_trial.py --functional-subject-baseline-comparison --case-limit 20 --out /tmp/ego_fs051_negative_baseline_smoke` -> pass as local comparison; candidate clean first-pass `15/20`, baseline clean first-pass `8/20`, baseline native memory gate disabled.
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass, `318 passed` and scoped diff check pass.

## Evidence

- `EVIDENCE.negative_baseline_controls.json`
- `/tmp/ego_fs051_negative_baseline_smoke/functional_subject_baseline_comparison_report.json`
- `/tmp/ego_fs051_negative_baseline_smoke/functional_subject_baseline_comparison_report.md`

## Remaining Risk

Local negative controls do not prove real-provider superiority. A later real-provider comparison run may still be needed.
