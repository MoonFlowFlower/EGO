# EgoDesktop PSPC Visual Shim v0 Status

- status: `pass`
- claim ceiling: `product_only_local_visual_behavior_mapping_from_shadow_proposal_hint`
- runtime authority: `none`
- mainline_connected: `false`
- enabled: `false`
- EgoOperator integration: `forbidden`

## Evidence

- Mapper: `EgoDesktop/src/pspcVisualShim.js`
- Viewer demo selector: `EgoDesktop/viewer/index.html`, `EgoDesktop/viewer/renderer.js`, `EgoDesktop/viewer/styles.css`
- Tests: `EgoDesktop/tests/pspc_visual_shim.test.js`
- Report: `artifacts/egodesktop_pspc_live2d_behavior_v0/EGODESKTOP_PSPC_LIVE2D_BEHAVIOR_V0_REPORT.md`
- Machine-readable artifact: `artifacts/egodesktop_pspc_live2d_behavior_v0/pspc_visual_shim.json`
- Viewer smoke: `artifacts/egodesktop_pspc_live2d_behavior_v0/smoke/live2d_desktop_smoke_report.json`

## Result

The seven existing PSPC `shadow_proposal_hint` packets map to local EgoDesktop presentation-only visual scenarios. The viewer exposes a local scenario selector that reads `config.pspcVisualShim` and does not use the chat-turn path. Electron smoke reports `live2d_desktop_smoke_pass`, `pspcVisualShimReady=true`, and `pspcVisualScenarioCount=7`.

## What This Proves

Existing PSPC proposal-hint artifacts can be represented as local EgoDesktop Live2D visual demo state without runtime authority.

## What This Does Not Prove

This does not prove PSPC runtime integration, adapter readiness, EgoOperator runtime efficacy, stable real user benefit, live autonomy, durable memory efficacy, consciousness, subjective experience, or real emotion.
