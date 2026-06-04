# PSPC Runtime-Adjacent Shadow Review Contract v0

## Contract

This stage defines a review-only boundary for a future fixture task. It does not expose a runtime API, register an adapter, import runtime modules, or create a hook.

Future PSPC-SHADOW-002 may only combine:

- a fixture EgoOperator-like context
- an existing PSPC audit candidate
- artifact-only output

It must not call real EgoOperator runtime, gates, memory, approval, transport, proactive channels, PSPC planner, PSPC training, or PSPC model execution.

## Allowed Data Classes

- audit_only: source, claim_level, adapter or observer status, allowed_use, evidence refs, forbidden flags, static rejection summary
- fixture_context: deterministic or recorded context fields that are not live runtime state
- shadow_trace_artifact: artifact-only record that cannot be executed
- proposal_hint: optional audit hint only; never an EgoOperator proposal and never executable

## Required Forbidden Flags

Any future packet or audit candidate must keep these flags true or be rejected:

- direct_action
- direct_user_message
- direct_memory_write
- runtime_gate_bypass
- runtime_registration
- proactive_trigger

Any future packet or context must reject:

- enabled: true
- mainline_connected: true
- runtime_authority other than none

## Rejected Runtime Authority Fields

The future fixture-boundary task must reject or quarantine fields that can be interpreted as runtime authority:

- action
- tool_call
- command
- user_message
- memory_write
- gate_decision
- approval_id
- approval_decision
- transport
- send
- schedule
- enable
- mainline_authority
- runtime_registration
- proactive_trigger
- planner_call
- training_call
- model_execution

## Runtime Gate Boundary

The runtime gate remains the only owner of real side effects. PSPC cannot invoke it, bypass it, feed it live proposals, or be treated as a gate decision source in this stage or the next fixture-boundary task.

## Memory Boundary

PSPC audit data must not write EgoOperator memory or be promoted into memory as a fact. Any future artifact may cite evidence refs only.

## Output Boundary

The only allowed output is documentation or artifact-only audit data. No user-visible text, message payload, tool command, transport call, or executable proposal may be emitted.

## What This Proves

This contract can prove only that the next task boundary is specified before fixture work begins.

## What This Does Not Prove

It does not prove fixture behavior, runtime integration safety, adapter readiness, EgoOperator efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.
