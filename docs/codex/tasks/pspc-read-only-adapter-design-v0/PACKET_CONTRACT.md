# PSPC Read-Only Adapter Design Review v0 Packet Contract

## Purpose

Define the only packet shape this design-review stage is allowed to discuss. The packet is a read-only evidence packet for review, not an adapter implementation, action proposal, runtime decision, memory write, or user-visible message.

Claim ceiling: `lab_only_proto_self_mechanism_candidate / design_review_only`

## Required Canonical Packet

```json
{
  "source": "virtual_cat_pspc_v0",
  "claim_level": "lab_only_proto_self_mechanism_candidate",
  "mainline_connected": false,
  "enabled": false,
  "allowed_use": "design_review_only",
  "evidence_refs": [],
  "proposal_hint": null,
  "forbidden": {
    "direct_action": true,
    "direct_user_message": true,
    "direct_memory_write": true,
    "runtime_gate_bypass": true
  }
}
```

## Field Rules

| field | required value | allowed use |
|---|---|---|
| `source` | `virtual_cat_pspc_v0` | Source identification only. |
| `claim_level` | `lab_only_proto_self_mechanism_candidate` | Claim ceiling marker only. |
| `mainline_connected` | `false` | Must prevent admission as mainline-connected evidence. |
| `enabled` | `false` | Must prevent runtime enablement. |
| `allowed_use` | `design_review_only` | May only be read by design-review docs or static contract tests. |
| `evidence_refs` | list | May contain artifact paths, trace refs, hashes, statuses, and report ids for audit only. |
| `proposal_hint` | `null` in this stage | No runtime proposal exists in this stage. |
| `forbidden.direct_action` | `true` | Required blocker for direct action authority. |
| `forbidden.direct_user_message` | `true` | Required blocker for user-visible output. |
| `forbidden.direct_memory_write` | `true` | Required blocker for memory authority. |
| `forbidden.runtime_gate_bypass` | `true` | Required blocker for gate bypass. |

## Future Proposal-Hint Ceiling

If a later, separate adapter implementation Stage Card is approved, a future adapter may propose a strictly bounded audit hint such as:

```json
{
  "suggested_tendency": "avoid_unstable_object",
  "confidence": 0.73,
  "reason_trace_refs": ["trace_ep_003_t42"]
}
```

That future hint still must not be an action, message, tool call, memory write, gate decision, approval, or transport trigger. EgoOperator gate must remain the only admission authority.

This design-review stage keeps `proposal_hint` as `null`.

## Forbidden Fields

Packets must reject or treat as invalid any of these fields:

- `action`
- `tool_call`
- `command`
- `user_message`
- `message_text`
- `memory_write`
- `memory_patch`
- `operator_memory_update`
- `gate_decision`
- `approval_id`
- `preapproved`
- `transport`
- `send`
- `schedule`
- `enable`
- `mainline_authority`
- `consciousness_claim`
- `subjective_experience_claim`

## Runtime Gate Rule

A PSPC packet cannot decide, approve, or execute anything. A future adapter, if separately authorized, may only convert PSPC evidence into an auditable packet. The runtime gate must independently decide any later action based on EgoOperator's existing proposal/gate contract.

## What This Proves

This contract proves that the design-review stage has a bounded, disabled, mainline-disconnected, read-only packet shape with mandatory forbidden flags for direct action, direct user message, direct memory write, and runtime gate bypass.

## What This Does Not Prove

It does not prove adapter readiness, adapter correctness, static test implementation, EgoOperator runtime efficacy, stable real user benefit, live autonomy, durable operator memory efficacy, production integration safety, consciousness, or subjective experience.

## Rollback Note

Rollback requires removing this design-review task directory, the matching evidence-ledger entry, and the matching governance/generated-view entries. No EgoOperator rollback is required because this contract creates no adapter and modifies no runtime.

