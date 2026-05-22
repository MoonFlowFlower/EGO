# Status

## Current

`accepted_local`

## Notes

- GPT-5.5 judged the latest #94 rerun as partial and requested stronger evidence for memory correction/forget/save retrieval.
- This task adds scripted evidence to the Functional Subject report; it does not close the parent real-provider smoke gate by itself.
- Functional Subject reports now include `memory_lifecycle_evidence`, and the GPT-5.5 judge packet receives the same evidence.
- Targeted rerun evidence:
  - evidence packet: `docs/codex/tasks/ego-functional-subject-memory-lifecycle-evidence/EVIDENCE.memory_lifecycle.json`
  - report: `/tmp/ego_fs_022_target/functional_subject_trial_report.json`
  - trace: `/tmp/ego_fs_022_target/functional_subject_memory_lifecycle_trace.jsonl`
  - observed checks: `/remember` save, retrieval context injection, candidate approval, correction quarantine, and `/forget` all pass.

## Verification

- `python3 -m py_compile scripts/run_ego_experience_trial.py scripts/tests/test_run_ego_experience_trial.py`
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py::test_functional_subject_trial_includes_memory_lifecycle_evidence -q`
- `python3 scripts/run_ego_experience_trial.py --functional-subject-trial --case-limit 1 --out /tmp/ego_fs_022_target`
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py EgoOperator/tests/test_memory_system.py EgoOperator/tests/test_operator_runtime_contract.py -q`
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> 269 passed + diff check
