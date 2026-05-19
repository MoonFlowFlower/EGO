# Trial-2 Public Driver Decision

- generated_at: `2026-04-09T23:13:48.497150+00:00`
- milestone_decision: `close`
- identified: `true`

## Ranking

- `H1 counterfactual low-success guard`
  - variant_id: `trial1_ablation_counterfactual_public_path_sever`
  - mean_weighted_gap: `0.0500`
  - positive_gap_case_count: `8`
- `H2 correction-pressure public guard`
  - variant_id: `trial2_ablation_correction_public_path_sever`
  - mean_weighted_gap: `0.0000`
  - positive_gap_case_count: `0`
- `H3 viability-pressure public guard`
  - variant_id: `trial2_ablation_viability_public_path_sever`
  - mean_weighted_gap: `0.0000`
  - positive_gap_case_count: `0`

## Claim Ceiling

- bounded_claim: Under the existing scorer and hard set, H1 counterfactual low-success guard is the current bounded active public driver.
- non_claim: This does not identify a universal MVS causal core.
- non_claim: This does not restore any prior public-efficacy claim.
- non_claim: This does not upgrade repo-level state or runtime evidence.

## Rationale

A single sever ablation uniquely carries the non-zero public gap while the other sever ablations remain near candidate. Under the frozen hard set and scorer, this is enough to identify the current bounded active public driver and close Trial-2.
