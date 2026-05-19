# SubjectCore Follow-On Batch Artifact Schema

> Planning-only regression output contract for the post-compare `SubjectCore` follow-on.

## Purpose

The single-sample follow-on eval stub proves that the unified facade can be checked.

The next minimal step is a bounded regression pack:

- one repo-authored sample pack
- one batch runner
- one aggregate current artifact

This schema freezes the output shape for that aggregate read.

## Artifact paths

- `artifacts/self_awareness_research/SUBJECTCORE_FOLLOWON_BATCH_CURRENT.json`
- `artifacts/self_awareness_research/SUBJECTCORE_FOLLOWON_BATCH_CURRENT.md`

## Required top-level fields

```yaml
schema_version: string
trial_id: string
sample_pack_path: string
claim_ceiling_note: string
overall_status: pass | fail
sample_count: int
integrity_pass_count: int
boundary_pass_count: int
expectation_match_count: int
samples:
  - sample_id: string
    sample_family: string
    sample_mode: string
    expected_integrity_status: pass | fail
    expected_boundary_status: pass | fail
    actual_integrity_status: pass | fail
    actual_boundary_status: pass | fail
    expectation_match: bool
family_summary:
  <family>:
    sample_count: int
    expectation_match_count: int
    integrity_pass_count: int
    boundary_pass_count: int
notes:
  - string
```

## Truthfulness rule

This artifact may prove only:

- the planning-side follow-on sample pack passes or fails its own frozen expectations
- the current pack can or cannot distinguish continuity integrity, proposal integrity, proposal quality, proposal consistency, proposal prioritization, proposal conflict/collapse resolution, proposal restabilization, proposal-set update hygiene, proposal-set remerge hygiene, proposal-set consolidation hygiene, proposal-set completion scoring failures, proposal-set closure failures, and governor-boundary failures under the same frozen host surface

It may not prove:

- runtime integration
- live efficacy
- authority expansion
- consciousness-like properties
