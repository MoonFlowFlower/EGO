# Implementation

## Current Slice - Task Card Only

This slice writes planning/governance files only. It does not run the calibration-reference builder, OFF_STATIC heldout
builder, replay evaluator, Electron smoke, same-access baseline, scoring, or `CREATURE_ON`.

Card acceptance readback must include:

- current layer: `engineering planning / captured calibration reference replay preflight card`
- mainline status: `not_connected_to_default_runtime`
- enabled status: `task_card_only_no_artifact_run`
- real trigger evidence: `planned_reuse_of_009_calibration_row_and_026_wizard_heldout_row`
- claim ceiling: `wizard_captured_calibration_reference_replay_card_only`

## Future Implementation Skeleton

If later authorized, the implementation must:

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
