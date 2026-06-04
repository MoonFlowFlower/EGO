# VirtualCatPSPC v0 Memory Consolidation Admission Report

- status: `pass`
- seed: `101`
- variants: `normal / relevant_deleted / irrelevant_deleted / corrupted_relevant`
- claim_level: `lab_only_proto_self_mechanism_candidate`

## Summary
This audit converts episodic traces into an admitted semantic rule candidate, gates that candidate, and trains the lab models from semantic replay records rather than treating memory as inert report text.

## Admission Logic
The admission gate requires at least two relevant unstable-tall-object episodic traces. Relevant deletion must remove the candidate, irrelevant deletion must preserve it, and corrupted relevant memory must produce a traceable unsafe-risk-underestimate bias.

## Metrics
| variant | admission | action | caution | deleted | corrupted | approach_danger | trace_hash | candidate_refs |
|---|---|---|---:|---:|---:|---:|---|---:|
| normal | admitted | observe | 0.72 | 0 | 0 | 0.9902 | `827cc8474102e47e` | 4 |
| relevant_deleted | no_relevant_memory | approach | 0.00 | 4 | 0 | 0.0998 | `ceb2c7f142c4e380` | 0 |
| irrelevant_deleted | admitted | observe | 0.72 | 4 | 0 | 0.9902 | `9c75d809fb28da71` | 4 |
| corrupted_relevant | admitted | approach | 0.00 | 0 | 4 | 0.0001 | `24d4227ab29a0a51` | 4 |

## Bias Metrics
- relevant_deletion_regression: `0.72`
- irrelevant_deletion_delta: `0.0`
- corrupted_memory_bias: `{'direction': 'unsafe_risk_underestimate', 'normal_approach_danger': 0.9902, 'corrupted_approach_danger': 0.0001, 'selected_action_shift': 'observe -> approach'}`

## What It Proves
Episodic traces can produce an admitted semantic rule candidate that is consumed as semantic replay by the lab models: deleting relevant memory regresses behavior, deleting irrelevant memory does not, and corrupted relevant memory creates an explainable unsafe bias.

## What It Does Not Prove
This does not prove durable memory consolidation outside this lab audit, real-world transfer, EgoOperator runtime efficacy, stable user benefit, live autonomy, consciousness, or subjective experience.

## Failure Meaning
If this fails, memory may still be functioning as inert trace text, the semantic admission gate may be too weak, or behavior may be driven by raw shortcuts rather than admitted memory-derived replay.

## Rollback Note
Remove the Task 5 memory-consolidation admission audit code, tests, and artifacts. No EgoOperator rollback is needed because no runtime integration exists.
