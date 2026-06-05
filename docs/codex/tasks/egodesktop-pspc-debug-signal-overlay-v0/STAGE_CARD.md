# EgoDesktop PSPC Debug Signal Overlay v0 Stage Card

## Problem Reframe

PSPC Reply Preview Mode can influence local reply style and Live2D presentation only when `--pspc-reply-preview-mode` is explicitly enabled, but its session-local proxy state is not visible enough to debug. A user can run normal creative chat and reasonably feel no PSPC effect, because the current text can be driven mostly by session context and LLM continuation rather than PSPC history signals.

This stage adds observability for the preview proxy. It does not strengthen PSPC, connect PSPC to runtime, or add durable memory.

## One Hypothesis

If the hidden audit overlay exposes PSPC style, confidence, history counts, recent categories, reason refs, and proxy bars, the user can distinguish:

- ordinary LLM creative continuation
- window-lifetime session context
- PSPC preview style hint
- PSPC signal inactive / neutral

## Change Surface

- `EgoDesktop/src/pspcReplyPreview.js`
- `EgoDesktop/viewer/renderer.js`
- `EgoDesktop/viewer/styles.css`
- `EgoDesktop/tests/pspc_reply_preview.test.js`
- `docs/codex/tasks/egodesktop-pspc-debug-signal-overlay-v0/`
- `artifacts/egodesktop_pspc_debug_signal_overlay_v0/`
- scoped state, contract, evidence-ledger, and generated-view entries required for closeout

## Authority Source

- Repo authority remains `docs/PROGRAM_STATE_UNIFIED.yaml`.
- `EgoDesktop` remains a local desktop surface.
- PSPC Reply Preview remains explicit-flag-only and session-local.
- EgoOperator runtime, gate, memory, approval, transport, proactive behavior, and human-trial harness remain unchanged.

## Boundaries

- claim ceiling: `local_reply_preview_observability_only`
- runtime authority: `none`
- persistence: window-lifetime preview state only
- default UI state: debug overlay hidden
- PSPC preview enabled only by `--pspc-reply-preview-mode`
- no adapter creation
- no mainline connection

## Forbidden

- Do not modify EgoOperator runtime, gate, memory, approval, transport, proactive behavior, or human-trial harness.
- Do not write real memory.
- Do not invoke gate, approval, transport, proactive behavior, tools, planner, training, or model execution.
- Do not create or register an adapter.
- Do not expose executable fields in debug overlay.
- Do not claim PSPC learned behavior, stable user benefit, durable memory, live autonomy, consciousness, subjective experience, or real emotion.

## Three-Level Verify

1. Unit tests prove standard history groups produce visible proxy bars and the current creative log remains neutral/inactive.
2. UI source uses scenario-provided debug overlay and does not change the reply path or send path.
3. Artifact report documents no side effects, rollback, failure meaning, and claim ceiling.

## Rollback

Delete the debug overlay additions in `EgoDesktop/src/pspcReplyPreview.js`, `EgoDesktop/viewer/renderer.js`, `EgoDesktop/viewer/styles.css`, the added tests, this task directory, artifact directory, and matching state/ledger/generated-view entries.

## What This Proves

This proves EgoDesktop can display PSPC Reply Preview proxy-state observability, including active versus neutral signal state, without adding runtime authority or side effects.

## What This Does Not Prove

It does not prove PSPC mainline integration, true learning, durable memory, runtime integration safety, stable real user benefit, live autonomy, consciousness, subjective experience, or real emotion.
