# EgoOperator: PolicyPatchCandidate and Replay Learning Loop

## Goal

Add a session-local `PolicyPatchCandidate` mechanism that turns repeated same-class failures into replayable strategy candidates, so later comparable turns can change strategy through prompt/trace context without mutating canonical memory or state.

## Scope

- Detect repeatable failure signatures from runtime outcomes.
- Emit a candidate after repeated same-class failures.
- Replay matching candidates into `SubjectState v0` on later comparable turns.
- Record emission and replay in trace.
- Add a scripted deterministic repeated-failure test.

## Non-Goals

- Do not write policy candidates to core memory, operator memory, program state, evidence ledger, or task board.
- Do not auto-promote policy patches to canonical behavior.
- Do not run background learning or unbounded retry loops.
- Do not modify legacy projects.

## Acceptance Gate

- Repeated-failure scripted case produces a policy candidate.
- Later same-class case shows changed strategy in trace.
- Policy candidates do not directly mutate canonical state.
- Existing `EgoOperator` and Autopilot verification profiles pass.

## Rollback

Remove session-local policy candidate storage, feedback classification, replay injection, tests, task docs, and local board status changes.

## Claim Ceiling

`PolicyPatchCandidate replay-learning local/scripted candidate pass`.
