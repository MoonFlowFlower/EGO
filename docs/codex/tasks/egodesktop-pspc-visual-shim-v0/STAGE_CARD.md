# EgoDesktop PSPC Visual Shim v0 Stage Card

- status: `pass`
- lane: `product-only-local-visual-shim`
- claim ceiling: `product_only_local_visual_behavior_mapping_from_shadow_proposal_hint`
- runtime authority: `none`
- EgoOperator integration: `forbidden`
- mainline mutation: `forbidden`
- PSPC runtime/action selection: `forbidden`

## Problem Reframe

PSPC proposal-hint artifacts are ready for product-only visual review, not for EgoOperator runtime integration. The useful next step is to show whether existing Live2D presentation can render different local visual tendencies from read-only PSPC proposal hints.

## One Hypothesis

If a side-effect-free visual mapper consumes the seven `shadow_proposal_hint` packets, EgoDesktop can present distinct local Live2D behavior profiles while preserving no runtime authority, no memory write, no gate invocation, no user-response mutation, and no proactive path.

## One Change Surface

Only the EgoDesktop presentation layer may change. The mapper may read existing PSPC proposal-hint artifacts and expose local visual demo state to the viewer.

## Authority Source

- Input evidence: `artifacts/pspc_shadow_proposal_hint_contract_v0/proposal_hint_contract.json`
- Existing side-effect sanitizer pattern: `EgoDesktop/src/signalFrame.js`
- Repo claim authority: `docs/PROGRAM_STATE_UNIFIED.yaml`

## What Can Change

- A pure EgoDesktop mapper from PSPC proposal-hint packet to local visual state.
- A local viewer demo selector that renders presentation-only behavior hints.
- Docs, tests, and artifact-only report for this stage.

## What Cannot Be Proven

This does not prove PSPC is integrated into EgoOperator, EgoOperator runtime safety, real user benefit, model learning, durable memory efficacy, live autonomy, consciousness, subjective experience, or real emotion.

## Three-Level Verify

1. Contract tests prove the mapper rejects unsafe packets and produces non-executable visual states.
2. Viewer static tests prove the PSPC demo path does not use `sendChatTurn` or EgoOperator runtime calls.
3. Artifact report records mapped scenarios, side-effect absence, claim ceiling, and rollback.

## Rollback Plan

Delete `EgoDesktop` PSPC visual-shim files, matching tests, this task directory, `artifacts/egodesktop_pspc_live2d_behavior_v0/`, and matching state/ledger/generated-view entries.
