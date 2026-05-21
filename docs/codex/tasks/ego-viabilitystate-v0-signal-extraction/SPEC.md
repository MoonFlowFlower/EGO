# EgoOperator: ViabilityState v0 Signal Extraction

## Goal

Add `ViabilityState v0` as a deterministic advisory signal layer for `EgoOperator`, estimating evidence gaps, goal stalls, safety risk, user misunderstanding, resource pressure, initiative pressure, and relationship risk before the LLM chooses a response or tool plan.

## Scope

- Implement `extract_viability_state_v0()` in `EgoOperator/primitives/subject_context.py`.
- Inject `ViabilityState v0` into the existing subject-context prompt and trace record.
- Link a compact viability summary into `SubjectState v0`.
- Add deterministic high-pressure and low-pressure tests.

## Non-Goals

- Do not let `ViabilityState v0` mutate memory, task state, program state, evidence, identity, or runtime state.
- Do not make `ViabilityState v0` decide the final reply or bypass gates.
- Do not alter command/file/web approval policy.
- Do not modify legacy projects.

## Acceptance Gate

- `ViabilityState v0` is deterministic and trace-visible.
- Signals are planner/gate inputs, not a second state authority.
- Tests cover at least one positive/high-pressure case and one hold/low-pressure case.
- Existing `EgoOperator` and Autopilot verification profiles pass.

## Rollback

Remove `extract_viability_state_v0()`, the prompt/trace fields, tests, task docs, and local board status changes.

## Claim Ceiling

`ViabilityState v0 signal extraction local candidate pass`.
