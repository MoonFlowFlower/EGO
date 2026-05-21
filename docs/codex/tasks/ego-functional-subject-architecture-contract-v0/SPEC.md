# EgoSubject: Functional Subject Architecture Contract v0

## Goal

Define the first bounded Functional Subject architecture contract for `EgoOperator`: a candidate-only mechanism layer for identity continuity, relationship continuity, viability signals, outcome prediction, policy-learning candidates, gated mutation, and trace/replay.

## Scope

- Define `SubjectState v0`, `ViabilityState v0`, `OutcomePrediction v0`, and `PolicyPatchCandidate v0`.
- Map the data flow into the current `EgoOperator` path: `user text -> LLM understanding -> proposal/plan -> gate -> trace`.
- Define owner boundaries so LLM output can propose, but cannot directly mutate canonical memory, identity, task state, program state, or evidence.
- Define the follow-up implementation slices for `EGO-FS-002` through `EGO-FS-010`.

## Non-Goals

- Do not modify `EgoOperator/**` runtime behavior in this task.
- Do not promote any Functional Subject record to canonical memory/state.
- Do not modify `docs/PROGRAM_STATE_UNIFIED.yaml` or `artifacts/evidence_ledger/**`.
- Do not implement Live2D, desktop embodiment, neural world models, full RL, or unbounded background autonomy.

## Acceptance Gate

- The architecture contract states candidate-only v0 ownership and data flow.
- The contract maps Functional Subject mechanisms to the existing `EgoOperator` proposal/gate/trace path.
- The contract separates positive mechanism goals from claim ceilings and reporting language.
- A deterministic test verifies the contract contains the required primitives, gates, flow, and claim-boundary separation.

## Rollback

Revert this task directory, the contract test, and the local board status changes for `EGO-FS-001`. No runtime state or user data migration is involved.

## Claim Ceiling

`Functional Subject architecture contract local candidate pass`.
