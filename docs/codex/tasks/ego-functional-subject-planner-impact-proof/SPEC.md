# EgoOperator Viability/Outcome Prediction Behavior-Impact Proof

## Goal

Prove that `ViabilityState v0` / `OutcomePrediction v0` can materially influence the real `EgoOperator` message-handling path by changing action selection when uncertainty and misunderstanding signals make direct answering less viable.

## Scope

Allowed changes:

- `EgoOperator/agent_base.py`
- `EgoOperator/tests/test_operator_runtime_contract.py`
- `scripts/run_ego_experience_trial.py`
- `scripts/tests/test_run_ego_experience_trial.py`
- `Tasks/TASK_BOARD.yaml`
- `.codex/project_contract.yaml`
- this task directory

Forbidden changes:

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- `legacy/ego-pre-handmade-mainline/**`
- canonical memory/state authority

## Canonical Source

- `Tasks/TASK_BOARD.yaml` task `EGO-FS-019`
- `/tmp/ego_functional_subject_real_provider_rerun_20260521b/gpt55_judge_result.json`

## Boundary Contract

- Owner: `EgoOperator` runtime.
- Canonical record: trace JSONL and scripted trial evidence packet.
- State/memory mutation: forbidden; this task only consumes candidate subject context.
- Tool mutation: none.
- Rollback: remove the outcome-prediction action-selection gate and its evidence fields/tests.

## Mainline E2E

`user message -> build_subject_context -> OutcomePrediction selected action -> runtime gate -> trace -> trial evidence packet`

The proof must touch `AgentRuntime.handle_user_message`, not only the fallback `Planner.propose` path.

## Acceptance Gate

- At least one scripted case changes selected action due to viability/outcome prediction.
- Trace links the selected action to `outcome_prediction_effect`.
- Evidence packet exposes the outcome prediction effect without treating it as canonical subject state.

## Claim Ceiling

`Functional Subject planner-impact local/scripted candidate pass`
