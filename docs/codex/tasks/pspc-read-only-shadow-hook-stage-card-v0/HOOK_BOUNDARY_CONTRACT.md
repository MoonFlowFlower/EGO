# PSPC Read-Only Shadow Hook Boundary Contract v0

Claim ceiling: `lab_only_proto_self_mechanism_candidate / shadow_hook_stage_card_only`

## Scope

This contract defines the allowed boundary for a future disabled PSPC shadow hook. It does not implement that hook and does not authorize runtime registration.

## Mandatory Defaults

- `enabled=false`
- `mainline_connected=false`
- `runtime_authority=none`
- `mode=shadow_audit_only`
- `side_effects_allowed=false`

## Allowed Future Inputs

A future hook may read only:

- EgoOperator audit/trace context explicitly passed into a test harness or approved shadow hook boundary
- PSPC `audit_candidate`
- PSPC fixture/static/dry-run evidence refs
- immutable configuration flags proving disabled/default-off state

## Allowed Future Output

A future hook may output only:

- shadow audit artifact
- audit metadata
- non-executable observation summary
- trace refs
- validation status

The output must not be consumed as a proposal, plan, action, approval, gate decision, memory patch, user message, transport payload, or proactive trigger.

## Forbidden Mutations

The future hook must not change:

- EgoOperator proposal
- EgoOperator plan
- approval state
- gate decision
- user response
- memory
- transport
- proactive state
- runtime registry
- claim ceiling

## Forbidden Calls

The future hook must not call:

- runtime gate
- memory writer
- approval executor
- transport sender
- proactive scheduler
- PSPC planner
- PSPC model training
- user-message renderer
- runtime registration

## Failure Meaning

If a future implementation needs any forbidden call or mutation to be useful, the correct verdict is `no_go_keep_lab_only`, not scope expansion inside the implementation.

## What This Proves

This proves the future hook boundary is documented before implementation and can be reviewed against a fixed no-authority contract.

## What This Does Not Prove

It does not prove hook implementation safety, runtime integration safety, real trace compatibility, adapter readiness, EgoOperator runtime efficacy, stable real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Rollback

Delete this task directory, `artifacts/pspc_read_only_shadow_hook_stage_card_v0/`, and matching governance/ledger/generated-view entries.
