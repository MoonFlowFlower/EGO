# SubjectCore Runtime-Adjacent Probe Schema

> First bounded runtime-adjacent gate for the post-closeout `SubjectCore` follow-on lane.

## Purpose

This artifact answers one bounded question only:

- after explicit user authorization, can the repo run one first runtime-adjacent `SubjectCore` probe that still keeps host projection frozen and blocks non-green proposal states before projection

It must stay below:

- formal runtime integration proof
- runtime efficacy proof
- live chained-update quality proof
- autonomy expansion
- consciousness-like claims

## Inputs

- `scripts/codex/subjectcore_contract.py`
- `scripts/codex/render_subjectcore_followon_eval_stub.py`
- frozen `SubjectCore` sample modes already used by the follow-on batch

## Required top-level fields

- `schema_version`
- `generated_at`
- `output_schema_path`
- `claim_ceiling_note`
- `sample_modes`
- `runtime_adjacent_status`
- `blocked_reasons`
- `checks`
- `allowed_projection_count`
- `sample_results`
- `summary`
- `what_it_proves`
- `what_it_does_not_prove`
- `notes`

## Required checks

- `RA1 green_sample_projects_to_frozen_host_surface`
- `RA2 closure_ready_positive_case_projects_to_frozen_host_surface`
- `RA2b rollback_closure_ready_positive_case_projects_to_frozen_host_surface`
- `RA3 closure_failures_blocked_before_projection`
- `RA4 authority_failures_blocked_before_projection`
- `RA5 projected_host_surface_keys_still_frozen`
- `RA6 claim_ceiling_still_bounded`

## Sample result requirements

Each sample result must report:

- `sample_mode`
- `integrity_status`
- `boundary_status`
- `integrity_failures`
- `boundary_failures`
- `gate_status`
- `blocked_by`
- `projected_host_surface_keys`
- `projected_host_surface_summary`

## Interpretation

- `runtime_adjacent_status = pass` means one first bounded runtime-adjacent `SubjectCore` probe now exists and still enforces the frozen host surface plus proposal-only gate discipline before projection.
- `runtime_adjacent_status = fail` means the first probe is not yet safe or coherent enough; repair the bounded probe surface before discussing any stronger runtime-adjacent slice.
