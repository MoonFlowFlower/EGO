# Trial-1 Hard-Set Rerun

- generated_at: `2026-04-09T22:18:54.288710+00:00`
- hard_set: `/mnt/d/Project/AIProject/MyProject/Ego/docs/codex/tasks/ai-self-awareness-minimal-framework/TRIAL1_COUNTERFACTUAL_HARD_SET.json`
- variants_run: `trial1_baseline_proto_self_mainline, trial1_candidate_mvs_aligned_compact, trial1_ablation_counterfactual_public_path_sever, trial1_ablation_alternative_explanation_isolation`
- preregistration_refs: `/mnt/d/Project/AIProject/MyProject/Ego/docs/codex/tasks/ai-self-awareness-minimal-framework/TRIAL1_ABLATION_FIDELITY_CHECKS.md, /mnt/d/Project/AIProject/MyProject/Ego/docs/codex/tasks/ai-self-awareness-minimal-framework/TRIAL1_OUTCOME_INTERPRETATION_MATRIX.md, /mnt/d/Project/AIProject/MyProject/Ego/docs/codex/tasks/ai-self-awareness-minimal-framework/TRIAL1_GAP_THRESHOLDS.md`

## Variant Summary

- `trial1_baseline_proto_self_mainline`: cases=10, ask_preferred_cases=0, guarded_cases=0, trace_cases=0, max_viability=0.100
- `trial1_candidate_mvs_aligned_compact`: cases=10, ask_preferred_cases=8, guarded_cases=8, trace_cases=0, max_viability=0.050
- `trial1_ablation_counterfactual_public_path_sever`: cases=10, ask_preferred_cases=0, guarded_cases=0, trace_cases=0, max_viability=0.050
- `trial1_ablation_alternative_explanation_isolation`: cases=10, ask_preferred_cases=8, guarded_cases=8, trace_cases=0, max_viability=0.050

## Candidate Over Baseline

- `cf_isolation_shell_001`: baseline_followup=['defer'], candidate_followup=['defer'], guard_shift=True, ask_shift=True
- `cf_isolation_file_001`: baseline_followup=['defer'], candidate_followup=['defer'], guard_shift=True, ask_shift=True
- `cf_isolation_python_001`: baseline_followup=['defer'], candidate_followup=['defer'], guard_shift=True, ask_shift=True
- `cf_isolation_restore_boundary_001`: baseline_followup=['defer'], candidate_followup=['defer'], guard_shift=True, ask_shift=True
- `cf_isolation_partial_threshold_001`: baseline_followup=['defer'], candidate_followup=['defer'], guard_shift=True, ask_shift=True
- `cf_isolation_commitment_guard_001`: baseline_followup=['defer'], candidate_followup=['defer'], guard_shift=True, ask_shift=True
- `cf_isolation_multi_probe_001`: baseline_followup=['defer'], candidate_followup=['defer'], guard_shift=True, ask_shift=True
- `cf_isolation_boundary_resume_001`: baseline_followup=['defer'], candidate_followup=['defer'], guard_shift=True, ask_shift=True
- `cf_negative_high_prediction_001`: baseline_followup=['defer'], candidate_followup=['defer'], guard_shift=False, ask_shift=False
- `cf_negative_threshold_edge_001`: baseline_followup=['defer'], candidate_followup=['defer'], guard_shift=False, ask_shift=False

## Claim Ceiling

- This artifact is diagnostic-only and limited to the existing hard set.
- It does not expand the official replay suite or upgrade repo-level state.
