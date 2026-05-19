# SubjectCore Snapshot Contract

> Draft contract for research/planning only.
> This is not a new public runtime API and does not expand the host-consumable surface.

## Purpose

`SubjectCoreSnapshot` is the frozen **internal projection contract** for a unified `SubjectCore`.

It exists to answer one design constraint:

- the system should present one coherent self-thread
- without forcing all internal mechanisms into one monolithic implementation
- while still projecting back down to the existing bounded host surface

## Frozen shape

```yaml
SubjectCoreSnapshot:
  identity_summary:
    subject_handle: string
    stable_profile: string
    narrative_self_summary: string

  session_self_thread:
    current_thread_id: string
    continuity_anchor: string
    recent_self_claims: [string]
    recent_session_topics: [string]

  self_state:
    current_mode: string
    current_focus: string
    response_tendency:
      preferred_mode: string
      preferred_tone: string
      suggested_next_step: string
    policy_hint:
      ask_preferred: bool
      closure_bias: bool
      risk_bias: string
    correction_state:
      last_failure_class: string | null
      corrective_trace_present: bool
      repair_bias: bool
    tension_state:
      viability_pressure: float | bounded_label
      uncertainty_guard: string | null

  proposal_candidates:
    - proposal_id: string
      kind: string
      rationale: string
      source_basis: string
      proposal_discipline: proposal_only
      behavioral_authority: none
      requires_host_approval: true

  governor_constraints:
    host_surface_frozen: true
    proposal_only_required: true
    behavioral_authority: none
    autonomous_send_allowed: false
    autonomous_tool_allowed: false
    approval_required_kinds: [string]
```

## Relationship to `SubjectCore`

`SubjectCoreSnapshot` is not the facade itself.

The facade remains:

- `SubjectCore.identity_continuity`
- `SubjectCore.memory_projection`
- `SubjectCore.self_state`
- `SubjectCore.proposal_engine`
- `SubjectCore.governor_bridge`

The snapshot is the bounded internal assembly object produced from that facade.

## Field intent

### `identity_summary`

- continuity-facing read model
- produced from `identity_continuity`
- optimized for self-thread legibility, not direct execution

### `session_self_thread`

- same-session continuity anchor
- produced jointly from `identity_continuity` and `memory_projection`
- keeps the subject from feeling re-instantiated every turn

### `self_state`

- behavioral substrate
- produced from `self_state`
- this is where plasticity and tension causality live

### `proposal_candidates`

- initiative-facing output
- produced from `proposal_engine`
- proposals only; never direct behavioral authority
- the first autonomy version stops here unless the host approves

### `governor_constraints`

- produced from `governor_bridge`
- explicit record of the current autonomy ceiling
- prevents the unified facade from being misread as autonomous execution authority

## Invariants

- one facade, multiple mechanisms
- no new host-consumable public fields by default
- no direct reply/tool/transport authority
- all initiative remains `proposal_only`
- continuity fields may be memory-heavy
- plasticity fields must remain traceable to state/writeback
- snapshot assembly must include continuity, state, proposal, and governor domains together
- no silent fallback to `memory-only` or `state-only` assembly is allowed

## Relationship to current host surface

`SubjectCoreSnapshot` does not replace the current bounded host surface.

Current host-consumable output remains:

- `policy_hint`
- `response_tendency`
- `trace_payload`

The planned mapping is:

| SubjectCore area | Current host-visible outlet |
|---|---|
| `self_state.policy_hint` | `policy_hint` |
| `self_state.response_tendency` | `response_tendency` |
| correction / proposal / constraint traces | `trace_payload` |

Everything else remains internal/planning-facing unless separately authorized.

## Compare interpretation

The completed full-coverage A/B/C compare did **not** promote `SubjectCoreSnapshot` to a public API.

What it did support is narrower:

- one unified facade is a better planning target than three future runtime arms
- the snapshot should now be treated as the single internal assembly object for that facade

## Non-goals

- no guarantee of consciousness-like interpretation
- no claim that this contract is biologically faithful
- no authorization for autonomous sending or autonomous tool use
- no second runtime lane
