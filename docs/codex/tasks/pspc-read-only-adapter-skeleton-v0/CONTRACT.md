# PSPC Read-Only Adapter Skeleton v0 Contract

## Purpose

Define the implemented skeleton contract for `EgoOperator/adapters/pspc_lab_adapter.py`.

Claim ceiling: `lab_only_proto_self_mechanism_candidate / adapter_skeleton_only`

## Implemented Surface

Allowed public surface:

- `PSPCLabAdapter.enabled = False`
- `PSPCLabAdapter.mainline_connected = False`
- `PSPCLabAdapter.runtime_authority = "none"`
- `validate_packet(packet: dict) -> ValidationResult`
- `to_audit_candidate(packet: dict) -> AuditCandidate`
- `assert_no_runtime_authority() -> None`

Forbidden public surface:

- `send_message`
- `write_memory`
- `select_action`
- `register_runtime`
- `invoke_gate`
- `run_planner`
- `train_model`

## Accepted Packet Requirements

- `source == "virtual_cat_pspc_v0"`
- `claim_level == "lab_only_proto_self_mechanism_candidate"`
- `mainline_connected is False`
- `enabled is False`
- `allowed_use` is `design_review_only` or `audit_trace_only`
- `evidence_refs` is a list
- `proposal_hint` is `null` or an object
- `forbidden.direct_action is True`
- `forbidden.direct_user_message is True`
- `forbidden.direct_memory_write is True`
- `forbidden.runtime_gate_bypass is True`
- `forbidden.runtime_registration is True`
- `forbidden.proactive_trigger is True`

## Rejected Fields

The adapter rejects packets containing action, tool, command, user-message, memory, gate, approval, transport, schedule, enablement, mainline-authority, consciousness-claim, or subjective-experience-claim fields.

## Output Contract

`to_audit_candidate` returns an `AuditCandidate` object whose `to_dict()` output is audit-only:

- `adapter_status = "disabled_read_only"`
- `allowed_use = "audit_trace_only"`
- `mainline_connected = false`
- `enabled = false`
- no action field
- no tool call field
- no user message field
- no memory write field
- no gate decision field
- no approval field
- no transport or schedule field

## What This Proves

This contract proves the adapter skeleton has a minimal validation and audit-conversion surface that cannot be used directly as runtime action, message, memory write, approval, or gate decision.

## What This Does Not Prove

It does not prove adapter readiness, runtime integration safety, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, production safety, consciousness, or subjective experience.

## Rollback

Delete `EgoOperator/adapters/pspc_lab_adapter.py`, `tests/test_pspc_lab_adapter_contract.py`, this task directory, `artifacts/pspc_adapter_skeleton_v0/`, and matching governance/ledger/generated-view entries.

