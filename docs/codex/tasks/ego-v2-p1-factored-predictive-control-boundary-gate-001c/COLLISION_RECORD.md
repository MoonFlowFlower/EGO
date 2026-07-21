# Collision record — EGO-V2-P1-FACTORED-PREDICTIVE-CONTROL-BOUNDARY-GATE-001C

## Observed collision

The 001B old-smoke result removed single-action collapse but did not cross its
runtime boundary.  Recovery measured 14.97 and 18.62 seconds, and mean trace
size measured 33,814.5 and 33,929.8 bytes.  Because the smoke gate failed, the
five-action prediction evaluator and all fresh effect contexts remained
unexecuted.  Faster-looking execution is insufficient if it skips independent
recomputation or changes planner semantics.

## Candidate comparison

| Candidate | Evidence produced | Cheapest matching explanation | Leakage / hard-coding risk | Smallest falsifier | Expected failure |
|---|---|---|---|---|---|
| Compress trace only | Smaller rows | Removes bytes without reducing planner work | Low leakage, high false-closure risk | Recovery remains above 10 s | Byte gate passes alone |
| Checkpoint, stored-plan replay, or reduced horizon | Faster recovery | Reuses prior answers or runs a cheaper controller | High replay weakness or semantic drift | Initial-state-plus-commands recomputation differs | Fast but inadmissible recovery |
| Fixed-order numeric predictor plus compact trace | Same decisions with less repeated work | Implementation efficiency rather than a new policy | Moderate numeric-order risk | Pre-change semantic fixture differs beyond tolerance | Replay drift or insufficient speedup |

## Selection

Select fixed-order numeric predictor execution plus compact trace.  Reject
trace-only closure because it cannot satisfy recovery.  Reject checkpoints,
stored-plan replay, and reduced beam/horizon because they weaken the evidence
boundary or change the tested controller.

## Baseline and ablation contract

- The semantic fixture is produced before product changes on the two consumed
  smoke contexts and is never regenerated after observing optimized results.
- Balanced evaluation scores every action at every eligible snapshot.
- The no-update predictor is an independent callable implementation using the
  same snapshots and a zero-initialized model.
- Selected-action-only metrics are recorded only to expose sampling bias.
- Hidden world state is evaluator-private and is rejected by predictor-input
  leakage scans; forbidden-field positive controls must fail.

## Fresh-context firewall

001C contains no execution mode that accepts worlds 60--65 or policy seeds
721/722.  Its output records `fresh_effect_seeds_consumed=false`.  A positive
boundary-and-prediction result can record eligibility for a separate task, but
is not itself an enablement decision.

## Claim ceiling and stop

This task may establish old-context runtime/replay bounds and measured
five-action predictor-error change only.  It cannot establish fresh-context
survival adaptation, general reinforcement learning, skill discovery, memory
causality, agency, subjectivity, consciousness, emotion, autonomy, or
electronic life.  Semantic drift, replay weakening, hidden-state predictor
input, a second product path, or any old-smoke threshold failure stops the next
gate.
