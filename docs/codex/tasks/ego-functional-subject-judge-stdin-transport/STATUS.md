# Status

## Current

`accepted_local`

## Notes

- WSL `OPENROUTER_API_KEY` was configured from the user-provided test key file without printing the secret.
- Real-provider v3 progressed through provider sampling but failed at GPT-5.5 judge launch because the packet was too large for argv.
- The judge transport now passes the prompt through stdin.
- Real-provider v4 reached GPT-5.5 judge successfully; judge returned `partial`, so the remaining blockers are behavior quality rather than transport.

## Verification

- `python3 -m py_compile scripts/run_ego_experience_trial.py scripts/tests/test_run_ego_experience_trial.py`
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py::test_companion_smoke_codex_judge_uses_gpt55_schema scripts/tests/test_run_ego_experience_trial.py::test_functional_subject_codex_judge_uses_functional_schema -q`
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> `272 passed` + diff check pass
- Real smoke: `python3 scripts/run_ego_experience_trial.py --functional-subject-trial --judge-with-codex --judge-model gpt-5.5 --out /mnt/c/Users/LEO/AppData/Local/Temp/ego_functional_subject_real_provider_rerun_v4` -> no argv transport failure; `judge=partial`
