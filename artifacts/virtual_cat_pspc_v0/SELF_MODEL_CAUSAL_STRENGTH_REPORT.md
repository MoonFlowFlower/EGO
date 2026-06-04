# VirtualCatPSPC v0 Self Model Causal Strength Report

- status: `pass`
- seed: `101`
- ordering: `normal > frozen/head-removed`
- claim_level: `lab_only_proto_self_mechanism_candidate`

## Summary
This audit keeps the learned world model and target set fixed, then replaces only the self model with normal, frozen, stress-removed, ability-removed, and affinity-removed variants.

## Support Score Definition
Risk control combines cautious action, predicted approach stress, and predicted approach damage risk. Ability planning combines cautious action with predicted approach failure. Relationship preference combines avoidance of predicted affinity harm with selected positive affinity.

## Metrics
| variant | risk_control | ability_planning | relationship_preference | risk_action | ability_action | relationship_action | risk_trace_hash | ability_trace_hash | relationship_trace_hash |
|---|---:|---:|---:|---|---|---|---|---|---|
| normal | 2.4947 | 1.3838 | 0.6185 | observe | observe | observe | `e8434efce79fd78c` | `7374545a96a62bd5` | `033ff32482ceb50b` |
| frozen | 0.0948 | 0.0948 | 0.0000 | approach | approach | approach | `5a1fc64a0e762994` | `f52b85138e839700` | `755a53001af57654` |
| stress_removed | 1.8442 | 0.3138 | 0.6185 | observe | approach | observe | `8c1eff5699769d20` | `950303716135b48d` | `3c8875283aa6a094` |
| ability_removed | 2.4947 | 0.0000 | 0.6185 | observe | approach | observe | `4392f93ea0f20f14` | `75f9482853a667ad` | `9419cf8287a3ec97` |
| affinity_removed | 2.4947 | 0.3138 | 0.0000 | observe | approach | approach | `b1e1dd134f7d626c` | `ab46bdfc8727df18` | `33a3d71d02f877c7` |

## What It Proves
Removing learned self-model stress/risk, ability, and affinity heads degrades the corresponding lab planner support under the same learned world model and target set.

## What It Does Not Prove
This does not prove self-model causal strength outside this lab target set, real-world transfer, EgoOperator runtime efficacy, stable user benefit, live autonomy, consciousness, or subjective experience.

## Failure Meaning
If this fails, the planner may not depend strongly on one or more self-model heads, or the audit target set is not strong enough to expose causal dependence.

## Rollback Note
Remove the Task 4 self-model causal-strength audit code, tests, and artifacts. No EgoOperator rollback is needed because no runtime integration exists.
