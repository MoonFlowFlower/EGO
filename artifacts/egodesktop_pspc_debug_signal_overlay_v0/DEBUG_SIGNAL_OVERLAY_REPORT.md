# EgoDesktop PSPC Debug Signal Overlay v0 Report

- status: `pass`
- claim_ceiling: `local_reply_preview_observability_only`
- runtime_authority: `none`
- enabled_by_default: `false`
- mainline_connected: `false`
- debug_overlay_hidden_by_default: `true`

## Scenario Summary

The hidden `审计` overlay now labels PSPC preview state as `PSPC preview proxy` and shows:

- `style`
- `confidence`
- `history_counts`
- `recent_categories`
- `reason_trace_refs`
- `basis`
- `claim_ceiling`
- `PSPC signal active` or `PSPC signal inactive / neutral`
- seven proxy bars: trust, stress, approach, avoidance, care, boundary, and low-interrupt

## Regression Interpretation

The current fanfic/creative continuation log is expected to stay `mixed_low_confidence` with `PSPC signal inactive / neutral`. That means the visible conversation was mostly ordinary LLM continuation plus window-lifetime session context, not a strong PSPC history signal.

Standard PSPC histories remain distinguishable:

- gentle history: raises trust and approach proxy bars
- frequent interruption history: raises stress, avoidance, and boundary proxy bars
- late-night history: raises care and low-interrupt proxy bars

## Side Effects

- no real memory write
- no gate invocation
- no approval invocation
- no transport call
- no proactive trigger
- no adapter creation
- no runtime registration
- no executable debug fields

## Failure Meaning

If the overlay stays neutral during normal chat, the current prompts did not trigger PSPC preview categories strongly enough. That is an observability finding, not proof that PSPC has failed. If standard history groups fail to move the proxy bars, then the preview classifier/scoring layer has regressed.

## Rollback

Delete the debug overlay additions in `EgoDesktop/src/pspcReplyPreview.js`, `EgoDesktop/viewer/renderer.js`, `EgoDesktop/viewer/styles.css`, `EgoDesktop/tests/pspc_reply_preview.test.js`, this task directory, artifact directory, and matching state/ledger/generated-view entries.

## What This Proves

This proves local PSPC Reply Preview proxy-state observability inside EgoDesktop.

## What This Does Not Prove

It does not prove PSPC mainline integration, true learning, durable memory, EgoOperator runtime integration safety, stable real user benefit, live autonomy, consciousness, subjective experience, or real emotion.

## Next Allowed Step

`PSPC Reply Preview Experience Harness v0`: run the same prompt against controlled histories and compare reply text plus proxy bars. This should remain local preview only until a separate design review explicitly admits any stronger integration.
