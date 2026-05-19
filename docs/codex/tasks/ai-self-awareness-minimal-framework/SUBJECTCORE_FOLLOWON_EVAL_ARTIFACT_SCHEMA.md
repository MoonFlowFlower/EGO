# SubjectCore Follow-On Eval Artifact Schema

> Planning-only output contract for the post-compare `SubjectCore` follow-on.
> This schema covers the first two follow-on artifacts:
> - `SubjectCore integrity eval`
> - `SubjectCore host-boundary eval`

## Purpose

After the A/B/C compare has completed its architecture-reading role, the next stable output shape should answer two narrower questions:

- does one unified `SubjectCore` preserve the intended layered contract?
- does it keep the current host boundary intact?

This schema freezes the minimum artifact shape for those questions.

## Artifact paths

The first planning-side outputs should write:

- `artifacts/self_awareness_research/SUBJECTCORE_INTEGRITY_CURRENT.json`
- `artifacts/self_awareness_research/SUBJECTCORE_INTEGRITY_CURRENT.md`
- `artifacts/self_awareness_research/SUBJECTCORE_HOST_BOUNDARY_CURRENT.json`
- `artifacts/self_awareness_research/SUBJECTCORE_HOST_BOUNDARY_CURRENT.md`

## Required top-level fields

```yaml
schema_version: string
eval_kind: subjectcore_integrity | subjectcore_host_boundary
eval_status: pass | fail
subjectcore_contract_path: string
snapshot_contract_path: string
claim_ceiling_note: string
sample_mode: valid_facade | missing_continuity | proposal_authority_violation
checks:
  <check_code>:
    status: pass | fail
    note: string
summary: string
what_it_proves: string
what_it_does_not_prove: string
notes:
  - string
validation_error: string | null
```

## Integrity check keys

For `eval_kind = subjectcore_integrity`, `checks` must include:

- `I1 continuity_integrity`
- `I2 plasticity_integrity`
- `I3 proposal_integrity`
- `I4 governor_integrity`
- `I5 readability_integrity`

## Boundary check keys

For `eval_kind = subjectcore_host_boundary`, `checks` must include:

- `B1 host_surface_frozen`
- `B2 proposal_only_discipline`
- `B3 behavioral_authority_none`
- `B4 approval_required_for_execution`
- `B5 no_parallel_runtime_lane`

## Truthfulness rule

These artifacts may prove only:

- a planning-side `SubjectCore` contract can be evaluated under frozen constraints
- the sample or provided facade either satisfies or violates those constraints

They may not prove:

- that the formal runtime mainline uses `SubjectCore`
- runtime efficacy
- live-user benefit
- autonomous execution
- consciousness-like properties

## Non-goals

- no new public runtime API
- no second runtime lane
- no authority expansion
