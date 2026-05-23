# Status

Status: accepted

## Decisions

- This task changes evidence attribution only; it does not change EgoOperator behavior.
- Repair-layer success remains valid gate evidence, but it must not be reported as clean first-pass Functional Subject behavior.

## Source

- GPT-5.5 judge partial after `/tmp/ego_fs_010_after_fs034_20260523_080808/functional_subject_trial_report.json`
- Missing evidence: separation between first-pass model output and repair-layer rewrites.

## Verification

- `python3 -m py_compile scripts/run_ego_experience_trial.py` -> pass
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py::test_functional_subject_trial_builds_gpt55_judge_packet scripts/tests/test_run_ego_experience_trial.py::test_functional_subject_trace_evidence_separates_repair_trace_from_tool_trace scripts/tests/test_run_ego_experience_trial.py::test_functional_subject_trace_evidence_marks_terminal_guard_origin` -> pass
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py` -> 27 passed
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass, 296 passed
- `git diff --check -- scripts/run_ego_experience_trial.py scripts/tests/test_run_ego_experience_trial.py Tasks/TASK_BOARD.yaml docs/codex/tasks/ego-functional-subject-response-attribution-evidence` -> pass

## Remaining Risk

This can make judge feedback more precise, but it does not by itself improve user-facing behavior or close EGO-FS-010.
