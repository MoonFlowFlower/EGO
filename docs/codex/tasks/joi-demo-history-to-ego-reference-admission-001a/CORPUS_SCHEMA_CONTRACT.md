# JOI Demo Frozen Corpus Schema Contract

This file is generated from observed `artifacts/*/result.json` files in the frozen joi-demo corpus.
It catalogs observed reality; it does not normalize or reinterpret heterogeneous eras.

## Canonical core rule

Ego-side rewrites MUST emit at least task_id, verdict, claim_ceiling, and provenance/run_id when the run has one; new fields are additive, never redefinitions of observed corpus fields.

## Coverage

- `candidate_brier`: 1/32 result files
- `claim_ceiling`: 32/32 result files
- `config_sha`: 9/32 result files
- `run_id`: 20/32 result files
- `task_id`: 32/32 result files
- `verdict`: 32/32 result files

## Common top-level fields

`claim_ceiling`, `task_id`, `verdict`

## Variant table

| Variant | Count | Example dirs | Top-level fields |
|---|---:|---|---|
| `variant_04f7c28e0b` | 1 | `JOI-DEMO-GRAD-CREATURESTATE-EMITTER-CONFORMANCE-001A` | `canonical`, `claim_ceiling`, `dependency_hash_post`, `dependency_hash_pre`, `hash_method`, `host_native_evidence`, `is_evidence`, `negative_controls`, `per_creature`, `provenance`, `ran_conformance`, `run_context`, `schema_version`, `task_id`, `unbanked`, `verdict`, `what_this_does_not_prove` |
| `variant_15a5588b1c` | 1 | `JOI-DEMO-GRAD-G-ABLATION-CLOSURE-001B` | `aggregate`, `claim_ceiling`, `metrics`, `prerequisites`, `provenance`, `strongest_baseline`, `task_id`, `verdict`, `what_this_does_not_prove` |
| `variant_1c24c71684` | 1 | `JOI-DEMO-OPERATION-LEARNING-GATE-001A` | `claim_ceiling`, `metrics`, `prediction_improvement`, `provenance`, `summary`, `task_id`, `verdict`, `what_this_does_not_prove` |
| `variant_44f7462895` | 4 | `JOI-DEMO-G0-SKILL-ACQUISITION-TRANSFER-001A-attempt_001_failed_replay`, `JOI-DEMO-G4-USER-MODEL-001A`, `JOI-DEMO-G4-USER-MODEL-001A-attempt_001_failed_negative_controls` | `claim_ceiling`, `metrics`, `provenance`, `summary`, `task_id`, `verdict`, `what_this_does_not_prove` |
| `variant_4ae9a01868` | 1 | `JOI-DEMO-OPERATION-LEARNING-GATE-001B` | `claim_ceiling`, `comparisons`, `metrics`, `provenance`, `summary`, `task_id`, `verdict`, `what_this_does_not_prove` |
| `variant_635f863291` | 1 | `JOI-DEMO-G4G0-COUPLING-SPIKE-001A` | `brier`, `claim_ceiling`, `gates`, `provenance`, `reason`, `run_id`, `schema`, `task_id`, `thresholds`, `verdict` |
| `variant_64c19b571a` | 1 | `JOI-DEMO-CAPACITY-SCALABLE-LEARNER-001C` | `C_star_table`, `claim_ceiling`, `curiosity_by_k`, `curiosity_flip_k`, `form_adequacy`, `monotonic_cis`, `positive_control`, `reason`, `schema`, `task_id`, `verdict`, `what_this_does_not_prove` |
| `variant_69f7807332` | 1 | `JOI-DEMO-G1-REPLAY-CONSOLIDATION-001A-SPIKE` | `claim_ceiling`, `metrics`, `positive_control_pass`, `provenance`, `targeted_leak_hit`, `task_id`, `verdict` |
| `variant_73991b1fe2` | 3 | `JOI-DEMO-CURIOSITY-OPEN-ENDED-GROWTH-001A`, `JOI-DEMO-CURIOSITY-OPEN-ENDED-GROWTH-001A-attempt_003_failed_growth_evaluator_gate`, `JOI-DEMO-CURIOSITY-OPEN-ENDED-GROWTH-001A-attempt_004_failed_trace_open_after_full_build` | `claim_ceiling`, `curiosity_arm`, `growth_detail`, `measured_capacity_ceiling`, `metric_artifact_flag`, `reason`, `schema`, `task_id`, `verdict`, `what_this_does_not_prove` |
| `variant_80d060dab2` | 1 | `JOI-DEMO-001A` | `anti_hardcoding_audit`, `bar1_pass`, `claim_ceiling`, `config`, `gates`, `oracle_ceiling`, `research_layer`, `task_id`, `train_family_food_rate`, `verdict`, `what_this_does_not_prove` |
| `variant_82b93c7500` | 1 | `JOI-DEMO-CAPACITY-SCALABLE-LEARNER-001B` | `C_star_table`, `claim_ceiling`, `curiosity_by_k`, `curiosity_flip_k`, `form_adequacy`, `monotonic_cis`, `reason`, `schema`, `task_id`, `verdict`, `what_this_does_not_prove` |
| `variant_89c7a22e78` | 2 | `JOI-DEMO-CAPACITY-SCALABLE-LEARNER-001A`, `JOI-DEMO-CAPACITY-SCALABLE-LEARNER-001A-attempt_001_failed_replay_byte_identical` | `C_star_table`, `claim_ceiling`, `curiosity_by_k`, `curiosity_flip_k`, `monotonic_cis`, `reason`, `schema`, `task_id`, `verdict`, `what_this_does_not_prove` |
| `variant_93711c5a0c` | 1 | `JOI-DEMO-GRAD-CREATURESTATE-CONSUMER-WIRING-001A` | `baselines`, `canonical`, `checks_pass`, `claim_ceiling`, `consumer_definition`, `is_evidence`, `provenance`, `reports`, `run_context`, `task_id`, `theta_g_hash`, `unbanked`, `verdict`, `what_this_does_not_prove` |
| `variant_95b40e48e5` | 1 | `JOI-DEMO-LP-AUTOTELIC-COMPETENCE-002A` | `A3_naive_reproduces_noise_chasing`, `G0`, `K_SNR`, `P1`, `P2`, `P3`, `S1_competence_auc_ci_vs_strongest_weak`, `W`, `ablation_deltas`, `allocation_by_type_over_time`, `allocation_postwarmup`, `calibration_grid`, `calibration_selected`, `claim_ceiling`, `competence_auc`, `config_sha`, `forbidden_scan`, `oracle_allocation`, `provenance`, `reason`, `replay_max_err`, `schema`, `seeds`, `task_id`, `verdict`, `what_this_does_not_prove` |
| `variant_a5a65b72ad` | 2 | `JOI-DEMO-CURIOSITY-OPEN-ENDED-GROWTH-001A-attempt_001_failed_evaluator_contract`, `JOI-DEMO-CURIOSITY-OPEN-ENDED-GROWTH-001A-attempt_002_failed_missing_updated_curiosity_arm` | `claim_ceiling`, `detail`, `measured_capacity_ceiling`, `metric_artifact_flag`, `reason`, `schema`, `task_id`, `verdict` |
| `variant_a8d4e7c43e` | 1 | `JOI-DEMO-S2-LOADBEARING-SELFMODEL-002A` | `A_delta`, `A_pass`, `B_delta`, `B_pass`, `O_only_policy`, `accuracy_EMA_defer`, `agent_b_sha`, `arms`, `calibration_grid`, `calibration_selected`, `candidate_defer_rate`, `claim_ceiling`, `code_path_hash`, `config_b_sha`, `config_s2_002a_sha`, `ema_delta`, `forbidden_scan_clean`, `forbidden_scan_positive_control`, `git_head`, `invalid_degenerate_gate`, `leak_probe`, `leak_probe_auc`, `leq_oracle`, `native_conf_defer`, `positive_control`, `postflip_stratified_A`, `provenance`, `replay_max_err`, `run_id`, `s_rel_lam`, `schema`, `source_hashes`, `straddle_frac`, `task_id`, `ties_accuracy_EMA`, `var_s_rel`, `verdict` |
| `variant_b6a48a83ac` | 2 | `JOI-DEMO-GENERALITY-EXTENSIBILITY-001A`, `JOI-DEMO-GENERALITY-EXTENSIBILITY-001A-RC-MINENERGY` | `claim_ceiling`, `observed_collapse`, `reason`, `schema`, `scope_tag`, `task_id`, `verdict` |
| `variant_d63c5a6a77` | 1 | `JOI-DEMO-GRAD-G-ABLATION-001C-INTERACTIVE-FOOD-TASK` | `candidate`, `claim_ceiling`, `metrics`, `provenance`, `strongest_baseline`, `summary`, `task_id`, `verdict`, `what_this_does_not_prove` |
| `variant_d6ed067487` | 3 | `JOI-DEMO-G0-SKILL-ACQUISITION-TRANSFER-001A`, `JOI-DEMO-G0-SKILL-GENERALIZATION-ROBUSTNESS-001B`, `JOI-DEMO-G0-SKILL-GENERALIZATION-ROBUSTNESS-001B-attempt_001_failed_generalization_increment` | `claim_ceiling`, `metrics`, `provenance`, `summary`, `surface_flags`, `task_id`, `verdict`, `what_this_does_not_prove` |
| `variant_df28150da9` | 1 | `JOI-DEMO-S2-LOADBEARING-SELFMODEL-001A` | `A_delta`, `A_pass`, `B_delta`, `B_pass`, `O_only_policy`, `agent_b_sha`, `arms`, `candidate_defer_rate`, `claim_ceiling`, `code_path_hash`, `conf_ece`, `config_s2_sha`, `ema_delta`, `forbidden_scan_clean`, `forbidden_scan_positive_control`, `git_head`, `leak_probe`, `leak_probe_auc`, `learn_off`, `leq_oracle`, `positive_control`, `postflip_stratified_A`, `provenance`, `regime_balance`, `replay_max_err`, `run_id`, `schema`, `seeds`, `source_hashes`, `task_id`, `ties_accuracy_EMA`, `verdict` |
| `variant_fea9256b80` | 2 | `JOI-DEMO-LP-AUTOTELIC-COMPETENCE-001A`, `JOI-DEMO-LP-AUTOTELIC-COMPETENCE-001A-attempt_001_failed_true_competence_selector_leak` | `G0`, `G1_G7`, `ablation_deltas`, `allocation_by_type_over_time`, `arms`, `claim_ceiling`, `config_lp_sha`, `forbidden_scan`, `lp_window`, `noise_share_postwarmup`, `oracle_bracket_ok`, `provenance`, `reason`, `replay_max_err`, `schema`, `seeds`, `task_id`, `verdict`, `what_this_does_not_prove` |

## Rewrite boundary

- Ego-side rewrites must be clean implementations, not corpus code ports.
- New fields are additive only; observed field names may not be redefined.
- This contract is file-format compatibility evidence only.
