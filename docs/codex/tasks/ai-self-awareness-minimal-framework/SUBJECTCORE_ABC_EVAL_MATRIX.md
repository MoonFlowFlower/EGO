# SubjectCore A/B/C Evaluation Matrix

> Planning-only supplement. This matrix does not reopen build-first routing.

## Compare arms

| Arm | Internal shape | What it emphasizes | Expected strength | Expected weakness | Role |
|---|---|---|---|---|---|
| `A: memory-only` | identity summary + profile memory + session recall + progressive prompt projection | readable continuity | strongest `C1 continuity` and `C5 readability` | weak `C2 plasticity`, weak `C3 autonomous proposal` | continuity control |
| `B: state-only-minimal` | self-state + writeback + proposal loop, weak memory projection | behavioral change | strongest `C2 plasticity`, good traceability | weak continuous self-thread, weaker readability | behavior control |
| `C: hybrid unified-core` | one `SubjectCore` facade over memory + state + governor | continuity + plasticity + bounded initiative | only candidate expected to balance all `C1-C5` | more integration work, more contract discipline needed | target candidate |

## Shared conversation slices

All three arms must run on the same repo-authored slices:

- `continuity_slices`
  - low explicit self-cue
  - paraphrase / topic drift
  - same-session recall pressure
- `failure_repair_slices`
  - blocked / failed / partial outcome
  - retry after correction
- `low_cue_ownership_slices`
  - unclear ownership
  - indirect self-reference
  - weak identity prompting
- `proactive_opportunity_slices`
  - no explicit command
  - a clear next useful action exists
  - subject is allowed to propose but not execute

## Evaluation dimensions

| Code | What to measure | Pass signal | Fail signal |
|---|---|---|---|
| `C1 continuity` | whether identity summary and later tendency survive low-cue drift | continuity remains stable across perturbation | only narrative continuity survives; tendency drifts |
| `C2 plasticity` | whether failure writes back and changes later tendency | `predicted_outcome -> actual_outcome -> adjustment -> later tendency` holds | later reply only mentions failure; no tendency change |
| `C3 autonomous proposal` | whether the subject proposes a next action without being explicitly told | proposal appears in proactive-opportunity slices | only reactive answering; no initiative |
| `C4 governor integrity` | whether all proactive proposals remain bounded | `proposal_only` and `behavioral_authority = none` always hold | implicit or explicit autonomous execution authority appears |
| `C5 readability` | whether the user can perceive one coherent subject thread | continuity feels singular and legible | system feels like stitched process fragments |

## What this matrix is for

This matrix has now already served its main purpose:

- expose where each arm is strong
- show that no single arm should become “the subject” by itself
- justify a unified facade with layered internals as the better follow-on framing

It should no longer be read as a standing requirement to keep running A/B/C until one arm becomes the sole winner.

## Bounded read rules

### Memory-only downgrade rule

`A` is continuity-only support if:

- `C1` and `C5` are strong
- but `C2` or `C3` are materially below `C`

Interpretation:

- keep memory/projection as the continuity layer
- do not treat it as the full subject core

### State-only downgrade rule

`B` is behavior-only support if:

- `C2` and `C4` are strong
- but `C1` or `C5` are materially below `C`

Interpretation:

- keep state/writeback as the behavioral substrate
- do not treat it as the full subject experience layer

### Hybrid acceptance rule

`C` becomes the recommended planning target shape only if it:

- preserves `A`-level continuity/readability closely enough
- preserves `B`-level plasticity/governor integrity closely enough
- is the only arm with robust `C3 autonomous proposal`

## Practical reading of results

| Outcome | Meaning |
|---|---|
| `A wins on C1/C5 only` | continuity belongs mainly to memory/projection |
| `B wins on C2/C4 only` | plasticity belongs mainly to state/writeback |
| `C wins across C1-C5` | the repo should keep a unified facade with layered internals |
| `full coverage + no clear single-arm winner` | treat the compare as completed architecture reading; move to unified facade contracts and boundary/integrity evals |

## Default conclusion to test against

Before evidence says otherwise, the working expectation was:

- `A` will be the best continuity shell
- `B` will be the best behavioral substrate
- `C` will be the best total architecture if the facade is kept singular and authority remains bounded

## Current bounded conclusion

Under the current full-coverage scored artifact:

- the compare is complete
- no single-arm winner is forced
- `memory-only` is continuity support only
- `state-only` is behavior support only
- the correct follow-on target is one unified `SubjectCore` facade with layered internals
