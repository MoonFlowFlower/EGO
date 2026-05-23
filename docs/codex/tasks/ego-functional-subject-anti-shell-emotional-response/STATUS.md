# Status

Status: accepted

## Decisions

- Treat “ordinary chat shell” concern as an emotional + mechanism alignment gate, not as a pure comfort request.
- Keep the response positive: state the selfhood mechanism and its falsification signal, rather than framing the task around no-consciousness claims.

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py` -> pass
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py::test_memory_language_fallback_preserves_project_shell_concern EgoOperator/tests/test_operator_runtime_contract.py::test_project_shell_concern_generic_comfort_falls_back_to_mechanism_gate` -> 2 passed
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests` -> 219 passed
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass, 304 passed
- `git diff --check -- EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py Tasks/TASK_BOARD.yaml docs/codex/tasks/ego-functional-subject-anti-shell-emotional-response` -> pass
- Real-provider scripted rerun: `/tmp/ego_fs_010_after_fs040_20260523_104348/functional_subject_trial_report.json` -> `scripted_functional_subject_judge_partial`, 20 cases, 0 timeouts; `fs_09` now ties the concern to emotional attunement, relationship continuity, initiative, feedback learning, trace, and falsification.

## Remaining Risk

This is local/scripted output-guard evidence. It does not prove the companion experience is stable across real sessions. Latest GPT-5.5 judge still marks the parent smoke partial, with remaining blockers around `fs_16` forget/revoke provider recovery, first-pass-vs-repair strength, and longitudinal/non-scripted evidence.
