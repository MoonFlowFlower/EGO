# EgoDesktop Session-Local Conversation Context v0 Stage Card

## Problem Reframe

EgoDesktop currently appears multi-turn in the UI, but each desktop backend turn starts a fresh runtime. That makes short follow-ups like `继续` lose context and makes PSPC preview quality hard to judge.

This stage adds bounded window-lifetime transcript context for EgoDesktop only.

## One Hypothesis

If EgoDesktop passes recent user/assistant turns as validated session-local context into the desktop turn script, local chat continuity improves without writing long-term memory or granting PSPC runtime authority.

## Change Surface

- `EgoDesktop/`
- `scripts/ego_operator_desktop_turn.py`
- targeted tests
- `docs/codex/tasks/egodesktop-session-local-conversation-context-v0/`
- `artifacts/egodesktop_session_local_conversation_context_v0/`
- necessary state/ledger/generated-view entries

## Authority Source

- Repo authority remains `docs/PROGRAM_STATE_UNIFIED.yaml`.
- EgoOperator core remains unchanged.
- `desktop_session_context` authority is local window transcript only.

## Boundaries

- claim ceiling: `local_session_context_only`
- persistence: `window_lifetime_only`
- runtime authority: `none`
- enabled: `false`
- mainline_connected: `false`
- no durable memory promotion

## Forbidden

- Do not modify `EgoOperator/agent_base.py`, gate, memory system, approval, transport, proactive behavior, or human-trial harness.
- Do not write real EgoOperator memory.
- Do not create or register PSPC adapter.
- Do not treat session context as PSPC durable memory.
- Do not claim stable user benefit, live autonomy, consciousness, subjective experience, or real emotion.

## Three-Level Verify

1. Node tests prove transcript construction, trimming, and payload wiring.
2. Python tests prove validator rejection and in-session memory injection.
3. Report artifacts document manual probes, no side effects, and rollback.

## Rollback

Delete the session context module, tests, desktop turn script edits, main process wiring, report script, this task directory, artifact directory, and matching state/ledger/generated-view entries.

## What This Proves

It proves EgoDesktop can pass bounded recent window-local turns to the one-turn backend as temporary in-session context.

## What This Does Not Prove

It does not prove durable memory, preference promotion, PSPC durable memory, runtime integration safety, stable real user benefit, live autonomy, consciousness, subjective experience, or real emotion.
