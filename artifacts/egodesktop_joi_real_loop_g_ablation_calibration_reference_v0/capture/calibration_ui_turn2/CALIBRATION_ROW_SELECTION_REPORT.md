# EgoDesktop G-ABLATION 009 Calibration Row Selection Report

- status: `blocked_superseded_post_hoc_selection_attempt_recorded`
- claim_ceiling: `egodesktop_real_loop_g_ablation_captured_calibration_reference_contract_only`
- selection_scope: `blocked_attempt_provenance_only_not_scoring_evidence`
- review_blocker: `B-009-IMPL-1_post_hoc_positional_selection`
- superseded_by: `artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/capture/calibration_ui_predeclared_single/PREDECLARED_CAPTURE_REPORT.json`
- raw_capture_rows: `artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/capture/calibration_ui_turn2/trace/trace_rows.jsonl`
- raw_capture_rows_count: `2`
- selected_rows: `artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/capture/calibration_ui_turn2/selected_calibration_trace_rows.jsonl`
- selected_row_hash: `f335d25a50fb944e11278917c8421a4e23399c3e092049a7533c95c250a73d3c`
- selected_turn_id: `turn_2`
- rejected_row_hash: `4f215fb0dee1a3f31fc40a6590aa2fb8b026a77ed060c69b189f57fbb3e83e10`
- rejected_reason: `literal_turn_id_overlap_with_heldout_turn_1`

## Current Meaning

The UI capture produced two calibration rows through the existing 006 tap. The first row was not consumed by 009
because its literal `turn_id` overlapped the heldout source row. The second row was selected and then checked by the
009 split partition manifest.

This report records the blocked post-hoc selection attempt only. It is not the accepted 009 calibration input, baseline
comparison, attribution verdict, route decision, or scoring run.
