# EgoOperator: OutcomePredictor v0 Trace-Based Planner Input

## Goal

Add `OutcomePredictor v0` as a bounded planner-input mechanism that scores likely outcomes for reply, ask, wait, repair, suggest, tool proposal, memory candidate, and no-action options from the current subject and viability signals.

## Scope

- Build a candidate outcome prediction set from `ViabilityState v0` and `SubjectState v0`.
- Render the prediction set into the subject-context prompt and trace.
- Allow fallback planning to use a high-confidence `ask` prediction to avoid premature direct replies.
- Record which prediction affected the fallback action choice.

## Non-Goals

- Do not make outcome prediction execute tools, approve operations, or mutate state.
- Do not replace the main LLM tool loop.
- Do not add keyword-first semantic routing or template fallback.
- Do not modify legacy projects, program state, or evidence ledger.

## Acceptance Gate

- Planner input includes outcome scores.
- Trace shows which prediction affected action/proposal choice.
- A deterministic case proves prediction changes a decision versus baseline.
- Existing `EgoOperator` and Autopilot verification profiles pass.

## Rollback

Remove `build_outcome_predictions_v0()`, prediction prompt/trace fields, fallback planner bias, tests, task docs, and local board status changes.

## Claim Ceiling

`OutcomePredictor v0 planner-input local candidate pass`.
