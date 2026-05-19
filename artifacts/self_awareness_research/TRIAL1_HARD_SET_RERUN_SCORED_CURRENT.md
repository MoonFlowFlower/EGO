# Trial-1 Shadow Replay Scored Report

- generated_at: `2026-04-09T22:19:09.098808+00:00`
- source_artifact: `artifacts/self_awareness_research/TRIAL1_HARD_SET_RERUN_CURRENT.json`
- candidate_id: `trial1_candidate_mvs_aligned_compact`
- challenger_status: `live_not_scored`

## Level Summary

- `trial1_baseline_proto_self_mainline`: admission=False, decision_adjacent=False, replay_efficacy=False, weighted=0.0000, decision=0.0000, response=0.0000, policy=0.0000, trace=0.0000
- `trial1_candidate_mvs_aligned_compact`: admission=True, decision_adjacent=True, replay_efficacy=False, weighted=0.0500, decision=0.0000, response=0.0000, policy=0.2500, trace=0.0000
- `trial1_ablation_counterfactual_public_path_sever`: admission=False, decision_adjacent=False, replay_efficacy=False, weighted=0.0000, decision=0.0000, response=0.0000, policy=0.0000, trace=0.0000
- `trial1_ablation_alternative_explanation_isolation`: admission=True, decision_adjacent=True, replay_efficacy=False, weighted=0.0500, decision=0.0000, response=0.0000, policy=0.2500, trace=0.0000

## Ablation Separation

- `trial1_ablation_counterfactual_public_path_sever`: mean_weighted_gap=0.0500, positive_gap_cases=8
- `trial1_ablation_alternative_explanation_isolation`: mean_weighted_gap=0.0000, positive_gap_cases=0

## Reading

- `admission_passed` can be supported by trace-only shift, but only when negative controls stay clean.
- `decision_adjacent_passed` requires public-output movement on representation-neutral policy/response surfaces.
- `replay_efficacy_passed` requires downstream decision-surface change and ablation separation. The current Trial-1 artifact does not meet that bar.
