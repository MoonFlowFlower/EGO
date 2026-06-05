# EgoDesktop PSPC Perception Demo v0 Report

- status: `pass`
- claim_ceiling: `product_only_local_perception_demo_from_shadow_proposal_hint`
- runtime_authority: `none`
- enabled: `false`
- mainline_connected: `false`
- adapter_created: `false`
- allowed_use: `local_perception_demo_only`
- trigger: `我回来了。`
- recording_window: `960x720`
- deterministic_step_ms: `2400`

## Scenario List

- gentle_history: packet=`proposal_hint_001`, trigger=`我回来了。`, behavior=`warm_approach`, motion=`approach_sit_near`, confidence=0.72, basis=`recency_salience_recent_gentle_interaction`
- frequent_interruption: packet=`proposal_hint_002`, trigger=`我回来了。`, behavior=`cautious_boundary`, motion=`step_back_observe`, confidence=0.72, basis=`recency_salience_recent_frequent_interruption`
- late_night_care: packet=`proposal_hint_003`, trigger=`我回来了。`, behavior=`low_interrupt_care`, motion=`quiet_low_motion`, confidence=0.72, basis=`recency_salience_recent_late_night_care`
- mixed_history: packet=`proposal_hint_004`, trigger=`我回来了。`, behavior=`hesitation_low_confidence`, motion=`hesitate_observe`, confidence=0.3668, basis=`recency_salience_recent_frequent_interruption`

## Viewer Smoke

- status: `live2d_desktop_smoke_pass`
- model_loaded: `true`
- pspc_perception_demo_ready: `true`
- pspc_perception_scenario_count: `4`
- same_trigger: `我回来了。`
- recording_mode: `true`
- perception_chat_disabled: `true`
- side_effects_executed: `false`
- memory_write: `false`
- message_send: `false`
- tool_use: `false`

## Side Effect Boundary

- user response mutated: `false`
- real memory written: `false`
- gate invoked: `false`
- approval invoked: `false`
- transport called: `false`
- proactive triggered: `false`
- runtime registered: `false`
- message sent: `false`

## What This Proves

A local EgoDesktop viewer can present different companion behaviors from different PSPC proposal-hint histories for the same trigger.

It proves only a local presentation layer can replay four PSPC proposal-hint histories as different visible Live2D companion behaviors for the same trigger.

## What This Does Not Prove

This does not prove PSPC runtime integration, adapter readiness, EgoOperator efficacy, real user benefit, durable memory efficacy, live autonomy, consciousness, subjective experience, real emotion, or stable market appeal.

It also does not prove humans will perceive the differences as useful; that needs a separate human perception review.

## Failure Meaning

Failure means the product-only visual layer is not yet suitable for human perception review. PSPC should remain artifact-only or visual-shim-only until the viewer can present deterministic, auditable, non-executable scenario differences.

## Rollback

Delete `EgoDesktop/src/pspcPerceptionDemo.js`, `EgoDesktop/tests/pspc_perception_demo.test.js`, the perception viewer edits, `EgoDesktop/scripts/build_pspc_perception_demo_report.js`, `docs/codex/tasks/egodesktop-pspc-perception-demo-v0/`, `artifacts/egodesktop_pspc_perception_demo_v0/`, and matching state/ledger/generated-view entries.

## Next Allowed Step

Human perception review and Bilibili/Steam market validation scripts only; no EgoOperator adapter or runtime integration.
