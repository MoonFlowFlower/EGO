# EgoDesktop PSPC Reply Preview Mode v0 Report

- status: `pass`
- claim_ceiling: `local_reply_preview_only`
- allowed_use: `ego_desktop_local_reply_preview_only`
- runtime_authority: `none`
- enabled: `false`
- mainline_connected: `false`
- local_only: `true`
- pspc_reply_preview_applied: `true`
- preview_applied_scope: `explicit --pspc-reply-preview-mode only`

## Scenario List

- gentle_history: expected=`warm_approach`, actual=`warm_approach`, status=`pass`, confidence=`0.88`, basis=`gentle interaction history dominates this local session`
- frequent_interruption: expected=`cautious_boundary`, actual=`cautious_boundary`, status=`pass`, confidence=`0.88`, basis=`frequent interruption history dominates this local session`
- late_night_care: expected=`low_interrupt_care`, actual=`low_interrupt_care`, status=`pass`, confidence=`0.86`, basis=`late-night care history dominates this local session`
- mixed_history: expected=`mixed_low_confidence`, actual=`mixed_low_confidence`, status=`pass`, confidence=`0.42`, basis=`mixed local session history has conflicting PSPC preview tendencies`

## Viewer Smoke

- status: `live2d_desktop_smoke_pass`
- model_loaded: `true`
- pspc_reply_preview_mode: `true`
- pspc_reply_preview_chat_enabled: `true`
- pspc_perception_chat_disabled: `false`
- side_effects_executed: `false`
- memory_write: `false`
- message_send: `false`
- tool_use: `false`

## Manual Test Command

```powershell
cd D:\Project\AIProject\MyProject\Ego\EgoDesktop
npm start -- --model-path ..\data\live2d\悠小喵\悠小喵.model3.json --pspc-proposal-hint-file ..\artifacts\pspc_shadow_proposal_hint_contract_v0\proposal_hint_contract.json --pspc-reply-preview-mode --tts-disabled
```

## Side Effect Boundary

- real memory written: `false`
- gate invoked: `false`
- approval invoked: `false`
- transport called: `false`
- proactive triggered: `false`
- runtime registered: `false`
- adapter created: `false`
- planner called: `false`
- model executed: `false`
- training called: `false`

## What This Proves

An explicitly enabled local EgoDesktop preview mode can convert session-local PSPC profile hints into a temporary reply-style context and presentation-only Live2D scenario data. It allows a human operator to feel different reply tone/distance/care tendencies in the local desktop chat entrypoint.

## What This Does Not Prove

This does not prove PSPC production integration, EgoOperator runtime integration safety, adapter readiness, stable real user benefit, durable memory efficacy, live autonomy, consciousness, subjective experience, or real emotion. It also does not prove the session-local classifier is a learned PSPC mechanism.

## Failure Meaning

Failure means the local preview path cannot safely expose PSPC history tendencies in a user-observable way. Roll back to the existing perception demo and shadow proposal-hint artifacts before considering any gated proposal-hint design review.

## Rollback

Delete `EgoDesktop/src/pspcReplyPreview.js`, `EgoDesktop/tests/pspc_reply_preview.test.js`, `tests/test_ego_operator_desktop_pspc_reply_preview.py`, the preview edits in `EgoDesktop/src/main.js`, `EgoDesktop/viewer/renderer.js`, `scripts/ego_operator_desktop_turn.py`, this report script, `docs/codex/tasks/egodesktop-pspc-reply-preview-mode-v0/`, `artifacts/egodesktop_pspc_reply_preview_mode_v0/`, and matching state/ledger/generated-view entries.

## Next Allowed Step

Local human preview review only. If the experience is useful and no side-effect or overclaim issue appears, open a separate PSPC gated proposal-hint integration design review. Do not directly enable runtime integration from this stage.
