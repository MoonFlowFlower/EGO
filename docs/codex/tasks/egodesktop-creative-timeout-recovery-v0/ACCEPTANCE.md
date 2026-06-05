# EgoDesktop Creative Timeout Recovery & Route Isolation v0 Acceptance

## Required Signals

- Raw `llm_expression_unavailable: desktop_turn_timeout` is not shown as the visible bot text.
- Backend timeout turns are not appended into `desktop_session_context`.
- One-turn `desktop_recovery_context` is sent only after a failed backend turn and cleared after a successful backend turn.
- `desktop_recovery_context` rejects authority escalation and executable fields.
- Injection order is session transcript, recovery context, PSPC preview context, current user turn.
- Adult/creative timeout marker is not rendered as `adult_fiction_provider_limit`, `roleplay_exit_after_adult_fiction_limit`, scene memory, or scene capsule.
- Fixture route checks cover short emotional feedback and redirect to normal story.

## Required Negative Signals

- No real memory write.
- No gate invocation.
- No approval invocation.
- No transport or proactive call.
- No message send or tool execution.
- No PSPC adapter creation or registration.
- No `enabled=true` or `mainline_connected=true`.
- Claim ceiling remains `local_desktop_timeout_recovery_only`.

## Manual Smoke

1. Trigger a backend timeout with a long creative prompt or low `--chat-timeout-ms` value.
2. Confirm the UI shows a local timeout recovery message, not the raw backend marker.
3. Send `呜呜呜`; the reply should acknowledge the local failure naturally.
4. Send `没事，不做成人故事了，写正常故事吧`; the reply should not carry adult-route failure language.
5. Ask about a current-session fact, such as milk tea preference, to confirm session context still works.

## What This Proves

This proves local desktop timeout recovery and bridge isolation behavior.

## What This Does Not Prove

It does not prove adult content generation is working, provider latency is solved, PSPC is integrated, durable memory is effective, real user benefit is stable, live autonomy exists, consciousness exists, subjective experience exists, or real emotion exists.
