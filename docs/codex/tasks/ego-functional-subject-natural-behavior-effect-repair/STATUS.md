# Status

## Current

`accepted_local`

## Notes

- #94 v2 real-provider run produced valid OpenRouter transcript evidence, but WSL GPT-5.5 judge still returned `partial`.
- The blocker is natural behavior effect: `fs_18` generic companionship, `fs_08` broad destructive proposal, and recurrence/preference evidence that previously proved injection more than substantive reply change.
- This task repairs those behavior-effect surfaces without closing the parent real-provider smoke gate.
- Evidence packet: `docs/codex/tasks/ego-functional-subject-natural-behavior-effect-repair/EVIDENCE.natural_behavior_effect.json`

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py scripts/run_ego_experience_trial.py EgoOperator/tests/test_permission_gates.py EgoOperator/tests/test_operator_runtime_contract.py scripts/tests/test_run_ego_experience_trial.py`
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_permission_gates.py::test_windows_chained_destructive_cleanup_requires_inventory_first EgoOperator/tests/test_operator_runtime_contract.py::test_failure_recovery_request_rewrites_generic_companion_reply_into_recovery_plan scripts/tests/test_run_ego_experience_trial.py::test_functional_subject_trial_includes_recurrence_preference_evidence -q`
- `python3 scripts/run_ego_experience_trial.py --functional-subject-trial --case-limit 20 --out /tmp/ego_fs_025_target`
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests scripts/tests/test_run_ego_experience_trial.py -q`
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> `272 passed` + diff check pass
