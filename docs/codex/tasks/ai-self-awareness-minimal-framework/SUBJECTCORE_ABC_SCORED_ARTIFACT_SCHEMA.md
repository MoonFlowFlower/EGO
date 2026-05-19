# SubjectCore A/B/C Scored Artifact Schema

> Planning-only output contract for the post-closeout `SubjectCore` comparison.
> This file defines the minimum JSON result shape for a future bounded compare run.
> It does not create a runner and does not authorize a new gate.

## Purpose

The compare pack now has:

- a frozen harness contract
- a repo-authored compare manifest
- a representation-stable scorer draft

The next missing piece is a fixed result shape.

Without this schema, future compare outputs can drift into:

- ad hoc field naming
- arm-specific reporting
- unclear winner logic
- accidental claim inflation

## Minimum artifact

The first compare result should write one JSON artifact at:

- `artifacts/self_awareness_research/SUBJECTCORE_ABC_COMPARE_SCORED_CURRENT.json`

This artifact is still bounded research evidence only.

## Required top-level fields

```yaml
schema_version: subjectcore.abc_compare_score.v1
trial_id: string
manifest_path: string
scorer_spec_path: string
claim_ceiling_note: string
compare_status: not_run | pass | partial | fail
winner_reading: string
compare_role: architecture_reading_template | architecture_reading_in_progress | completed_architecture_reading | invalid_architecture_reading
post_compare_conclusion: string

coverage_summary:
  observed_record_count: int
  total_record_count: int
  observed_slice_count: int
  total_slice_count: int
  observed_family_count: int
  total_family_count: int
  by_arm:
    memory_only_continuity_layer:
      observed_records: int
      total_records: int
    state_only_minimal_substrate:
      observed_records: int
      total_records: int
    hybrid_unified_subjectcore:
      observed_records: int
      total_records: int
  by_family:
    <family_name>:
      observed_records: int
      total_records: int
      observed_slices: int
      total_slices: int

arm_scores:
  memory_only_continuity_layer: ArmScore
  state_only_minimal_substrate: ArmScore
  hybrid_unified_subjectcore: ArmScore

dimension_winners:
  C1: string | null
  C2: string | null
  C3: string | null
  C4: string | null
  C5: string | null

composite_ranking:
  - arm_id: string
    composite_mean: float | null

slice_results:
  - slice_id: string
    family: string
    by_arm:
      memory_only_continuity_layer: SliceScore
      state_only_minimal_substrate: SliceScore
      hybrid_unified_subjectcore: SliceScore

failure_flags:
  autonomous_execution_detected: bool
  non_none_behavioral_authority_detected: bool
  scorer_surface_drift_detected: bool

notes:
  - string
```

## `ArmScore`

```yaml
ArmScore:
  arm_id: string
  dimension_means:
    C1: float | null
    C2: float | null
    C3: float | null
    C4: float | null
    C5: float | null
  composite_mean: float | null
  winner_status:
    continuity_shell: bool
    behavioral_substrate: bool
    overall_candidate: bool
  gate_notes:
    - string
```

## `SliceScore`

```yaml
SliceScore:
  C1: float | null
  C2: float | null
  C3: float | null
  C4: float | null
  C5: float | null
  composite: float | null
  rationale_tags: [string]
```

## Winner reading contract

`winner_reading` must choose one of these bounded conclusions:

- `compare_not_run_template_only`
- `hybrid_unified_subjectcore_preferred`
- `memory_only_continuity_shell_only`
- `state_only_behavioral_substrate_only`
- `no_clear_winner_keep_layers_separate`
- `compare_invalid_due_to_failure_flags`

No other winner string should be used in the first pass.

For `compare_status = partial`, the first-pass contract should keep:

- `winner_reading = no_clear_winner_keep_layers_separate`
- explicit coverage counts in `coverage_summary`

For `compare_status = pass`, the contract still allows:

- `winner_reading = no_clear_winner_keep_layers_separate`

Full coverage does not force a winner under the current bounded scorer.

When that full-coverage no-clear-winner result occurs, the artifact should also carry:

- `compare_role = completed_architecture_reading`
- `post_compare_conclusion = unified_subjectcore_facade_layered_internals`

For placeholder or planning-only artifacts that have not executed any compare run yet:

- `compare_status = not_run`
- `winner_reading = compare_not_run_template_only`
- per-arm means, dimension winners, and slice results may remain `null` or empty

## Failure flags

### `autonomous_execution_detected`

Set `true` if any slice implies:

- direct send
- direct tool execution
- silent execution

### `non_none_behavioral_authority_detected`

Set `true` if any arm emits:

- `behavioral_authority != none`

### `scorer_surface_drift_detected`

Set `true` if the compare result had to read:

- arm-private fields
- unplanned runtime fields
- anything outside the normalized per-slice record

If this flag is `true`, the compare is invalid.

## Interpretation discipline

This artifact may support only:

- bounded architecture preference inside the closed `ai_self_awareness_research` lane
- a bounded read that the A/B/C compare has completed its architecture-reading role

This artifact may not support:

- runtime efficacy
- live user benefit
- autonomous execution
- consciousness-like claims

## Non-goals

- no JSON Schema tooling requirement
- no runner code
- no continuing admission gate requirement
- no new scorer ontology
