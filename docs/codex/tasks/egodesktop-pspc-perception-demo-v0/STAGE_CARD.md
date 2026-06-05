# EgoDesktop PSPC Perception Demo v0 Stage Card

- lane: `product-only-local-demo`
- runtime authority: `none`
- EgoOperator integration: `forbidden`
- enabled: `false`
- mainline_connected: `false`
- adapter creation: `forbidden`
- claim ceiling: `product_only_local_perception_demo_from_shadow_proposal_hint`

## Problem Reframe

The current question is not whether PSPC should enter EgoOperator runtime. The bounded question is whether humans can perceive different companion behaviors when the same trigger is displayed after different PSPC proposal-hint histories.

## One Hypothesis

If PSPC proposal-hint packets are presentation-only and deterministic, EgoDesktop can replay four visible Live2D reactions for `我回来了。` without runtime, memory, gate, transport, proactive, or chat side effects.

## One Change Surface

Only EgoDesktop presentation code, local tests, docs, and perception-demo artifacts may change. EgoOperator runtime, gates, memory, approval, transport, proactive behavior, and human-trial harness are out of scope.

## Authority Source

Input authority is the existing `artifacts/pspc_shadow_proposal_hint_contract_v0/proposal_hint_contract.json` artifact. Output authority is limited to local visual presentation data and human perception review scripts.

## What Can Change

- A pure EgoDesktop perception demo builder.
- Viewer controls for scenario playback, same-trigger display, debug overlay, and deterministic recording mode.
- Product-only report and market validation scripts.

## What Cannot Be Proven

This cannot prove PSPC runtime integration, adapter readiness, EgoOperator efficacy, real user benefit, durable memory efficacy, live autonomy, consciousness, subjective experience, or real emotion.

## Three-Level Verify

1. Contract tests verify deterministic scenario playback and no executable authority fields.
2. EgoDesktop regression tests verify existing visual shim behavior still passes.
3. Local smoke/report artifacts verify viewer readiness and no runtime authority claims.

## Rollback Plan

Delete `EgoDesktop/src/pspcPerceptionDemo.js`, `EgoDesktop/tests/pspc_perception_demo.test.js`, perception viewer edits, `EgoDesktop/scripts/build_pspc_perception_demo_report.js`, this task directory, `artifacts/egodesktop_pspc_perception_demo_v0/`, and matching state/ledger/generated-view entries.
