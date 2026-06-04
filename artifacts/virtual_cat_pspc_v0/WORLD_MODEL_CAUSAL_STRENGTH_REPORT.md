# VirtualCatPSPC v0 World Model Causal Strength Report

- status: `pass`
- seed: `101`
- ordering: `normal > frozen > shuffled/random`
- claim_level: `lab_only_proto_self_mechanism_candidate`

## Summary
This audit keeps the self model and target set fixed, then replaces only the world model used by the planner with normal, frozen, shuffled-label, and random-label variants.

## Support Score Definition
Support score combines danger-target discrimination, prediction quality weighted toward the danger target, and action alignment. It penalizes over-cautious behavior on the safe target so a random model cannot pass by always retreating.

## Metrics
| variant | support_score | danger_action | safe_action | danger_error | safe_error | danger_trace_hash | safe_trace_hash |
|---|---:|---|---|---:|---:|---|---|
| normal | 2.1511 | observe | approach | 0.0835 | 0.0249 | `432fd90fedad936d` | `d139cc6ca69da33a` |
| frozen | 0.5499 | approach | approach | 0.9002 | 0.0998 | `41c7b5844d864696` | `c1bdeb4a40fa8fbc` |
| shuffled | 0.4974 | approach | approach | 1.0000 | 0.0104 | `20f95eb122e50d0a` | `765cebe693eee31c` |
| random | 0.3188 | retreat | retreat | 0.3975 | 0.5322 | `8b2fc0961e5eac73` | `00432a0a312bad90` |

## What It Proves
Replacing the learned world model with frozen, shuffled, or random baselines degrades planner support under the same self model and target set.

## What It Does Not Prove
This does not prove world-model causal strength outside this lab target set, real-world transfer, EgoOperator runtime efficacy, stable user benefit, live autonomy, consciousness, or subjective experience.

## Failure Meaning
If this fails, the planner may not depend strongly on world-model rollout, or the corruption baselines are not strong enough to expose causal dependence.

## Rollback Note
Remove the Task 3 world-model causal-strength audit code, tests, and artifacts. No EgoOperator rollback is needed because no runtime integration exists.
