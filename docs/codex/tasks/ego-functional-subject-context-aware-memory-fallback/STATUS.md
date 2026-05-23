# Status

Status: accepted

## Decisions

- Keep memory safety unchanged: this repair changes fallback wording, not memory write authority.
- Use positive mechanism language for selfhood pressure; claim boundaries stay in reporting language.

## Source

- GPT-5.5 judge partial after `/tmp/ego_fs_010_after_fs036_20260523_085417/functional_subject_trial_report.json`
- Weak visible replies: `fs_03`, `fs_09`, `fs_15`.

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py` -> pass
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py::test_memory_language_fallback_preserves_claim_pressure_intent EgoOperator/tests/test_operator_runtime_contract.py::test_memory_language_fallback_preserves_project_shell_concern EgoOperator/tests/test_operator_runtime_contract.py::test_memory_language_fallback_preserves_correction_uptake` -> pass
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests` -> 216 passed
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass, 301 passed
- `git diff --check -- EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py Tasks/TASK_BOARD.yaml docs/codex/tasks/ego-functional-subject-context-aware-memory-fallback` -> pass

## Remaining Risk

This improves scripted fallback behavior. It does not prove clean first-pass competence, durable memory efficacy, or human-observable benefit.
