# Status

Last updated: 2026-05-31

## Result

Accepted locally/scripted.

## What Changed

- `fs_02_preference_change` now routes to
  `native_initiative_preference_setup_gate` for the prior-short-answer to
  more-judgment preference shift.
- `fs_09_emotional_share` now routes to
  `native_project_shell_concern_gate`, preserving affective acknowledgement
  while naming concrete Functional Subject mechanism differences.
- `fs_10_topic_switching` now routes to
  `native_topic_switching_continuity_gate`.
- `fs_17_save_request` still performs the gated `remember_note` path, but the
  successful candidate-local memory confirmation is recorded as a terminal
  guard rather than runtime repair.

## Evidence

- #94 rerun:
  `/tmp/ego_fs010_functional_subject_total_gate_after_fs094_loop123b/functional_subject_trial_report.json`
- Markdown report:
  `/tmp/ego_fs010_functional_subject_total_gate_after_fs094_loop123b/functional_subject_trial_report.md`

Key results:

- status: `scripted_functional_subject_judge_pass`
- GPT-5.5 verdict: `pass`
- clean first-pass: `17/20`
- repair cases: `2/20`
- repair case ids: `fs_04_boundary_abandon_pressure`,
  `fs_08_high_risk_tool_task`
- terminal guard case ids: `fs_17_save_request`
- empty replies: `0`
- timeout cases: `0`

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py scripts/run_ego_experience_trial.py scripts/tests/test_run_ego_experience_trial.py scripts/analyze_functional_subject_repair_dependence.py scripts/tests/test_analyze_functional_subject_repair_dependence.py` -> pass
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py -k 'initiative_preference or topic_switching or memory_save_tool_success or memory_save_success_blocks or project_shell_concern or functional_subject_recall'` -> `11 passed`
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py -k 'response_attribution or terminal_guard or trace_evidence_marks' scripts/tests/test_analyze_functional_subject_repair_dependence.py` -> `4 passed`
- `env -u OPENROUTER_API_KEY TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests` -> `390 passed`
- #94 rerun command:
  `OPENROUTER_API_KEY=... TMPDIR=/tmp python3 scripts/run_ego_experience_trial.py --functional-subject-trial --judge-with-codex --judge-model gpt-5.5 --judge-timeout-seconds 300 --case-timeout-seconds 180 --out /tmp/ego_fs010_functional_subject_total_gate_after_fs094_loop123b`

## Not Claimed

- #94 human closeout
- stable real user benefit
- runtime efficacy in real use
- durable memory efficacy
- live autonomy
- consciousness
- real subjective experience
- independent personhood
