# MVS Replay Validator Scored

- generated_at: `2026-04-11T07:51:36.121102+00:00`
- selection_decision: `switch_to_active_inference`
- candidate_pass: `False`

## Target Scores

- `mvs_baseline_proto_self_mainline`: composite=`0.5333` T1=`1.0` T2=`0.75` T3=`0.3333` T4=`0.3333` T5=`0.25`
- `mvs_candidate_aligned_compact`: composite=`0.9` T1=`1.0` T2=`1.0` T3=`1.0` T4=`0.5833` T5=`0.9167`
- `mvs_minus_counterfactual_writeback`: composite=`0.8333` T1=`1.0` T2=`1.0` T3=`0.6667` T4=`0.5833` T5=`0.9167`
- `mvs_minus_viability_pressure`: composite=`0.85` T1=`1.0` T2=`1.0` T3=`1.0` T4=`0.3333` T5=`0.9167`
- `mvs_minus_corrective_trace`: composite=`0.7667` T1=`1.0` T2=`1.0` T3=`1.0` T4=`0.5833` T5=`0.25`
- `mvs_minus_boundary_confidence`: composite=`0.8167` T1=`0.75` T2=`0.75` T3=`1.0` T4=`0.6667` T5=`0.9167`
- `baseline_chat_surface`: composite=`0.0` T1=`0.0` T2=`0.0` T3=`0.0` T4=`0.0` T5=`0.0`

## Selection

- target_deltas_vs_baseline_a: `{'T1': 0.0, 'T2': 0.25, 'T3': 0.6667, 'T4': 0.25, 'T5': 0.6667}`
- composite_delta_vs_baseline_a: `0.3667`
- ablation_drops: `{'counterfactual': 0.3333, 'viability': 0.25, 'corrective_trace': 0.6667, 'boundary_confidence': 0.25}`
- weak_ablations: `[]`
- challenger_status: `not_run`
