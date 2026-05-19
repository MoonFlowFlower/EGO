# Trial-1 Shadow Replay Scored Report

- generated_at: `2026-04-09T20:34:11.225720+00:00`
- source_artifact: `/mnt/d/Project/AIProject/MyProject/Ego/artifacts/self_awareness_research/TRIAL1_SHADOW_REPLAY_CURRENT.json`
- candidate_id: `trial1_candidate_mvs_aligned_compact`
- challenger_status: `live_not_implemented`

## Level Summary

- `trial1_baseline_proto_self_mainline`: admission=False, decision_adjacent=False, replay_efficacy=False, weighted=0.0000, decision=0.0000, response=0.0000, policy=0.0000, trace=0.0000
- `trial1_candidate_mvs_aligned_compact`: admission=True, decision_adjacent=True, replay_efficacy=False, weighted=0.4125, decision=0.5000, response=0.0000, policy=0.4375, trace=1.0000
- `trial1_ablation_minus_counterfactual_writeback`: admission=True, decision_adjacent=True, replay_efficacy=False, weighted=0.4125, decision=0.5000, response=0.0000, policy=0.4375, trace=1.0000
- `trial1_ablation_minus_viability_pressure`: admission=True, decision_adjacent=True, replay_efficacy=False, weighted=0.1500, decision=0.0000, response=0.0000, policy=0.2500, trace=1.0000
- `trial1_ablation_minus_corrective_trace`: admission=True, decision_adjacent=True, replay_efficacy=False, weighted=0.3125, decision=0.5000, response=0.0000, policy=0.4375, trace=0.0000

## Ablation Separation

- `trial1_ablation_minus_counterfactual_writeback`: mean_weighted_gap=0.0000, positive_gap_cases=0
- `trial1_ablation_minus_viability_pressure`: mean_weighted_gap=0.2625, positive_gap_cases=3
- `trial1_ablation_minus_corrective_trace`: mean_weighted_gap=0.1000, positive_gap_cases=4

## Reading

- `admission_passed` can be supported by trace-only shift, but only when negative controls stay clean.
- `decision_adjacent_passed` requires public-output movement on representation-neutral policy/response surfaces.
- `replay_efficacy_passed` requires downstream decision-surface change and ablation separation. The current Trial-1 artifact does not meet that bar.
