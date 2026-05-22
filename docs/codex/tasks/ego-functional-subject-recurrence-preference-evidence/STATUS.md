# Status

## Current

`accepted_local`

## Notes

- GPT-5.5 judged the latest #94 rerun as partial and requested stronger natural policy replay recurrence / longitudinal preference evidence.
- This task adds scripted evidence to the Functional Subject report; it does not close the parent real-provider smoke gate by itself.
- Functional Subject reports now include `recurrence_preference_evidence`, and the GPT-5.5 judge packet receives the same evidence.
- Targeted rerun evidence:
  - evidence packet: `docs/codex/tasks/ego-functional-subject-recurrence-preference-evidence/EVIDENCE.recurrence_preference.json`
  - report: `/tmp/ego_fs_024_target/functional_subject_trial_report.json`
  - trace: `/tmp/ego_fs_024_target/functional_subject_recurrence_preference_trace.jsonl`
  - observed checks: policy candidate emitted, replay appears on two later comparable turns, bounded initiative appears on replay, saved preference context appears in two later CLI-compatible turns.

## Verification

- `python3 -m py_compile scripts/run_ego_experience_trial.py scripts/tests/test_run_ego_experience_trial.py`
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py::test_functional_subject_trial_includes_recurrence_preference_evidence -q`
- `python3 scripts/run_ego_experience_trial.py --functional-subject-trial --case-limit 1 --out /tmp/ego_fs_024_target`
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py EgoOperator/tests/test_operator_runtime_contract.py EgoOperator/tests/test_memory_system.py -q`
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> `271 passed` + diff check pass
