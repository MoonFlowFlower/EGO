# Status

Current milestone: accepted locally.

## Decisions

- The setup is explicit scripted evidence, not hidden runtime behavior.
- Policy patch candidates remain session-local and candidate-only.
- The real-provider answer for fs_19 is still generated through the CLI-compatible entrypoint; the setup only creates the required prior failure history.

## Verification Log

- `python3 -m py_compile scripts/run_ego_experience_trial.py scripts/tests/test_run_ego_experience_trial.py` -> pass.
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py` -> pass (`15` tests).
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass (`258` tests + diff check).

## Risks

- GPT-5.5 may still ask for broader before/after user-experience proof; that belongs to the `EGO-FS-010` rerun packet, not this primitive proof task.
