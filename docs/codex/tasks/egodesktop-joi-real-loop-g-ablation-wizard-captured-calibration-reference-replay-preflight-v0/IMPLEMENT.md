# Implementation

## Prior Slice - Task Card Only

The initial slice wrote planning/governance files only. It did not run the calibration-reference builder, OFF_STATIC
heldout builder, replay evaluator, Electron smoke, same-access baseline, scoring, or `CREATURE_ON`.

Card acceptance readback included:

- current layer: `engineering planning / captured calibration reference replay preflight card`
- mainline status: `not_connected_to_default_runtime`
- enabled status: `task_card_only_no_artifact_run`
- real trigger evidence: `planned_reuse_of_009_calibration_row_and_026_wizard_heldout_row`
- claim ceiling: `wizard_captured_calibration_reference_replay_card_only`

## Future Implementation Skeleton

Authorized and executed on 2026-06-27. The implementation:

1. Build a new 028 captured calibration reference from the accepted 009 calibration trace row plus the accepted 026 Wizard
   heldout trace row.
2. Verify the new partition/reference report records:
   - `captured_calibration_reference_written`
   - `selection_policy_status=deterministic_predeclared_single_prompt_consumed`
   - `post_hoc_selection_status=absent`
   - `partition_disjointness_status=pass`
   - `content_disjointness_status=pass`
   - `provenance_distinctness_status=pass`
   - `overlap_positive_control_status=pass`
   - `synthetic_fallback_positive_control_status=pass`
   - calibration source row hash distinct from the 026 Wizard source row hash.
3. Build the Wizard `OFF_STATIC_REPLAY_HELDOUT` row with the new 028 `calibration_reference.json`.
4. Verify the rebuilt row reports:
   - `calibration_reference_kind=captured_backend_trace_reference`
   - `split_contract_status=captured_calibration_reference_distinct_from_heldout_observation`
   - `heldout_observation_source_hash=3a4569e77c39733a4d13034e3ad9cdfc5879e1974b9561760c06703e38d06a76`
   - no synthetic reference in the accepted row.
5. Run the evaluator precondition with scoring disabled.
6. Scan committed 028 artifacts for raw selected-source and calibration utterance leakage.
7. Run route/repo checks and scoped closeout.

Stop instead of proceeding if current scripts cannot produce a new 028 partition/reference report against the 026 Wizard
heldout row.

## Actual Implementation Results - 2026-06-27

Commands run:

```powershell
node EgoDesktop/scripts/build-joi-g-ablation-calibration-reference.js --calibration-rows artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/capture/calibration_ui_predeclared_single/trace/trace_rows.jsonl --heldout-rows artifacts/egodesktop_joi_real_loop_g_ablation_wizard_selected_source_chat_smoke_v0/trace/trace_rows.jsonl --predeclared-calibration-prompt-pack artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/capture/calibration_ui_predeclared_single/PREDECLARED_CALIBRATION_PROMPT_PACK.json --out artifacts/egodesktop_joi_real_loop_g_ablation_wizard_captured_calibration_reference_replay_preflight_v0/calibration_reference --run-id egodesktop_gablation_028_wizard_captured_calibration_reference
node EgoDesktop/scripts/build-joi-g-ablation-off-static-replay-heldout.js --source-rows artifacts/egodesktop_joi_real_loop_g_ablation_wizard_selected_source_chat_smoke_v0/trace/trace_rows.jsonl --calibration-reference artifacts/egodesktop_joi_real_loop_g_ablation_wizard_captured_calibration_reference_replay_preflight_v0/calibration_reference/calibration_reference.json --out artifacts/egodesktop_joi_real_loop_g_ablation_wizard_captured_calibration_reference_replay_preflight_v0/replay --run-id egodesktop_gablation_028_wizard_captured_reference_off_static_replay
node EgoDesktop/scripts/evaluate-joi-g-ablation-replay.js --rows artifacts/egodesktop_joi_real_loop_g_ablation_wizard_captured_calibration_reference_replay_preflight_v0/replay/trace_rows.jsonl --out artifacts/egodesktop_joi_real_loop_g_ablation_wizard_captured_calibration_reference_replay_preflight_v0/eval --run-id egodesktop_gablation_028_wizard_captured_reference_replay_eval --require-007-scoring-precondition --required-condition OFF_STATIC_REPLAY_HELDOUT
```

Evidence paths:

- `artifacts/egodesktop_joi_real_loop_g_ablation_wizard_captured_calibration_reference_replay_preflight_v0/calibration_reference/calibration_reference_report.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_wizard_captured_calibration_reference_replay_preflight_v0/calibration_reference/partition/SPLIT_PARTITION_MANIFEST.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_wizard_captured_calibration_reference_replay_preflight_v0/replay/builder_report.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_wizard_captured_calibration_reference_replay_preflight_v0/replay/trace_rows.jsonl`
- `artifacts/egodesktop_joi_real_loop_g_ablation_wizard_captured_calibration_reference_replay_preflight_v0/eval/evaluation_report.json`

Key results:

- `captured_calibration_reference_written`
- `selection_policy_status=deterministic_predeclared_single_prompt_consumed`
- `post_hoc_selection_status=absent`
- `partition_disjointness_status=pass`
- `content_disjointness_status=pass`
- `provenance_distinctness_status=pass`
- `overlap_positive_control_status=pass`
- `synthetic_fallback_positive_control_status=pass`
- `calibration_reference_kind=captured_backend_trace_reference`
- `split_contract_status=captured_calibration_reference_distinct_from_heldout_observation`
- `heldout_observation_source_hash=3a4569e77c39733a4d13034e3ad9cdfc5879e1974b9561760c06703e38d06a76`
- `replay_integrity_preflight_pass_no_verdict`
- `d_field_replay_precondition_satisfied=true`
- `scoring_run_authorized=false`
- `verdict_authorized=false`

Raw text boundary:

- `raw_text_field_scan_status=pass` for raw-text-bearing keys in the 028 artifact directory.

Claim boundary:

- This is offline artifact-only preflight evidence. It does not prove `CREATURE_ON`, scoring, same-access baseline,
  attribution, route advancement, runtime integration safety, stable user benefit, durable memory efficacy, agency,
  emotion, subjectivity, consciousness, alive status, or Bar-2 specialness.
