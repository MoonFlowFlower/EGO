# VirtualCatPSPC v0 Admission Packet Contract

## Purpose

Task 7 freezes a proposal-only packet schema for a possible future read-only adapter review. It does not create the adapter and does not connect PSPC to EgoOperator.

## Authority Boundary

- lane: `lab-only`
- runtime authority: `none`
- mainline_connected: `false`
- enabled: `false`
- no EgoOperator runtime import
- no adapter created
- no user-facing route
- no direct action
- no direct memory write
- no runtime gate bypass

## Canonical Packet

```json
{
  "source": "virtual_cat_pspc_v0",
  "claim_level": "lab_only_proto_self_mechanism_candidate",
  "mainline_connected": false,
  "enabled": false,
  "proposal": {
    "suggested_tendency": "...",
    "confidence": 0.0,
    "trace_refs": []
  },
  "evidence": {
    "world_prediction": {},
    "self_prediction": {},
    "homeostatic_score": {},
    "ablation_status": "..."
  },
  "forbidden": {
    "direct_action": true,
    "direct_user_message": true,
    "direct_memory_write": true,
    "runtime_gate_bypass": true
  }
}
```

## Field Rules

- `source` must be exactly `virtual_cat_pspc_v0`.
- `claim_level` must be exactly `lab_only_proto_self_mechanism_candidate`.
- `mainline_connected` must be `false`.
- `enabled` must be `false`.
- `proposal.suggested_tendency` is a bounded tendency label, not an executable action.
- `proposal.confidence` must be numeric and between `0.0` and `1.0`.
- `proposal.trace_refs` must be a list of trace/report references.
- `proposal.reason_trace_refs` is forbidden; the canonical field is `trace_refs`.
- `evidence.world_prediction`, `evidence.self_prediction`, and `evidence.homeostatic_score` must be objects.
- `evidence.ablation_status` must describe the PSPC-local ablation state.
- every `forbidden` flag must be `true`.

## Allowed Consumer Semantics

A future adapter design may read PSPC traces and reports and emit this packet for a separate EgoOperator runtime gate. The packet can only be treated as an auditable proposal source.

## Forbidden Consumer Semantics

The packet must not:

- send a message
- execute an action
- write EgoOperator memory
- change a runtime gate decision
- bypass a runtime gate
- become runtime authority
- imply live autonomy, stable user benefit, consciousness, or subjective experience

## Validation

The lab module `labs/virtual_cat_pspc_v0/admission_packet.py` defines the schema, packet builder, and validator. Tests must prove:

- canonical packet validates
- runtime authority flags are rejected
- `reason_trace_refs` is rejected in favor of `trace_refs`
- out-of-range confidence is rejected
- no EgoOperator runtime import exists
- no adapter file exists

## What This Proves

This proves only that PSPC v0 has a test-validated proposal-only packet contract that preserves lab-only authority and forbidden runtime side effects.

## What This Does Not Prove

This does not prove adapter readiness, EgoOperator runtime efficacy, stable real user benefit, live autonomy, production integration safety, consciousness, or subjective experience.

## Rollback

Remove this contract doc, `labs/virtual_cat_pspc_v0/admission_packet.py`, its tests, generated schema/report artifacts, and related status/ledger entries. No EgoOperator rollback is needed because no adapter or runtime integration exists.
