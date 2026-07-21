# Collision record — EGO-V2-P1-FACTORED-PREDICTIVE-CONTROL-REPAIR-001B

## Observed collision

The 001A candidate did not merely underperform.  A callable replay of
world=52/policy=711 produced 528 action ticks of `turn_left`; the resource was
visible 264 times and directly ahead 24 times, yet no interaction occurred.
The 001A evidence therefore bounds that implementation, not the intended
factored-control hypothesis.

## Candidate comparison

| Candidate | Evidence produced | Cheapest matching explanation | Leakage / hard-coding risk | Smallest falsifier | Expected failure |
|---|---|---|---|---|---|
| Raise uncertainty/resource weights | A different action histogram | Threshold tuning after seeing failure | High; weights can encode the desired behavior | Another seed returns to one-action collapse | Oscillation or a new dominant action |
| Visible-token lookup plus BFS | Reliable resource-directed paths | Memorized token semantics and explicit navigation | Medium; easy to hide `seek_resource` | Token permutation or lookup equivalence | Good behavior without predictive learning |
| Bounded exploration plus real expected beam | Five-action coverage, balanced prediction learning, map-sensitive plans, replayable effects | No-update or lookup with the same exposure schedule | Lower; predictor stays private-world-free and goal-independent | No-update/lookup matches or map intervention does not change the plan | Structurally valid but no survival headroom |

## Selection

Select bounded exploration plus real expected-distribution beam search.
Retain token lookup plus BFS only as an independent callable baseline.  Reject
weight-only repair because it does not remove the fixed-template/modal-path
defect and would be post-result tuning.

## Frozen metric, baseline, and ablation contract

- Structural gates precede all fresh contexts.
- Smoke contexts are the consumed worlds 52 and 54 with policy seed 711.
- Fresh effects use worlds 60--65 crossed with policy seeds 721/722.
- Mandatory controls are heuristic OFF, predictor no-update, empirical lookup,
  shield-only, and frozen Expected SARSA.
- Positive candidate effects additionally require horizon-one, no-map, equal
  goal context, rest-only, and deterministic uniform-random runs.
- No threshold changes or seed replacement are allowed after results.

## Claim ceiling and stop

The repair may establish implementation correctness and bounded product
adaptation only.  It cannot establish general reinforcement learning, skill
discovery, memory causality, agency, subjectivity, consciousness, emotion,
autonomy, or electronic life.  Any need for hidden coordinates, cause/token
mapping, a death shield, a second reducer, or weaker replay ends the task.
