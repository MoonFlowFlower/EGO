# Trial-1 Causal Separation Report

- generated_at: `2026-04-09T21:12:27.581535+00:00`
- source_raw: `/mnt/d/Project/AIProject/MyProject/Ego/artifacts/self_awareness_research/TRIAL1_SHADOW_REPLAY_CURRENT.json`
- source_scored: `/mnt/d/Project/AIProject/MyProject/Ego/artifacts/self_awareness_research/TRIAL1_SHADOW_REPLAY_SCORED_CURRENT.json`
- hard_set: `/mnt/d/Project/AIProject/MyProject/Ego/docs/codex/tasks/ai-self-awareness-minimal-framework/TRIAL1_COUNTERFACTUAL_HARD_SET.json`
- final_decision: `redesign_ablation`

## Variant Summary

| Variant | Admission | Decision Adjacent | Replay Efficacy | Weighted | Decision | Policy | Trace |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `trial1_baseline_proto_self_mainline` | `False` | `False` | `False` | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| `trial1_candidate_mvs_aligned_compact` | `True` | `True` | `False` | 0.4125 | 0.5000 | 0.4375 | 1.0000 |
| `trial1_ablation_minus_counterfactual_writeback` | `True` | `True` | `False` | 0.4125 | 0.5000 | 0.4375 | 1.0000 |
| `trial1_ablation_minus_viability_pressure` | `True` | `True` | `False` | 0.1500 | 0.0000 | 0.2500 | 1.0000 |

## Current Gap

- candidate vs strongest ablation gap cases: `0`
- candidate vs strongest ablation private-only cases: `4`
- candidate vs strongest ablation public-gap steps: `0`
- candidate vs neighboring ablation gap cases: `4`

## Reachability Diagnosis

- failure/blocked updates set both recent_correction_tags and low counterfactual prediction together
- derive_policy_hint turns on ask_preferred for either correction_pressure >= 0.6 or viability_pressure >= 0.5 before counterfactual-only isolation matters
- success-after-correction decays correction tags but also restores counterfactual prediction to >= 0.65
- therefore the current Trial-1 path does not naturally expose a low-prediction/public-gap phase after correction pressure has decayed

## Hard Set

- diagnostic_case_count: `10`
- positive_isolation_cases: `8`
- negative_control_cases: `2`
- note: this hard set is diagnostic-only and does not upgrade the official replay suite.

## Decision

- `redesign_ablation`
- candidate does not beat the strongest ablation on any current representation-neutral case
- the strongest ablation differs only on private-state fields the scorer intentionally ignores
- the current update rules make counterfactual-only public separation unreachable on the existing Trial-1 path
- claim_change: demote the narrow claim that counterfactual_writeback is already shown as a replay-efficacy contributor under the current ontology
