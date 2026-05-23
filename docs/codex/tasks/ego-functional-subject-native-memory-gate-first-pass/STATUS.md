# Status

Status: accepted

## Decisions

- Keep memory-save as the existing explicit tool/gate path; this task does not auto-write memory.
- Native first-pass only handles no-side-effect correction, forget/revoke guidance, opt-out boundary, and reminder authorization semantics.
- Use the existing `AgentAction -> gate -> trace` path so this remains mainline behavior, not a second response engine.

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py scripts/run_ego_experience_trial.py EgoOperator/tests/test_operator_runtime_contract.py scripts/tests/test_run_ego_experience_trial.py` -> pass.
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py scripts/tests/test_run_ego_experience_trial.py` -> pass, `142 passed`.
- `python3 scripts/run_ego_experience_trial.py --functional-subject-trial --case-limit 20 --out /tmp/ego_fs048_local_trial_smoke_final` -> pass as local scripted smoke; scorecard `clean_first_pass=15/20`, `native_memory_gate=4`, `runtime_repair=5`.
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass, `318 passed` and scoped diff check pass.

## Evidence

- `EVIDENCE.native_memory_gate_first_pass.json`
- `/tmp/ego_fs048_local_trial_smoke_final/functional_subject_trial_report.json`
- `/tmp/ego_fs048_local_trial_smoke_final/functional_subject_trial_report.md`

## Remaining Risk

This reduces repair dependence for explicit gate cases but does not prove durable memory efficacy or restart continuity.
EGO-FS-010 remains blocked pending later scripted real-provider / judge and human smoke evidence.
