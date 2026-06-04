# PSPC Runtime-Adjacent Shadow Review v0

## Problem Reframe

PSPC is not being connected to EgoOperator in this stage. The real question is whether existing PSPC audit-only evidence can move one step closer to EgoOperator runtime contracts without becoming action authority, proposal execution, memory mutation, gate input, transport output, or user-visible behavior.

This stage is a design review package only. It may approve PSPC-SHADOW-002, a fixture-boundary task, or reject the path and keep PSPC artifact-only.

## Stage Boundary

- lane: pspc_runtime_adjacent_shadow
- stage: runtime_adjacent_shadow_review_only
- runtime authority: none
- mainline_connected: false
- enabled: false
- EgoOperator integration: forbidden in this stage
- runtime import or registry: forbidden
- memory write: forbidden
- gate invocation: forbidden
- user-visible output: forbidden
- direct action: forbidden
- transport or proactive channel: forbidden
- planner, training, or model execution: forbidden
- claim ceiling: lab_only_proto_self_mechanism_candidate / runtime_adjacent_shadow_review_only

## One Hypothesis

If PSPC remains disabled, mainline-disconnected, audit-only, and unregistered, then the next safe evidence step is not runtime integration. The next safe step is a fixture-boundary task that checks whether a PSPC audit candidate can be represented beside an EgoOperator-like trace fixture without side effects.

## One Change Surface

Allowed change surface for this stage:

- docs/codex/tasks/pspc-runtime-adjacent-shadow-review-v0/
- Tasks/TASK_BOARD.yaml status update for PSPC-SHADOW-001 and PSPC-SHADOW-002

Forbidden change surface for this stage:

- EgoOperator main loop
- EgoOperator runtime registry
- EgoOperator gates
- EgoOperator memory
- EgoOperator approval flow
- EgoOperator human-trial harness
- EgoOperator transport or proactive channels
- PSPC planner, training, or model execution

## Authority Source

- docs/PROGRAM_STATE_UNIFIED.yaml remains the repo authority.
- Tasks/TASK_BOARD.yaml is the local task-board authority.
- Existing PSPC shadow evidence remains bounded to lab-only or artifact-only review packages.
- GitHub Project is mirror-only and unavailable while gh is not on PATH.

## What Can Change

- A review package can be created for PSPC-SHADOW-001.
- The task board can mark PSPC-SHADOW-001 accepted and PSPC-SHADOW-002 active after verification.
- The next allowed task can be named as PSPC-SHADOW-002 only.

## What Cannot Be Proven

This stage cannot prove adapter readiness, runtime integration safety, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, subjective experience, or that PSPC can affect real user responses.

## Three-Level Verify

1. Contract check: Review docs freeze disabled, mainline-disconnected, audit-only status and forbidden runtime surfaces.
2. Static boundary check: Scan EgoOperator runtime sources to confirm PSPC remains unregistered and unimported.
3. Autopilot check: Confirm plan-next moves from PSPC-SHADOW-001 to PSPC-SHADOW-002 after board status update.

## Rollback

Delete docs/codex/tasks/pspc-runtime-adjacent-shadow-review-v0/ and revert the PSPC-SHADOW-001/002 task-board status update. PSPC returns to recorded/offline shadow evidence only.

## Claim Ceiling

lab_only_proto_self_mechanism_candidate / runtime_adjacent_shadow_review_only
