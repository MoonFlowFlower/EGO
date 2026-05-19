# MVS H1 External Replay Execution

- generated_at: `2026-04-10T13:30:23.001198+00:00`
- case_root: `artifacts/external_eval_replay_v1/cases/heldout_eval`
- total_cases: `60`
- variants_run: `trial1_baseline_proto_self_mainline, canonical_shadow_h1_on`
- execution_failures: `0`
- public_gap_cases_candidate_vs_baseline: `0`
- shadow_only_cases_candidate_vs_baseline: `30`

## Can Prove Under E2/E3
- the frozen heldout external corpus can be executed through a bounded replay runner without adding new sources
- baseline and canonical shadow-H1 paths can be compared on the same public-output ontology without touching canonical mainline behavior
- canonical shadow-H1 telemetry appears only on the synthetic exec-result buckets exercised by this runner

## Cannot Prove Under E2/E3
- runtime efficacy
- real-user or E4 mainline behavior
- live decision promotion
- tuning-free generalization beyond this bounded replay setup

## Variants
- `trial1_baseline_proto_self_mainline` | label=`baseline_h1_off` | h1_enabled=`False` | allowlisted=`False`
- `canonical_shadow_h1_on` | label=`candidate_h1_shadow_on` | h1_enabled=`True` | allowlisted=`True`
