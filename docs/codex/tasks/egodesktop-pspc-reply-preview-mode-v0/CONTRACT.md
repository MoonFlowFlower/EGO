# EgoDesktop PSPC Reply Preview Mode v0 Contract

## Input

The desktop main process may send `pspc_reply_preview_context` only when `pspc_reply_preview_mode=true`.

Required context fields:

- `schema_version: ego_desktop.pspc_reply_preview_context.v0`
- `source: ego_desktop_session_local_pspc_reply_preview`
- `claim_ceiling: local_reply_preview_only`
- `allowed_use: ego_desktop_local_reply_preview_only`
- `runtime_authority: none`
- `enabled: false`
- `mainline_connected: false`
- `profile.style`
- `profile.confidence`
- `profile.basis`
- `profile.reason_trace_refs`
- `forbidden`
- `no_authority`

## Forbidden Fields

The preview context must reject executable fields including:

- `action`
- `tool_call`
- `command`
- `user_message`
- `memory_write`
- `gate_decision`
- `approval_id`
- `transport`
- `send`
- `schedule`
- `enable`
- `mainline_authority`
- `proposal_id`

## Required Forbidden Flags

These flags must be present and true:

- `direct_action`
- `direct_user_message`
- `direct_memory_write`
- `runtime_gate_bypass`
- `runtime_registration`
- `proactive_trigger`
- `planner_execution`
- `model_execution`
- `training`

## Required No-Authority Flags

These flags must be present and false:

- `direct_action_allowed`
- `direct_user_message_allowed`
- `direct_memory_write_allowed`
- `runtime_gate_bypass_allowed`
- `runtime_registration_allowed`
- `proactive_trigger_allowed`
- `planner_execution_allowed`
- `model_execution_allowed`
- `training_allowed`

## Runtime Boundary

The desktop turn script may convert a valid context into temporary in-session system context after `build_demo_runtime(enable_operator_memory=False)` and before `handle_user_message()`.

It must not write real memory, invoke gates, request approvals, call transports, trigger proactive behavior, call PSPC planner/training/model execution, or register PSPC in runtime.

## What This Proves

This contract proves only that a local preview context can be validated and used as a temporary reply-style hint under an explicit flag.

## What This Does Not Prove

It does not prove PSPC runtime integration safety, adapter readiness, durable memory efficacy, stable real user benefit, consciousness, subjective experience, real emotion, or production readiness.
