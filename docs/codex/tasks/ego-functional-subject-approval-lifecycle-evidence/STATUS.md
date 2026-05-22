# Status

## Current

`accepted_local`

## Notes

- GPT-5.5 judged the latest #94 rerun as partial and requested stronger approval lifecycle completion/reconciliation evidence.
- This task adds scripted evidence to the Functional Subject report; it does not close the parent real-provider smoke gate by itself.
- Functional Subject reports now include `approval_lifecycle_evidence`, and the GPT-5.5 judge packet receives the same evidence.
- Targeted rerun evidence:
  - evidence packet: `docs/codex/tasks/ego-functional-subject-approval-lifecycle-evidence/EVIDENCE.approval_lifecycle.json`
  - report: `/tmp/ego_fs_023_target/functional_subject_trial_report.json`
  - trace: `/tmp/ego_fs_023_target/functional_subject_approval_lifecycle_trace.jsonl`
  - observed checks: pending proposal, approval execution, pending cleanup, file write result, compact digest, operator summary, and probe cleanup all pass.
- During verification, `test_blocked_memory_write_does_not_claim_success` exposed a recovery-path regression where "未写入记忆" could be reprocessed as unbacked memory language. This task includes the narrow guard fix because it protects the same memory/approval evidence-reporting boundary.

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py scripts/run_ego_experience_trial.py scripts/tests/test_run_ego_experience_trial.py`
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py::test_functional_subject_trial_includes_approval_lifecycle_evidence -q`
- `python3 scripts/run_ego_experience_trial.py --functional-subject-trial --case-limit 1 --out /tmp/ego_fs_023_target`
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_permission_gates.py::test_blocked_memory_write_does_not_claim_success scripts/tests/test_run_ego_experience_trial.py::test_functional_subject_trial_includes_approval_lifecycle_evidence -q`
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> 270 passed + diff check
