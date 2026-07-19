# EGO-ITL-V2-ONLY-SIMPLIFICATION-001A — Ego execution card

Status: `OPERATOR_AUTHORIZED__EXECUTION_REQUESTED_2026-07-18`

Authority source: the current user-authored plan headed `Ego + ITL V2-Only
整体简化计划`, transcribed by the ITL card
`docs/codex/tasks/EGO-ITL-V2-ONLY-SIMPLIFICATION-001A.md`.

Auto-Remote-Anchor: `forbidden`

Local rollback tag: `authorized`; push/publication: `forbidden`.

## Problem definition

Retire EgoOperator/EgoDesktop from the current tree, make the existing V2
playground the only explicit product entry, and replace divergent active docs
with views rendered from an exact pinned ITL product-axis mirror.

## Layer, mainline, enablement, trigger

- Layer: engineering implementation and product/evidence governance.
- Mainline: `scripts/run_ego_life_playground_v0.py` only.
- Enabled: explicit user launch only; default/autostart/background/network/LLM
  remain off.
- Trigger: launcher -> one `PlaygroundController` -> SQLite transition/trace ->
  save/load -> fresh-process replay recomputation.

## Hypothesis and strongest baseline

Exact state mirroring plus generated views and manifest-backed removal will make
active context smaller and fail closed on drift. A manual docs-only rewrite is
the strongest baseline and is rejected because it cannot prove mirror bytes,
caller absence, positive-control detection, or rollback reconstruction.

## Ablation, replay, provenance

Mutating the source pin, mirror, entrypoint, enablement, or active-owner wording
must fail. Replay must use serialized state plus observation. Verification
receipts record callable producer, inputs, run ID, aggregation and code hash.
The real-Tk smoke stores its bounded screenshot/result/trace/baseline/ablation/
replay/failure set below the task artifact directory; these are product-path
smoke artifacts, not new mechanism evidence.

## Acceptance and claim ceiling

Acceptance is the exact set in the ITL card plus byte identity for the four
causal producers and a zero legacy current-code caller scan. Claim ceiling is
local explicit V2 product selection and bounded engineering/replay evidence;
no learning, memory causality, agency, subjectivity, consciousness, or stable
user benefit claim is authorized.

## Fixed X -> Y -> Z -> W convergence

- ITL X authorizes the V2-only boundary with retirement pending.
- Ego Y mirrors the raw ITL X Git blob, pins its OID/SHA-256, performs the
  manifest-backed retirement, and writes the Ego receipt.
- ITL Z consumes that receipt only after asserting its ITL source OID is the
  object produced by X; ITL then marks both retired projects complete and pins
  Ego Y.
- Ego W must re-mirror the raw ITL Z Git blob and regenerate all active views.

Final acceptance is Ego W == `ITL Z:artifacts/ROUTE-STATE-MACHINE-001A/product_axis_state.json`
at raw blob-byte, field, OID, and SHA-256 levels. The intermediate pending
mirror at Ego Y cannot satisfy final acceptance. No CRLF or semantic
normalization may substitute for raw Git blob equality.

## Stop, rollback, files

Stop on drift, blocking independent Red review, unmanifested deletion, causal
producer change, mirror mismatch, replay failure, or recovery failure. Rollback
is the authorized local pre-retirement tag plus ordinary revert commits. Exact
paths are in `MUTATION_SCOPE.json` and the generated retirement manifest.
