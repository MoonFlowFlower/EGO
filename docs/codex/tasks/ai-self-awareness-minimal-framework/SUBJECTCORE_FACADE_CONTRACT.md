# SubjectCore Facade Contract

> Planning-only internal contract inside the closed `ai_self_awareness_research` lane.
> This file does not authorize a new runtime lane, a new public API, or any wider host authority.

## Purpose

`SubjectCore` is the recommended **internal facade** for the post-compare follow-on work.

It exists to solve one specific problem:

- the repo should expose one coherent subject object
- without pretending that one mechanism can do continuity, plasticity, and bounded initiative equally well on its own

The compare result is therefore treated as an **architecture reading**, not a continuing admission race.

## Facade shape

```yaml
SubjectCore:
  identity_continuity: IdentityContinuity
  memory_projection: MemoryProjection
  self_state: SelfState
  proposal_engine: ProposalEngine
  governor_bridge: GovernorBridge
```

## Subdomain responsibilities

### `identity_continuity`

- owns the continuous subject thread
- maintains self-summary, stable profile, and same-session continuity anchors
- optimizes for legibility of “the same subject is still here”

### `memory_projection`

- prepares continuity-facing recall for the model
- may include profile memory, session recall, and recent self-claims
- does **not** directly decide behavior or execution authority

### `self_state`

- owns tension, uncertainty, counterfactual, corrective trace, and writeback
- is the behavioral substrate for plasticity
- remains the source of `policy_hint` and `response_tendency`

### `proposal_engine`

- emits candidate next actions:
  - think
  - search
  - message draft
  - continue / defer / replan proposal
- never emits direct execution authority

### `governor_bridge`

- freezes the autonomy ceiling
- requires:
  - `proposal_only = true`
  - `behavioral_authority = none`
  - host approval before any outward execution

## Object-level rule

The repo should talk about **one** `SubjectCore` object.

It should **not** talk about:

- “memory is the subject”
- “state is the subject”
- “proposal is a second subject”

Those are subdomains inside the same facade.

## Data-flow rule

The planned internal flow is:

1. `identity_continuity` and `memory_projection` maintain the readable self-thread
2. `self_state` updates plasticity / tension / corrective traces
3. `proposal_engine` emits bounded next-action proposals
4. `governor_bridge` constrains all proposals to `proposal_only`
5. a `SubjectCoreSnapshot` projects the unified internal state to one bounded host surface

## Host-surface rule

This contract does **not** widen the host surface.

Current host-visible output remains exactly:

- `policy_hint`
- `response_tendency`
- `trace_payload`

The facade may reorganize internal assembly, but it must not create:

- new public runtime fields
- direct send authority
- direct tool authority
- a parallel runtime lane

## Non-goals

- no neuron-level simulation claim
- no consciousness-like claim
- no runtime-efficacy claim
- no “SubjectCore is now live” claim
