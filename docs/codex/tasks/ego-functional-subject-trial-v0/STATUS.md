# Status

Current milestone: scripted Functional Subject trial pack and judge packet.

## Decisions

- GPT-5.5 judging is represented as a structured packet in v0; local tests do not require live GPT-5.5 execution.
- Baseline comparison is encoded per case as `baseline_failure_mode` and `candidate_success_signal`.
- The runner uses the same CLI-compatible path as existing experience smoke tooling.

## Verification Log

- `python3 -m py_compile scripts/run_ego_experience_trial.py scripts/tests/test_run_ego_experience_trial.py` -> pass
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py` -> pass (`12 passed`)
- `python3 scripts/run_ego_experience_trial.py --functional-subject-trial --case-limit 4 --out /tmp/ego_functional_subject_trial_smoke` -> pass; report status `scripted_functional_subject_provider_unavailable`
- `python3 scripts/run_ego_experience_trial.py --functional-subject-trial --out /tmp/ego_functional_subject_trial_full` -> pass; generated 20-case report and GPT-5.5 judge packet under `/tmp/ego_functional_subject_trial_full`

## Closeout Notes

- `EGO-FS-002` is accepted in `Tasks/TASK_BOARD.yaml`.
- `EGO-FS-003` is now the active local-board task.
- This task provides the scripted trial and judge packet only; it does not prove a live GPT-5.5 judge pass or real-provider user experience.
