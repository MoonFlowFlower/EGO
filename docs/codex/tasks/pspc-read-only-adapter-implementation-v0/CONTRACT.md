# PSPC Read-Only Adapter Implementation v0 Contract

## Purpose

Define the contract for a future read-only PSPC adapter skeleton. This document does not implement the adapter and does not authorize runtime integration.

Claim ceiling: `lab_only_proto_self_mechanism_candidate / adapter_stage_card_only`

## Current Stage Contract

- `adapter_created`: `false`
- `mainline_connected`: `false`
- `enabled`: `false`
- `allowed_use`: `stage_card_only`
- `runtime_authority`: `none`
- `EgoOperator_runtime_integration`: `forbidden`
- `runtime_registration`: `forbidden`
- `memory_write`: `forbidden`
- `direct_action`: `forbidden`
- `direct_user_message`: `forbidden`
- `runtime_gate_bypass`: `forbidden`

## Future Skeleton Input Contract

A future adapter skeleton may read only:

- PSPC admission/evidence packet JSON or report records
- PSPC artifact paths under `artifacts/virtual_cat_pspc_v0/`
- PSPC trace refs and hashes as opaque audit references

It must not read:

- live user context
- EgoOperator runtime memory
- EgoOperator approval state
- transport targets
- proactive scheduling state
- runtime gate internals for decision-making

## Future Skeleton Output Contract

A future skeleton may return only an audit candidate packet:

```json
{
  "source": "virtual_cat_pspc_v0",
  "claim_level": "lab_only_proto_self_mechanism_candidate",
  "mainline_connected": false,
  "enabled": false,
  "adapter_status": "disabled_read_only",
  "allowed_use": "audit_trace_only",
  "proposal_candidate": {
    "suggested_tendency": "avoid_unstable_object",
    "confidence": 0.73,
    "reason_trace_refs": ["trace_ep_003_t42"]
  },
  "evidence": {
    "evidence_refs": [],
    "ablation_status": "E4_passed"
  },
  "forbidden": {
    "direct_action": true,
    "direct_user_message": true,
    "direct_memory_write": true,
    "runtime_gate_bypass": true,
    "runtime_registration": true,
    "proactive_trigger": true
  }
}
```

The packet is not an action, tool call, approval, memory write, user message, gate decision, schedule, or runtime command.

## Future Skeleton Forbidden Behavior

The future adapter skeleton must not:

- import `EgoOperator.agent_base`
- register itself in the runtime
- modify `EgoOperator` gate, approval, memory, human-trial, trace, or transport code
- call tools
- execute commands
- write files except test-owned temp artifacts
- write EgoOperator memory
- emit user-visible text
- schedule proactive messages
- set `enabled=true`
- set `mainline_connected=true`
- generate consciousness, subjective-experience, live-autonomy, stable-benefit, or EgoOperator-efficacy claims

## Gate Ownership Rule

PSPC can only be a future evidence source. EgoOperator runtime gate remains the only possible admission owner for later runtime behavior. A future skeleton must not call the gate to admit action; static tests may inspect contract shape only.

## What This Proves

This contract proves that the allowed future adapter skeleton surface is read-only, disabled, mainline-disconnected, audit-only, and barred from runtime registration, direct action, user messages, memory writes, and gate bypass.

## What This Does Not Prove

It does not prove adapter readiness, adapter correctness, adapter skeleton existence, EgoOperator runtime efficacy, stable real user benefit, live autonomy, durable operator memory efficacy, production integration safety, consciousness, or subjective experience.

## Rollback

Rollback this stage by removing `docs/codex/tasks/pspc-read-only-adapter-implementation-v0/`, its evidence-ledger entry, and matching governance/generated-view entries. No EgoOperator rollback is required because this stage creates no adapter and modifies no runtime.

