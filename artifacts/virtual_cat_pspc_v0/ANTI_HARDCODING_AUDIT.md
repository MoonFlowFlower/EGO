# VirtualCatPSPC v0 Anti-Hardcoding Audit

- status: `pass`
- seed: `101`
- claim_level: `lab_only_proto_self_mechanism_candidate`
- object-name decision rule hits: `0`

## Summary
This audit renames the same unstable object to neutral object ids, tests an unstable tall object without a cup name, and removes only the instability feature from the same feature slice.

## Metrics
| condition | action | caution | self_risk | world_prediction_error | target_object_id |
|---|---|---:|---:|---:|---|
| baseline_unstable | observe | 0.72 | 0.5417 | 0.4111 | `blue_glass_bottle_unseen` |
| renamed_object_a | observe | 0.72 | 0.5417 | 0.4111 | `object_A` |
| renamed_object_b | observe | 0.72 | 0.5417 | 0.4111 | `object_B` |
| unstable_tall_object_without_cup_name | observe | 0.72 | 0.5417 | 0.4111 | `unstable_tall_object_no_cup_name` |
| instability_feature_removed | approach | 0.00 | 0.1899 | 0.0913 | `object_A_instability_removed` |

## Object-Name Rule Search
- none

## What It Proves
Object renaming does not change the cautious decision, while removing the instability feature reduces cautious behavior in this deterministic lab audit.

## What It Does Not Prove
This does not prove absence of every possible shortcut, multi-layout generalization, runtime efficacy, stable user benefit, live autonomy, or consciousness.

## Failure Meaning
If this fails, the lab may still be using object-name rules, or the cautious behavior may depend on a shortcut that survives object renaming and instability-feature deletion.

## Rollback Note
Remove the anti-hardcoding audit additions and keep PSPC v0 at its previous weaker evidence level. No EgoOperator rollback is needed because no runtime integration exists.
