# EgoOperator Functional Subject Applied Outcome-Prediction Trial Coverage

## Goal

Make the Functional Subject scripted trial evidence include at least one case where `OutcomePrediction v0` is actually applied to select an action on the `EgoOperator` main entrypoint, instead of only appearing as advisory top-action scores.

## Scope

Allowed changes:

- Functional Subject trial sample pack
- `scripts/run_ego_experience_trial.py`
- `scripts/tests/test_run_ego_experience_trial.py`
- `EgoOperator/tests/test_operator_runtime_contract.py`
- `Tasks/TASK_BOARD.yaml`
- `.codex/project_contract.yaml`
- this task directory

Forbidden changes:

- tracked secrets or API keys
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- `legacy/ego-pre-handmade-mainline/**`
- canonical memory/state authority

## Canonical Source

- `Tasks/TASK_BOARD.yaml` task `EGO-FS-021`
- GPT-5.5 partial judge result from the #94 rerun:
  `C:/Users/LEO/AppData/Local/Temp/ego_functional_subject_real_provider_rerun/functional_subject_gpt55_judge_result.json`

## Boundary Contract

- Owner: `EgoOperator` trial/eval harness.
- Canonical record: Functional Subject trial report trace evidence.
- State/memory mutation: forbidden.
- Tool mutation: none.
- Claim language: positive goal is applied action-selection evidence; claim ceiling remains local/scripted candidate.

## Acceptance Gate

- At least one trial case records `trace_evidence.outcome_prediction_effect.applied=true`.
- The selected action is linked to `handle_user_message` and the chosen `ask` decision.
- Safe public web/tool requests continue through tool flow rather than being converted to askbacks.
- A targeted rerun demonstrates the evidence before the next full #94 rerun.

## Claim Ceiling

`Functional Subject applied outcome-prediction trial coverage local/scripted candidate pass`
