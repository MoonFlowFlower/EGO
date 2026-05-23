# EgoOperator Functional Subject Direct Trace Evidence Packet

## Goal

Add direct trace evidence packets to the Functional Subject trial report so memory, approval, and replay claims are backed by concrete record/proposal/replay identifiers instead of summary booleans alone.

This is a positive evidence mechanism: make Functional Subject behavior auditable and replay-friendly before raising any parent gate.

## Source

- EGO-FS-049 GPT-5.5 judge partial verdict.
- Missing evidence: direct trace excerpts proving actual memory record IDs, approval transitions, replay activation, and side-effect boundaries.

## Stage Card

### Boundary Contract

- Owner: Functional Subject eval harness.
- Change surface: `scripts/run_ego_experience_trial.py`, tests, task docs/board.
- Allowed mutation: report/judge-packet schema extension only.
- Forbidden mutation: EgoOperator runtime behavior, memory authority, program state, evidence ledger, legacy code, GitHub Project.

### Mainline E2E

`run_ego_experience_trial.py -> memory_lifecycle_evidence / approval_lifecycle_evidence / recurrence_preference_evidence -> gpt55_judge_packet`

The judge packet must receive direct record/proposal/replay identifiers and side-effect boundary fields.

### Evidence Report

Closeout evidence must record:

- direct memory record IDs and lifecycle transitions
- approval proposal id, lease id, payload hash, execution status, pending counts
- policy replay trigger signatures and bounded initiative counts
- preference save key/scope and repeated context injection
- local verification commands

## Acceptance Gate

- Report includes `direct_trace_evidence` for memory lifecycle, approval lifecycle, and recurrence/preference evidence.
- GPT-5.5 judge packet includes those direct evidence fields.
- Existing lifecycle evidence tests assert the new direct evidence fields.
- Functional Subject trial and Autopilot regression profiles do not regress.

## Not In Scope

- No runtime behavior change.
- No negative baseline implementation.
- No real-provider rerun in this task.
- No program state/evidence ledger update.

## Rollback

Remove `direct_trace_evidence` fields and keep EGO-FS-010 partial on traceability evidence.

## Claim Ceiling

`Functional Subject direct trace evidence packet local workflow pass`
