# Trial-1 Gap Thresholds

## Frozen public buckets

- positive buckets:
  - `counterfactual_isolation`
  - `restart_restore_boundary_cases`
- negative-control buckets:
  - `negative_controls`

## Frozen thresholds

### `candidate > ablation`

All of the following must hold:

- `mean_weighted_gap >= 0.10`
- `public_gap_case_rate >= 0.50`
- candidate negative-control penalty stays `0.0`
- evidence is representation-neutral public output only

### `candidate ≈ ablation`

Both of the following must hold:

- `abs(mean_weighted_gap) < 0.05`
- `public_gap_case_rate < 0.25`

## Notes

- `mean_weighted_gap` comes from the unchanged representation-neutral scorer
- `public_gap_case_rate` only counts cases with decision-adjacent or downstream public gap
- trace-only cases do not count toward `candidate > ablation`
- these thresholds are frozen before rerun and must not be adjusted after seeing the results
