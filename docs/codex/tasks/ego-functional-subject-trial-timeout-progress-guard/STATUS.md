# Status

## Current

`accepted`

## Notes

- Created after EGO-FS-029 because no local ready tasks remained and EGO-FS-010 was blocked by real-provider/human smoke evidence.
- Previous one-case and full real-provider reruns could hang without a final report, which made the parent smoke gate hard to audit.
- The trial harness now writes `functional_subject_trial_progress.json` after each completed case.
- The harness now supports `--case-timeout-seconds`; on WSL/Unix it records a timed-out case as explicit unavailable evidence instead of hanging forever.
- This does not close EGO-FS-010. It only makes the next full smoke rerun safer and more auditable.

## Verification

- `python3 -m py_compile scripts/run_ego_experience_trial.py` -> pass.
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py::test_functional_subject_trial_writes_progress_report scripts/tests/test_run_ego_experience_trial.py::test_functional_subject_trial_case_timeout_writes_partial_report` -> pass.
- `env -u OPENROUTER_API_KEY python3 scripts/run_ego_experience_trial.py --functional-subject-trial --case-limit 1 --case-timeout-seconds 30 --out /tmp/ego_fs_030_progress_smoke` -> pass, progress report written.
