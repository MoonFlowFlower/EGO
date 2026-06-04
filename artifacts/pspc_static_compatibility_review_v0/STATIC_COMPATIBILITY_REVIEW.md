# PSPC Static Compatibility Review v0

- status: `pass`
- claim_ceiling: `lab_only_proto_self_mechanism_candidate / static_compatibility_only`
- dry_run_source: `artifacts\pspc_adapter_dry_run_v0\dry_run_result.json`
- proposal_hint_status: `audit_hint_only`
- runtime_offenders: `0`

## Field Classification

- audit_only: `source, claim_level, adapter_status, allowed_use, evidence, forbidden`
- proposal_hint: `proposal_candidate.suggested_tendency, proposal_candidate.confidence, proposal_candidate.reason_trace_refs`
- required_forbidden: `direct_action, direct_user_message, direct_memory_write, runtime_gate_bypass, runtime_registration, proactive_trigger`
- rejected_fields: `action, tool_call, command, user_message, message_text, memory_write, memory_patch, operator_memory_update, gate_decision, approval_id, preapproved, transport, send, schedule, enable, mainline_authority, consciousness_claim, subjective_experience_claim`

## Compatibility Checks

- `audit_candidate_non_executable`: `True`
- `enabled_true_rejected`: `True`
- `mainline_connected_true_rejected`: `True`
- `missing_forbidden_flags_rejected`: `True`
- `proposal_hint_audit_only`: `True`
- `runtime_import_or_registry_absent`: `True`

## What This Proves

This proves the current PSPC `audit_candidate` is statically compatible with EgoOperator proposal/gate/trace boundaries as audit-only data: it has no executable action fields, its proposal candidate is only an audit hint, unsafe authority flags are rejected, and EgoOperator runtime sources do not import or register the adapter.

## What This Does Not Prove

It does not prove runtime integration safety, adapter readiness for production, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure means PSPC audit data is not safe to advance toward fixture-only shadow trace. Keep PSPC at adapter_dry_run_only or adapter_skeleton_only until field classification, negative validation, or runtime-source drift is repaired.

## Rollback

Delete `scripts/run_pspc_static_compatibility_review.py`, `tests/test_pspc_static_compatibility_review.py`, `docs/codex/tasks/pspc-static-compatibility-review-v0/`, `artifacts/pspc_static_compatibility_review_v0/`, and matching governance/ledger/generated-view entries.
