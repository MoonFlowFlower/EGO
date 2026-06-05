# EgoDesktop Session-Local Conversation Context v0 Acceptance

## Acceptance Criteria

- EgoDesktop sends `desktop_session_context` on chat turns.
- First turn sends an empty context.
- Successful turns append user and assistant visible text.
- Failed backend turns are not appended.
- Context is trimmed to 12 recent turns, 1200 chars per message, and 12000 chars total.
- Python validator rejects system roles, authority escalation, executable fields, and over-limit payloads.
- Prior transcript is injected before PSPC preview style hint and before current user input.
- Report records `desktop_session_context_applied=true`, message count, no real memory write, no gate/approval/transport/proactive path, and claim ceiling.
- No `EgoOperator/agent_base.py`, gate, memory system, approval, transport, proactive, or human-trial harness changes.

## Manual Probes

- After a story turn, `继续` should continue the story.
- After saying the user likes coconut jelly and pearls in milk tea, `还记得我喜欢什么奶茶吗` should answer using this-session wording.
- After restarting EgoDesktop, the same memory probe should not recall the prior window session.

## Required Checks

- `node --test tests\session_context.test.js`
- `python -m pytest -q tests\test_ego_operator_desktop_session_context.py`
- `npm test`
- repo integrity and closeout gates

## What This Proves

It proves local EgoDesktop session continuity is available to the desktop turn backend.

## What This Does Not Prove

It does not prove durable memory, PSPC durable memory, stable user benefit, live autonomy, consciousness, subjective experience, or real emotion.
