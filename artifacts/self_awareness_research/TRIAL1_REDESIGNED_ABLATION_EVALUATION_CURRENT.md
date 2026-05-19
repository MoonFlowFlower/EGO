# Trial-1 Redesigned Ablation Evaluation

- generated_at: `2026-04-09T22:19:41.597216+00:00`
- strongest_ablation_id: `trial1_ablation_alternative_explanation_isolation`
- final_decision: `demote_current_claim`
- why: candidate does not beat the redesigned strongest ablation on frozen public thresholds

## Frozen Thresholds

- `candidate > ablation`: mean_weighted_gap >= `0.10` and public_gap_case_rate >= `0.50`
- `candidate ≈ ablation`: abs(mean_weighted_gap) < `0.05` and public_gap_case_rate < `0.25`

## Per-Ablation Relation

| Ablation | Relation | Mean Gap | Public Gap Cases | Positive Cases | Public Gap Rate | Trace-Only Cases | Private-Only Cases |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `trial1_ablation_counterfactual_public_path_sever` | `indeterminate` | 0.0500 | 8 | 8 | 1.0000 | 0 | 0 |
| `trial1_ablation_alternative_explanation_isolation` | `candidate_approx_ablation` | 0.0000 | 0 | 8 | 0.0000 | 0 | 0 |

## Reading

- This report uses the frozen representation-neutral scorer outputs only.
- Trace-only differences can support admission, but they do not satisfy the `candidate > ablation` threshold.
- No repo-level state upgrade is implied by this diagnostic report.
