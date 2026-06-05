# EgoDesktop Session-Local Conversation Context v0 Contract

## Context Schema

- `schema_version: ego_desktop.session_context.v0`
- `source: ego_desktop_main_process_session_local`
- `claim_ceiling: local_session_context_only`
- `persistence: window_lifetime_only`
- `runtime_authority: none`
- `enabled: false`
- `mainline_connected: false`
- `messages: [{ role, content, turn_index }]`

Allowed roles are only `user` and `assistant`.

## Limits

- Keep the latest 12 user/assistant pairs.
- Max 1200 chars per message.
- Max 12000 chars total context.
- Append a turn only after backend status is `ok`.
- Clear automatically when the EgoDesktop window process exits.

## Rejection Rules

Reject contexts containing:

- `system` role
- `enabled: true`
- `mainline_connected: true`
- runtime authority other than `none`
- executable fields such as `action`, `tool_call`, `user_message`, `memory_write`, `gate_decision`, `transport`, or `send`
- too many messages
- too-long messages

## Injection Rule

The desktop turn script injects validated prior transcript into `runtime.memory` after `build_demo_runtime(enable_operator_memory=False)` and before the current `handle_user_message()` call. PSPC reply preview system context, if present, is injected after prior transcript and before the current user turn.

## What This Proves

This proves only local desktop chat continuity can be represented as temporary in-session context.

## What This Does Not Prove

It does not prove long-term memory, real user benefit, PSPC learning, runtime integration safety, consciousness, subjective experience, or real emotion.
