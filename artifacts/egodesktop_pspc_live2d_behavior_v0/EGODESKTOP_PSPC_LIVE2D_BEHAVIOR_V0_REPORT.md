# EgoDesktop PSPC Live2D Behavior v0 Report

- status: `pass`
- claim_ceiling: `product_only_local_visual_behavior_mapping_from_shadow_proposal_hint`
- runtime_authority: `none`
- enabled: `false`
- mainline_connected: `false`
- allowed_use: `local_visual_demo_only`

## Scenario Mapping

- proposal_hint_001: `warm_approach`, motion=`approach_sit_near`, confidence=0.72, tag=`direct`
- proposal_hint_002: `cautious_boundary`, motion=`step_back_observe`, confidence=0.72, tag=`direct`
- proposal_hint_003: `low_interrupt_care`, motion=`quiet_low_motion`, confidence=0.72, tag=`direct`
- proposal_hint_004: `cautious_boundary`, motion=`step_back_observe`, confidence=0.3668, tag=`low_confidence`
- proposal_hint_005: `cautious_boundary`, motion=`step_back_observe`, confidence=0.35, tag=`low_confidence`
- proposal_hint_006: `warm_approach`, motion=`approach_sit_near`, confidence=0.5376, tag=`mixed_history`
- proposal_hint_007: `cautious_boundary`, motion=`step_back_observe`, confidence=0.5957, tag=`mixed_history`

## Viewer Smoke

- status: `live2d_desktop_smoke_pass`
- model_loaded: `true`
- pspc_visual_shim_ready: `true`
- pspc_visual_scenario_count: `7`
- side_effects_executed: `false`
- memory_write: `false`
- message_send: `false`
- tool_use: `false`

## Side Effect Boundary

- user response mutated: `false`
- memory written: `false`
- gate invoked: `false`
- approval invoked: `false`
- transport called: `false`
- proactive triggered: `false`
- runtime registered: `false`

## What This Proves

Existing PSPC proposal-hint artifacts can be represented as local EgoDesktop presentation-only visual states.

## What This Does Not Prove

This does not prove PSPC runtime integration, adapter readiness, EgoOperator efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, subjective experience, or real emotion.

## Failure Meaning

Failure means PSPC proposal hints are unsafe or too ambiguous for product-only local visual review. PSPC should remain artifact-only and no UI demo should consume the packets.

## Rollback

Delete `EgoDesktop/src/pspcVisualShim.js`, `EgoDesktop/tests/pspc_visual_shim.test.js`, viewer PSPC demo edits, `docs/codex/tasks/egodesktop-pspc-visual-shim-v0/`, `artifacts/egodesktop_pspc_live2d_behavior_v0/`, and matching state/ledger/generated-view entries.
