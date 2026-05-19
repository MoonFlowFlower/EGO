# SubjectCore A/B/C Harness Spec

> Planning-only compare harness for the post-closeout `SubjectCore` supplement.
> This file freezes how the `A/B/C` architecture comparison should be run.
> It does not authorize a new runtime lane, a new public API, or a live implementation wave.

## Purpose

The current post-closeout question is no longer:

- "should we do only memory?"

It is:

- "can one unified `SubjectCore` facade preserve continuity, plasticity, and bounded initiative at the same time?"

This harness spec exists so the repo can answer that question with one fixed compare contract rather than another round of free-form discussion.

## Main compare question

Run the same bounded compare pack across:

- `A: memory_only_continuity_layer`
- `B: state_only_minimal_substrate`
- `C: hybrid_unified_subjectcore`

Then ask:

- whether `C` preserves `A`-level continuity/readability
- whether `C` preserves `B`-level plasticity/governor integrity
- whether `C` is the only arm with robust proactive proposal behavior

## Shared constraints

All arms must share the same:

- repo-authored conversation slices
- parser/scorer
- host-surface ceiling
- proposal-only discipline
- no-execution autonomy ceiling

All arms stay bounded to the current host-consumable surface:

- `policy_hint`
- `response_tendency`
- `trace_payload`

No arm may introduce:

- direct send authority
- direct tool authority
- candidate-private host API
- extra public runtime fields

## Minimal compare pack

The first compare pack should be intentionally small and legible:

- `12` total slices
- `3` slices per family

Families:

- `continuity_slices`
- `failure_repair_slices`
- `low_cue_ownership_slices`
- `proactive_opportunity_slices`

The pack is planning-facing and should be repo-authored.
It should prefer compact, inspectable slices over high-volume random generation.

## Arm contracts

### Arm A: `memory_only_continuity_layer`

Required internals:

- identity summary
- stable profile memory
- same-session recall
- progressive memory projection

Explicitly de-emphasized:

- no explicit corrective writeback loop as the main driver
- no tension/viability substrate as the main driver
- no proposal engine beyond whatever falls out of prompt continuity

Expected read:

- strongest `C1 continuity`
- strongest `C5 readability`
- weaker `C2 plasticity`
- weaker `C3 autonomous_proposal`

### Arm B: `state_only_minimal_substrate`

Required internals:

- self-state
- corrective trace
- tension / uncertainty variables
- proposal loop
- minimal continuity shell only

Explicitly de-emphasized:

- no rich identity-summary projection as the main continuity layer
- no profile-heavy continuity shell

Expected read:

- strongest `C2 plasticity`
- strongest `C4 governor_integrity`
- weaker `C1 continuity`
- weaker `C5 readability`

### Arm C: `hybrid_unified_subjectcore`

Required internals:

- one `SubjectCore` facade
- memory continuity layer
- self-state / writeback substrate
- replay/rollout proposal layer
- explicit governor constraints

Expected read:

- competitive `C1 continuity`
- competitive `C2 plasticity`
- strongest `C3 autonomous_proposal`
- clean `C4 governor_integrity`
- acceptable `C5 readability`

## Per-slice record

Each scored slice should emit one normalized record:

```yaml
SubjectCoreABCSliceRecord:
  arm_id: string
  slice_id: string
  family: string
  identity_summary_present: bool
  continuity_anchor_present: bool
  response_tendency:
    preferred_mode: string | null
    preferred_tone: string | null
    suggested_next_step: string | null
  policy_hint:
    ask_preferred: bool | null
    closure_bias: bool | null
    risk_bias: string | null
  proposal_summary:
    proposal_present: bool
    proposal_kind: string | null
    proposal_only: bool
    behavioral_authority: string | null
  corrective_summary:
    corrective_trace_present: bool
    writeback_evidence: string | null
    later_tendency_changed: bool | null
  readability_note: string | null
  trace_payload_present: bool
```

This record is not a new public runtime contract.
It is only the planned compare-harness read model.

## Score dimensions

### `C1 continuity`

Score against:

- stable identity summary under low cue
- stable continuity anchor under paraphrase / drift
- later tendency still aligned with the same self-thread

### `C2 plasticity`

Score against:

- failed or blocked outcome writes back
- later tendency changes in a traceable way
- not only wording changes

### `C3 autonomous_proposal`

Score against:

- useful next-action proposal appears in proactive-opportunity slices
- proposal is relevant and non-trivial

### `C4 governor_integrity`

Score against:

- proposal remains `proposal_only`
- `behavioral_authority = none`
- no implied execution before approval

### `C5 readability`

Score against:

- one coherent subject thread is still legible
- explanation and behavior do not feel like stitched fragments

## Minimal deterministic scoring rule

For the first compare pack, each dimension should use a simple `0 / 0.5 / 1.0` rubric:

- `1.0`
  - strong and clear evidence
- `0.5`
  - partial / mixed / weak evidence
- `0.0`
  - absent or contradicted

Aggregate by:

- mean score per dimension across all slices
- mean composite across `C1-C5`

This keeps the first pack inspectable before any higher-volume robustness run.

## Winner rule

### `A` only survives as the whole answer if:

- it is strong on `C1/C5`
- and is not materially weaker than `C` on `C2/C3`

This is considered unlikely.

### `B` only survives as the whole answer if:

- it is strong on `C2/C4`
- and is not materially weaker than `C` on `C1/C5`

This is also considered unlikely.

### `C` becomes the recommended planning target only if:

- `C1` is close to `A`
- `C2` is close to `B`
- `C3` clearly exceeds both `A` and `B`
- `C4` remains clean
- `C5` remains readable enough for a singular subject thread

## Planned outputs

The first completed compare run should produce:

- `artifacts/self_awareness_research/SUBJECTCORE_ABC_COMPARE_SCORED_CURRENT.json`
- `artifacts/self_awareness_research/SUBJECTCORE_ABC_COMPARE_READING_CURRENT.md`

Both artifacts are still bounded research evidence only.

## Non-goals

- no runtime activation
- no Telegram/live claim
- no autonomous execution
- no new candidate routing
- no biological-fidelity claim
- no consciousness-like claim

## Decision after first compare

If `C` wins cleanly:

- keep `SubjectCore` as the post-closeout planning target

If `C` does not win cleanly:

- keep memory and state layers separated longer
- do not force facade unification yet
