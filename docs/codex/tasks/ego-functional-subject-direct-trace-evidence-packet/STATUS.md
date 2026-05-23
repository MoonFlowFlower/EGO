# Status

Status: accepted

## Decisions

- Keep this as an eval-harness evidence task, not a runtime behavior task.
- Add direct identifiers to existing lifecycle evidence surfaces instead of creating a second report format.
- Preserve current claim ceiling; direct trace evidence improves auditability, not durable efficacy.

## Verification

- `python3 -m py_compile scripts/run_ego_experience_trial.py scripts/tests/test_run_ego_experience_trial.py` -> pass.
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py` -> pass, `29 passed`.
- `python3 scripts/run_ego_experience_trial.py --functional-subject-trial --case-limit 20 --out /tmp/ego_fs050_direct_trace_smoke_final` -> pass as local scripted smoke; report and judge packet include direct evidence.
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass, `318 passed` and scoped diff check pass.

## Evidence

- `EVIDENCE.direct_trace_evidence_packet.json`
- `/tmp/ego_fs050_direct_trace_smoke_final/functional_subject_trial_report.json`
- `/tmp/ego_fs050_direct_trace_smoke_final/functional_subject_trial_report.md`

## Remaining Risk

Direct trace evidence can make the scripted report more auditable, but it does not replace baseline negative controls, restart durability, or human smoke evidence.
