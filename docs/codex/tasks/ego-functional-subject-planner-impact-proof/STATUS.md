# Status

## Current

`accepted_local`

## Notes

- This task repairs `EGO-FS-019`.
- The outcome prediction effect remains candidate-local and traceable.
- The runtime gate still admits the selected action; the prediction does not bypass gate semantics.

## Completed

- Added a real-entry `handle_user_message` outcome-prediction gate for high-confidence `ask` selections.
- Added trace/external metadata for `outcome_prediction_effect`.
- Added scripted trial evidence extraction for the applied prediction effect.
- Added deterministic tests proving action selection changes before LLM chat and the evidence packet records the effect.

## Verification

- `python3 -m py_compile EgoOperator/agent_base.py EgoOperator/tests/test_operator_runtime_contract.py scripts/run_ego_experience_trial.py scripts/tests/test_run_ego_experience_trial.py` -> pass
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py::test_viability_outcome_prediction_changes_mainline_action_selection_and_trace scripts/tests/test_run_ego_experience_trial.py::test_functional_subject_trace_evidence_separates_repair_trace_from_tool_trace -q` -> pass
- `TMPDIR=/tmp python3 -m pytest -q EgoOperator/tests/test_operator_runtime_contract.py scripts/tests/test_run_ego_experience_trial.py -q` -> pass
- `python3 scripts/codex_project_autopilot.py verify-profile --profile autopilot_full` -> pass, 265 tests + diff check
