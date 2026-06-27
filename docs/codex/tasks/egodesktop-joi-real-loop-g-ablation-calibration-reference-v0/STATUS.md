# EgoDesktop Joi Real-Loop G-ABLATION Captured Calibration Reference v0 Status

- status: `card_reviewed_no_blocking_findings__implementation_not_started`
- task_id: `EGODESKTOP-GABLATION-009`
- claim_ceiling: `egodesktop_real_loop_g_ablation_captured_calibration_reference_contract_only`
- mainline_connected: `false`
- enabled: `explicit_cli_only`
- real_trigger_evidence: `none_yet_for_this_slice`
- runtime_authority: `none`

## Current Objective

Replace the 008 synthetic calibration reference with a captured/fitted calibration source before any future
`CREATURE_ON` row or scoring slice. This task is provenance/replay hygiene only.

## Current Readback

- 008 accepted row hash:
  `bd120552670850025ab531a8dc8b9a064c50ba30277115451a0d86c84b38de04`
- 006 source artifact:
  `artifacts/egodesktop_joi_real_loop_g_ablation_backend_trace_snapshot_v0/trace/trace_rows.jsonl`
- Current 006 source artifact contains one `CURRENT_SHIM` / `heldout` row and no separate `calibration` split row.
- Therefore implementation must capture or consume a separate calibration source before replacing the synthetic
  reference. It must not relabel heldout as calibration.

## Evidence Produced

- Card-stage docs and task-board entry only.
- No calibration-reference builder has been implemented.
- No calibration trace has been captured.
- No rebuilt heldout row has been produced.

## Claude Review Readback

Desktop Claude returned `BLOCKING_FINDINGS` source-limited for the first 009 card draft:

1. `split` leakage: hash inequality is not enough; require a predeclared disjoint calibration/heldout partition protocol.
2. input-blind definition too loose: captured calibration must be a fixed output schedule, not state reuse in heldout
   recompute.
3. calibration row production was under-specified even though no calibration row currently exists.
4. acceptance lacked must-fire positive controls.

Card repairs now recorded:

- pre-capture partition manifest with protocol hash, disjointness assertions, and split-overlap positive control;
- fixed-output-schedule replay contract and captured-state provenance-only restriction;
- explicit requirement to reuse the existing 006 tap / real sendChatTurn path under flags;
- must-fire controls for synthetic fallback, split overlap, synthetic kind, and captured-calibration shuffle/invariance.

Non-blocking caveat: without `CREATURE_ON` output, captured calibration remains a `CURRENT_SHIM`-level weak baseline
component. Decisive saturation handling still depends on a separate same-access reproducer battery slice.

## Acceptance Readback

Card accepted for implementation only. Desktop Claude returned `NO_BLOCKING_FINDINGS` source-limited for the repaired
card text after B-009-1..4 were repaired. This is not implementation acceptance and does not prove any artifact capture,
replay recompute, scoring result, or route verdict.

## What This Can Prove

Only that a static replay heldout row consumes a captured/fitted calibration reference instead of a synthetic constant.

## What This Does Not Prove

This does not prove baseline saturation, creature failure, candidate attribution, real-loop effect, route advancement,
product benefit, runtime integration safety, stable user benefit, durable memory efficacy, agency, emotion,
subjectivity, consciousness, alive status, or Bar-2 specialness.

## Next Minimal Closed-Loop Action

Implement only the tests-first calibration-reference builder and rebuilt `OFF_STATIC_REPLAY_HELDOUT` row. Do not score,
compare, emit `CREATURE_ON`, update program state, update evidence ledger, push, tag, or remote-anchor in 009.
