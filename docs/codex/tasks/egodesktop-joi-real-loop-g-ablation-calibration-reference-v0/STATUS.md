# EgoDesktop Joi Real-Loop G-ABLATION Captured Calibration Reference v0 Status

- status: `accepted_after_claude_no_blocking__local_commit_pending`
- task_id: `EGODESKTOP-GABLATION-009`
- claim_ceiling: `egodesktop_real_loop_g_ablation_captured_calibration_reference_contract_only`
- mainline_connected: `false`
- enabled: `explicit_cli_only`
- real_trigger_evidence: `window.egoDesktop.sendChatTurn_ui_capture_to_existing_006_tap`
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
- 009 captured a separate predeclared calibration source before replacing the synthetic reference. It does not relabel
  heldout as calibration.

## Evidence Produced

- Calibration-reference builder module and CLI implemented:
  `EgoDesktop/src/joiRealLoopGAblationCalibrationReference.js` and
  `EgoDesktop/scripts/build-joi-g-ablation-calibration-reference.js`.
- Existing heldout replay builder now accepts an explicit captured calibration reference while preserving the 008
  synthetic default path.
- Rejected/superseded attempt: the first implementation captured two calibration UI rows and consumed `turn_2` after
  rejecting `turn_1` because of literal `turn_id` overlap. Claude blocked that as post-hoc positional selection. The
  blocked attempt is preserved under
  `artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/capture/calibration_ui_turn2/`.
- Repair capture: a single calibration prompt was predeclared before capture:
  `artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/capture/calibration_ui_predeclared_single/PREDECLARED_CALIBRATION_PROMPT_PACK.json`.
- Predeclared prompt pack hash:
  `63704cafe002d3ee07f7b5a61a0f3820fca8688c9e52a844cd7d97600c7bc0db`.
- Fresh real calibration capture was produced through the visible EgoDesktop UI, using
  `window.egoDesktop.sendChatTurn(...)` and the existing 006 trace tap/writer:
  `artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/capture/calibration_ui_predeclared_single/trace/trace_rows.jsonl`.
- Fresh captured calibration row hash:
  `aebbdbedaca71d8955e470ffc6977d1bb9816e49f8af5878abd20eebbc5a4b28`.
- Predeclared capture report:
  `artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/capture/calibration_ui_predeclared_single/PREDECLARED_CAPTURE_REPORT.json`.
  It records `raw_capture_rows_count=1`, `selection_policy_status=deterministic_predeclared_single_prompt_consumed`,
  `post_hoc_selection_status=absent`, and `turn_id_role=informational_position_provenance_not_content_disjointness_gate`.
- Captured calibration reference:
  `artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/calibration_reference/calibration_reference.json`.
- Captured calibration reference hash:
  `52411a8378e4a258a03f16b606052d9fcc42650af16c655684db07dc94356067`.
- Split partition manifest:
  `artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/calibration_reference/partition/SPLIT_PARTITION_MANIFEST.json`.
- Partition protocol hash:
  `2d7a6e745a68812348ea49cbf579e8e0e866e11b37b1541cecbf6ebc28804b50`.
- Rebuilt heldout row path:
  `artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/trace/trace_rows.jsonl`.
- Rebuilt heldout row hash:
  `95722e9c2be9e29a188e759f4490f75bb8518d99e70fd79c41533f5b60345166`.
- Evaluator report:
  `artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/evaluator/evaluation_report.json`.

## Claude Review Readback

Desktop Claude returned `BLOCKING_FINDINGS` source-limited for the first 009 card draft:

1. `split` leakage: hash inequality is not enough; require a predeclared disjoint calibration/heldout partition protocol.
2. input-blind definition too loose: captured calibration must be a fixed output schedule, not state reuse in heldout
   recompute.
3. calibration row production was under-specified even though no calibration row currently exists.
4. acceptance lacked must-fire positive controls.

Card repairs now recorded:

- predeclared calibration prompt pack plus partition manifest with protocol hash, disjointness assertions, and
  split-overlap positive control;
- fixed-output-schedule replay contract and captured-state provenance-only restriction;
- explicit requirement to reuse the existing 006 tap / real sendChatTurn path under flags;
- must-fire controls for synthetic fallback, split overlap, synthetic kind, and captured-calibration shuffle/invariance.

Non-blocking caveat: without `CREATURE_ON` output, captured calibration remains a `CURRENT_SHIM`-level weak baseline
component. Decisive saturation handling still depends on a separate same-access reproducer battery slice.

## Acceptance Readback

Card accepted for implementation only. Desktop Claude returned `NO_BLOCKING_FINDINGS` source-limited for the repaired
card text after B-009-1..4 were repaired. This is not implementation acceptance and does not prove any artifact capture,
replay recompute, scoring result, or route verdict.

Local implementation evidence accepted by Claude source-limited review:

- partition_disjointness_status: `pass`
- content_disjointness_status: `pass`
- provenance_distinctness_status: `pass`
- turn_id_provenance_status: `informational_only_not_content_disjointness_gate`
- selection_policy_status: `deterministic_predeclared_single_prompt_consumed`
- post_hoc_selection_status: `absent`
- overlap_positive_control_status: `pass`
- synthetic_fallback_positive_control_status: `pass`
- split_contract_status: `captured_calibration_reference_distinct_from_heldout_observation`
- calibration_reference_kind: `captured_backend_trace_reference`
- calibration_reference_source: `fixed_output_schedule_from_calibration_trace`
- observation_shuffle_control_status: `pass`
- calibration_state_shuffle_control_status: `pass`
- evaluator_status: `replay_integrity_preflight_pass_no_verdict`
- d_field_replay_precondition_satisfied: `true`
- scoring_run_authorized: `false`
- verdict_authorized: `false`
- focused G-ablation tests: `26 passed`
- EgoDesktop npm test: `94 passed`

Claude implementation review returned `BLOCKING_FINDINGS` source-limited for B-009-IMPL-1: the prior two-row capture
used post-hoc positional selection and treated `turn_id` as too strong a disjointness gate. The local repair now:

- predeclares a single calibration prompt pack before capture;
- captures exactly one matching calibration row through the real UI/default IPC seam;
- makes the builder consume the predeclared prompt exact match and report `post_hoc_selection_status=absent`;
- splits `content_disjointness` (`prompt_id`, `user_text_hash`) from `provenance_distinctness`
  (`source_row_hash`, `trace_record_hash`, `capture_run_id`);
- records `turn_id` as informational provenance only, not a content disjointness gate.

Claude re-review returned `NO_BLOCKING_FINDINGS (source-limited)`: B-009-IMPL-1 is closed because the predeclared
single-prompt capture eliminates post-hoc selection, the builder is deterministic exact-match, `turn_id` is demoted to
informational provenance, and minimal surface/default-off/no-scoring boundaries remain intact. Claude's next minimal
action is to commit 009 locally only; the decisive `SAME_ACCESS_REPRODUCER_BATTERY + CREATURE_ON` comparison is a
separate future slice with pre-frozen thresholds.

## What This Can Prove

Only that a static replay heldout row consumes a captured/fitted calibration reference instead of a synthetic constant.

## What This Does Not Prove

This does not prove baseline saturation, creature failure, candidate attribution, real-loop effect, route advancement,
product benefit, runtime integration safety, stable user benefit, durable memory efficacy, agency, emotion,
subjectivity, consciousness, alive status, or Bar-2 specialness.

## Next Minimal Closed-Loop Action

Commit 009 locally only. The next separate slice is a decisive `SAME_ACCESS_REPRODUCER_BATTERY + CREATURE_ON`
comparison with pre-frozen thresholds; do not score, compare, emit `CREATURE_ON`, update program state, update evidence
ledger, push, tag, or remote-anchor in 009.
