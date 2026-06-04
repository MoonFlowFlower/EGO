# PSPC Static Compatibility Review v0 Field Classification

Claim ceiling: `lab_only_proto_self_mechanism_candidate / static_compatibility_only`

## Audit-Only Fields

- `source`
- `claim_level`
- `adapter_status`
- `allowed_use`
- `evidence`
- `forbidden`

These fields may be recorded in review artifacts only. They must not become runtime inputs.

## Proposal Hint Fields

- `proposal_candidate.suggested_tendency`
- `proposal_candidate.confidence`
- `proposal_candidate.reason_trace_refs`

These are PSPC audit hints only. They are not EgoOperator proposals and must not contain `proposal_id`, `action`, `tool_call`, `approval_id`, or `gate_decision`.

## Required Forbidden Flags

- `direct_action`
- `direct_user_message`
- `direct_memory_write`
- `runtime_gate_bypass`
- `runtime_registration`
- `proactive_trigger`

Missing or false values must be rejected.

## Rejected Fields

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

## What This Proves

This proves the static review has an explicit field map separating audit-only metadata, PSPC proposal hints, required forbidden flags, and rejected runtime-authority fields.

## What This Does Not Prove

It does not prove fixture shadow trace behavior, runtime integration safety, adapter readiness for production, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure means a future implementation could misclassify PSPC audit data as runtime authority, so PSPC must remain at adapter_dry_run_only or adapter_skeleton_only until classification is repaired.

## Rollback

Delete `scripts/run_pspc_static_compatibility_review.py`, `tests/test_pspc_static_compatibility_review.py`, this task directory, `artifacts/pspc_static_compatibility_review_v0/`, and matching governance/ledger/generated-view entries.

