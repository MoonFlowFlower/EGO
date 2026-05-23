# Status

Status: accepted

## Decisions

- Add an eval/report scorecard instead of trying to force more runtime repairs first.
- The scorecard is evidence routing, not product behavior proof.
- It should make future closeout comments and judge packets more precise about what was first-pass and what was guard/recovery behavior.

## Verification

- `python3 -m py_compile scripts/run_ego_experience_trial.py scripts/tests/test_run_ego_experience_trial.py` -> pass.
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py::test_functional_subject_response_attribution_summary_separates_origins scripts/tests/test_run_ego_experience_trial.py::test_functional_subject_trial_builds_gpt55_judge_packet scripts/tests/test_run_ego_experience_trial.py::test_functional_subject_experiment_control_classifies_v7_blockers` -> 3 passed.
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py` -> 28 passed.
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass, 310 passed.
- `python3 scripts/run_ego_experience_trial.py --functional-subject-trial --case-limit 4 --out /tmp/ego_fs044_scorecard_smoke` -> provider-unavailable local report smoke; JSON/judge packet/Markdown contain response attribution scorecard.

## Remaining Risk

This improves evidence interpretation. It does not itself improve user-facing behavior or prove Functional Subject efficacy. Future Functional Subject closeout must still use real-provider/human evidence where required.
