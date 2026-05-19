# SubjectCore Neuro Motif Map

> Planning-only supplement in the closed `ai_self_awareness_research` lane.
> This file maps brain-inspired computational motifs to repo-level design decisions.
> It does not claim biological fidelity and does not create a new authority source.

## Purpose

This map answers one narrow question:

- if the repo continues the `SubjectCore` framing, what neuro-computational motifs are worth imitating at the current engineering layer?

The answer is explicitly **not** “simulate neurons first”.

The useful layer is:

- memory/planning coupling
- uncertainty-sensitive state updating
- future-oriented replay/rollout
- bounded control and gating

## Motif 1: Hippocampus-PFC memory/planning coupling

### Research reading

- hippocampus and prefrontal cortex repeatedly appear as a coupled system for memory-guided planning, flexible retrieval, and future-oriented decision support
- the useful abstraction is not “memory storage vs command center” in isolation, but a loop:
  - hippocampal-style episodic retrieval / replay
  - prefrontal-style context selection / control / action relevance

Primary sources:

- [Nature Reviews Neuroscience 2017](https://www.nature.com/articles/nrn.2017.74)
- [Nature 2015](https://www.nature.com/articles/nature14445)
- [PMC 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11179466/)

### Repo interpretation

This motif maps to:

- `memory_projection`
  - session recall, identity summary, recent self thread
- `proposal_engine`
  - next useful action proposal
- `governor_bridge`
  - relevance filtering and bounded proposal discipline

### Practical takeaway

Do not treat memory as just “longer prompt”.

Treat it as:

- selective retrieval for current planning
- current-thread continuity support
- future-action relevance support

This strengthens the case for:

- `memory-only` as continuity support
- not as the whole subject core

## Motif 2: Replay and future simulation

### Research reading

- hippocampal replay is not only about past recall; it also supports future path simulation and deliberation
- the engineering analogue is rollout/replay for “what should I do next?”

Primary sources:

- [Nature 2013](https://pubmed.ncbi.nlm.nih.gov/23594744/)
- [Nature Communications 2017](https://www.nature.com/articles/ncomms14652)
- [PubMed 2019](https://pubmed.ncbi.nlm.nih.gov/30892976/)

### Repo interpretation

This motif maps to:

- `counterfactual writeback`
- `proposal_candidates`
- `repair_closure`
- `next_guard`

### Practical takeaway

Bounded initiative should start as:

- replay/rollout driven proposal formation
- not automatic execution

This supports the current autonomy ceiling:

- `proposal_only`
- `behavioral_authority = none`

## Motif 3: Active-inference-style uncertainty control

### Research reading

- active inference is useful here not because it “proves consciousness”, but because it formalizes:
  - uncertainty-sensitive policy selection
  - epistemic exploration
  - precision / confidence control
- even supportive reviews still describe consciousness claims as preliminary and not yet a strict process theory

Primary sources:

- [Review of Philosophy and Psychology 2022](https://link.springer.com/article/10.1007/s13164-021-00579-w)
- [arXiv 2019](https://arxiv.org/abs/1909.10863)
- [arXiv 2022 survey reference trail](https://arxiv.org/abs/2201.06387)

### Repo interpretation

This motif maps to:

- `self_state`
  - uncertainty
  - calibration
  - viability pressure
  - source confidence
  - agency confidence
- `policy_hint`
- `response_tendency`

### Practical takeaway

This is the current strongest substrate for:

- `C2 plasticity`
- `C4 governor integrity`
- tension-sensitive proposal behavior

It is not, by itself, the full continuity shell.

## Motif 4: Workspace/gating as bounded coordination, not full theory commitment

### Research reading

- workspace-like ideas remain useful as a coordination metaphor, but they should not be overcommitted as the entire self model
- the useful engineering reading is “bounded routing and gating across subsystems”

### Repo interpretation

This motif maps to:

- `SubjectCore` facade
- `trace_payload`
- host-governed arbitration
- explicit proposal discipline

### Practical takeaway

Use workspace ideas as:

- interface coordination
- visibility/gating

Do **not** treat them as proof that a unified consciousness architecture has been recovered.

## Recommended mapping summary

| Brain-inspired motif | Engineering role | SubjectCore area | Current repo fit |
|---|---|---|---|
| hippocampus-PFC coupling | selective recall for planning | `memory_projection` + `proposal_engine` | high |
| replay / future simulation | next-step generation | `proposal_candidates` + corrective replay | high |
| active-inference uncertainty control | plastic decision substrate | `self_state` | very high |
| workspace/gating | coordination and bounded visibility | `governor_bridge` + facade contract | medium |
| neuron-level simulation | low-level mechanistic fidelity | none for current tranche | low |

## Current recommendation

The next research step should stay at the motif level above and ask:

- can one unified `SubjectCore` facade coordinate
  - continuity memory
  - plastic self-state
  - replay-driven bounded initiative

without changing the current host authority contract?

If yes, that is the right next abstraction.
If not, the repo should keep the internals separated longer rather than forcing premature unification.
