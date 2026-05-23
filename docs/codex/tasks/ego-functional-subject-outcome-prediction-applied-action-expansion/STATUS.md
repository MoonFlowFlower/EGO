# Status

Status: accepted

## Decisions

- Treat OutcomePrediction as an advisory planner selector, not as a second policy engine.
- Let it choose bounded `suggest` / `repair` response actions only when ViabilityState provides clear signals.
- Preserve existing tool, memory, permission, and trace gates.

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py EgoOperator/primitives/subject_context.py EgoOperator/tests/test_operator_runtime_contract.py` -> pass
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py -k "outcome_prediction or viability_outcome"` -> 5 passed
- `TMPDIR=/tmp python3 -m pytest -q scripts/tests/test_run_ego_experience_trial.py -k "response_attribution or records_applied_outcome_prediction_effect"` -> 2 passed
- `python3 scripts/run_ego_experience_trial.py --functional-subject-trial --case-limit 20 --out /tmp/ego_fs046_local_trial_smoke3` -> pass, provider unavailable/NoLLM local smoke
- Local scorecard: clean first-pass 12/20, outcome_prediction_gate 6/20, runtime_repair 8/20
- Applied OutcomePrediction cases: `fs_07`, `fs_08`, `fs_12`, `fs_13`, `fs_18`, `fs_20`

## Remaining Risk

This can improve transcript-visible planner influence, but it does not by itself prove clean first-pass behavior across real-provider runs or close EGO-FS-010.

EGO-FS-010 remains blocked on real-provider/GPT-5.5/human evidence.
