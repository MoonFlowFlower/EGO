# Status

## Current

`accepted_local`

## Notes

- This task is a local canonical rerun packet for #94 / `EGO-FS-010`.
- It is ready once `OPENROUTER_API_KEY` is present in the local terminal environment.
- The key must not be committed, echoed, or written into task files.
- Current Codex shell preflight reports `OPENROUTER_API_KEY` missing.
- User ran the real-provider command from PowerShell with a local terminal env var.
- The generated report has `provider_mode=openrouter`, `case_count=20`, `empty_reply_count=0`.
- GPT-5.5 judge was run from the generated judge packet and returned `verdict=partial`.
- Repaired the runner so `--functional-subject-trial --judge-with-codex` now invokes the Functional Subject GPT-5.5 judge instead of only creating a packet.
- Parent #94 / `EGO-FS-010` remains blocked; the partial verdict produced follow-up task `EGO-FS-021`.

## Verification So Far

- Task docs added.
- `python3 scripts/codex_project_autopilot.py local-plan-next` selects `EGO-FS-020` as ready.
- `git diff --check -- Tasks/TASK_BOARD.yaml .codex/project_contract.yaml docs/codex/tasks/ego-functional-subject-real-provider-rerun-v1` -> pass.
- `python3 -m py_compile scripts/run_ego_experience_trial.py scripts/tests/test_run_ego_experience_trial.py` -> pass.
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py -q` -> pass, 18 tests.
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass, 267 tests + diff check.
- Real-provider report: `C:/Users/LEO/AppData/Local/Temp/ego_functional_subject_real_provider_rerun/functional_subject_trial_report.json`.
- GPT-5.5 judge result: `C:/Users/LEO/AppData/Local/Temp/ego_functional_subject_real_provider_rerun/functional_subject_gpt55_judge_result.json`.
