# EgoOperator OutcomePrediction Applied-Action Expansion

## Goal

Expand OutcomePrediction from an ask-only planner influence into a bounded action-selection primitive that can choose trace-visible `suggest` and `repair/checkpoint` responses when ViabilityState provides clear initiative, failure, or safety signals.

This task is about making the Functional Subject mechanism affect the transcript more often, not about adding autonomy, memory authority, or direct tool execution.

## Source

- EGO-FS-045 scorecard real-provider rerun.
- `/tmp/ego_fs_010_scorecard_rerun_20260523_121618/functional_subject_trial_report.json`
- GPT-5.5 judge follow-up: strengthen applied OutcomePrediction so trace-selected actions drive more cases, not only context.

## Stage Card

### Boundary Contract

- Owner: `EgoOperator` runtime candidate.
- Change surface: `EgoOperator/primitives/subject_context.py`, `EgoOperator/agent_base.py`, targeted tests, local task metadata.
- Canonical record: `Tasks/TASK_BOARD.yaml` plus this task evidence file.
- Allowed mutation: advisory planner selection and trace metadata.
- Forbidden mutation: core memory writes, program state, evidence ledger, legacy code, direct tool execution, approval bypass.
- Rollback: revert the OutcomePrediction selected-action expansion and task metadata.

### Mainline E2E

`user text -> SubjectContext/ViabilityState -> OutcomePredictions -> AgentRuntime._action_from_outcome_prediction -> gate.check -> trace -> Functional Subject trial report`

The selected action must remain a normal `AgentAction` that goes through the existing runtime gate. It may return a bounded response, but it must not execute tools or mutate state.

### Evidence Report

Closeout evidence must record:

- deterministic tests for `ask`, `suggest`, and `repair/checkpoint`
- trace `outcome_prediction_effect.applied=true`
- selected action type and reason
- whether Functional Subject reports show more than one applied OutcomePrediction case
- remaining GPT-5.5/human evidence gap

## Acceptance Gate

- OutcomePrediction can select at least `suggest` and `repair/checkpoint` actions when ViabilityState provides clear initiative, failure, or safety signals.
- Selected actions remain advisory/runtime responses only; they do not execute tools, mutate memory/state, or bypass approval gates.
- Trace records `outcome_prediction_effect` with `applied=true`, `decision`, `reason`, selected prediction, and viability scores.
- Functional Subject report/eval can show more than one applied OutcomePrediction case.
- Existing EgoOperator and Autopilot regression profiles do not regress.

## Not In Scope

- No new memory authority.
- No tool execution or automatic approval.
- No GitHub Project mutation.
- No `docs/PROGRAM_STATE_UNIFIED.yaml` or evidence ledger changes.
- No claim that Functional Subject is complete.

## Rollback

Revert OutcomePrediction action-selection expansion and keep EGO-FS-010 blocked on `planner_trace_not_transcript_visible` / first-pass strength.

## Claim Ceiling

`Functional Subject OutcomePrediction applied-action local candidate pass`
