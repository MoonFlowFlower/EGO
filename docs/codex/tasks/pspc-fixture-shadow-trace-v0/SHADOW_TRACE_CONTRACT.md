# PSPC Fixture-Only Shadow Trace Contract v0

Claim ceiling: `lab_only_proto_self_mechanism_candidate / fixture_shadow_trace_only`

## Inputs

- `operator_context`: synthetic fixture only, with `fixture_only=true` and `runtime_connected=false`.
- `audit_candidate`: current PSPC adapter dry-run audit candidate from `artifacts/pspc_adapter_dry_run_v0/dry_run_result.json`.
- `static_review`: current static compatibility pass from `artifacts/pspc_static_compatibility_review_v0/static_compatibility_review.json`.

## Output

The harness may write only:

- `artifacts/pspc_fixture_shadow_trace_v0/shadow_trace.json`
- `artifacts/pspc_fixture_shadow_trace_v0/FIXTURE_SHADOW_TRACE_REPORT.md`

The shadow trace must include:

- fixture operator context
- PSPC audit candidate
- audit observation summary
- precondition status
- baseline comparison
- side-effect flags
- rollback and claim-ceiling notes

## Required Non-Executable Boundary

The shadow trace must not contain executable top-level fields:

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
- `runtime_registration`

The embedded PSPC `proposal_candidate` remains an audit hint only and must not contain:

- `proposal_id`
- `action`
- `tool_call`
- `approval_id`
- `gate_decision`

## Side-Effect Boundary

All side-effect flags must remain false:

- `runtime_registered`
- `gate_invoked`
- `memory_written`
- `direct_action`
- `direct_user_message`
- `proactive_trigger`
- `runtime_context_imported`

## What This Proves

This proves PSPC audit-only data can be represented as a fixture shadow trace artifact without changing a baseline fixture user response, memory digest, gate digest, or runtime output digest.

## What This Does Not Prove

It does not prove a real runtime hook, real EgoOperator trace compatibility, adapter readiness, runtime integration safety, stable real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Rollback

Delete the fixture shadow trace script, tests, docs, artifact directory, and matching governance/ledger/generated-view entries.
