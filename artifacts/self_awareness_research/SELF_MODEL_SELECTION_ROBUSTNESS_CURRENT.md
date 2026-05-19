# Operational Selection Robustness Audit

> AUTO-GENERATED ROBUSTNESS REPORT.
> This audit tests ranking stability, not consciousness.

## Summary

- generated_at: `2026-04-09T16:50:50Z`
- git_commit_short: `62e54bd`
- seeds: `[20260409, 20260410, 20260411, 20260412, 20260413]`
- splits: `['balanced', 'identity_stress', 'repair_stress']`
- weight_scenarios: `35`
- scenario_count: `525`
- mvs_remains_robust_first_choice: `True`
- conclusion: MVS-aligned compact remains the robust build-first choice under the current synthetic audit.

## Candidate Summary

| candidate | win_rate | mean_rank | rank_variance | top2_rate | weight_rank_change_rate | mean_weight_score_delta |
|---|---:|---:|---:|---:|---:|---:|
| Baseline chat | 0.0000 | 6.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0042 |
| Narrative identity shell | 0.0000 | 7.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0044 |
| Identity anchor only | 0.0000 | 4.9886 | 0.0113 | 0.0000 | 0.0118 | 0.0052 |
| Corrective trace only | 0.0000 | 4.0114 | 0.0113 | 0.0000 | 0.0118 | 0.0053 |
| Operational self-loop core | 0.0000 | 3.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0019 |
| MVS-aligned compact | 0.9867 | 1.0133 | 0.0132 | 1.0000 | 0.0137 | 0.0006 |
| Active-inference self-model | 0.0133 | 1.9867 | 0.0132 | 1.0000 | 0.0137 | 0.0018 |

## Baseline Weight Winners

- `MVS-aligned compact`: `15`

## Pairwise Focus: MVS vs Active

| split | seed | baseline_winner | mvs_rank | active_rank | mvs_build_first | active_build_first |
|---|---:|---|---:|---:|---:|---:|
| balanced | 20260409 | mvs_aligned_compact | 1 | 2 | 0.7956 | 0.7827 |
| balanced | 20260410 | mvs_aligned_compact | 1 | 2 | 0.7957 | 0.7840 |
| balanced | 20260411 | mvs_aligned_compact | 1 | 2 | 0.7954 | 0.7836 |
| balanced | 20260412 | mvs_aligned_compact | 1 | 2 | 0.7970 | 0.7847 |
| balanced | 20260413 | mvs_aligned_compact | 1 | 2 | 0.7959 | 0.7835 |
| identity_stress | 20260409 | mvs_aligned_compact | 1 | 2 | 0.7959 | 0.7835 |
| identity_stress | 20260410 | mvs_aligned_compact | 1 | 2 | 0.7956 | 0.7845 |
| identity_stress | 20260411 | mvs_aligned_compact | 1 | 2 | 0.7953 | 0.7838 |
| identity_stress | 20260412 | mvs_aligned_compact | 1 | 2 | 0.7964 | 0.7833 |
| identity_stress | 20260413 | mvs_aligned_compact | 1 | 2 | 0.7946 | 0.7834 |
| repair_stress | 20260409 | mvs_aligned_compact | 1 | 2 | 0.7957 | 0.7834 |
| repair_stress | 20260410 | mvs_aligned_compact | 1 | 2 | 0.7950 | 0.7839 |
| repair_stress | 20260411 | mvs_aligned_compact | 1 | 2 | 0.7954 | 0.7836 |
| repair_stress | 20260412 | mvs_aligned_compact | 1 | 2 | 0.7957 | 0.7832 |
| repair_stress | 20260413 | mvs_aligned_compact | 1 | 2 | 0.7963 | 0.7836 |

## Robustness Rule

- baseline_split_seed_sweeps_all: MVS must win all baseline-weight seed/split runs
- overall_win_rate_floor: `0.5`
- top2_rate_floor: `0.95`
- challenger_overall_win_rate_ceiling: `0.35`

## Interpretation

- A candidate can only win if it still passes the unweighted operational target gate.
- Weight sensitivity is measured as the fraction of non-baseline weight scenarios where the candidate's rank changes relative to the same seed/split baseline.
