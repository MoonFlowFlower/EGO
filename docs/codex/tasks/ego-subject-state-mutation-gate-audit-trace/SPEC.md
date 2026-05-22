# EgoOperator: Subject State Mutation Gate and Audit Trace

## Goal

Define and enforce a v0 gate for subject-state, memory, relationship, and policy candidates so candidate writes require explicit decisions and leave replayable audit evidence.

## Scope

- Add subject-state mutation proposal and decision records.
- Block direct LLM-output mutation requests.
- Add runtime helpers to record explicit decisions.
- Write audit trace rows with proposal, decision, owner, target record, and rollback guidance.

## Non-Goals

- Do not promote any candidate into canonical memory/state in v0.
- Do not change `remember_note`, `/remember`, or existing operator memory gates.
- Do not modify program state or evidence ledger.
- Do not add a public tool for LLM self-approval.

## Acceptance Gate

- Candidate writes require explicit gate decisions.
- Trace includes proposal, decision, owner, target record, and rollback guidance.
- LLM output cannot directly mutate canonical memory/state.
- Existing `EgoOperator` and Autopilot verification profiles pass.

## Rollback

Remove mutation proposal/decision helpers, runtime audit wiring, tests, task docs, and local board status changes.

## Claim Ceiling

`Subject-state mutation gate local candidate pass`.
