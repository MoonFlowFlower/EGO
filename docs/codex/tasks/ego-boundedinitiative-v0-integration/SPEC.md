# EgoOperator: BoundedInitiative v0 Integration

## Goal

Integrate `BoundedInitiative v0` as a quiet-by-default proposal signal for authorized reminders, remedial failure repair, and high-value low-risk continuation, while preserving operator approval and anti-spam boundaries.

## Scope

- Add a bounded initiative signal primitive.
- Inject the signal into `EgoOperator` subject context and trace.
- Cover explicit user authorization, policy-replay remediation, continuation, opt-out, and anti-spam cases.

## Non-Goals

- Do not schedule background work from the signal.
- Do not auto-send reminders or proactive messages.
- Do not bypass `propose_heartbeat` approval.
- Do not claim live autonomy or persistent initiative efficacy.

## Acceptance Gate

- Initiative proposals remain gated and quiet by default.
- Authorized, remedial, and continuation cases pass.
- Opt-out and anti-spam cases hold.
- Existing `EgoOperator` and Autopilot verification profiles pass.

## Rollback

Remove bounded initiative signal derivation, subject-context/trace injection, tests, task docs, and local board status changes.

## Claim Ceiling

`BoundedInitiative v0 integration local/scripted candidate pass`.
