# VirtualCatPSPC v0 Multi-Seed Layout Generalization Report

- status: `pass`
- seeds: `101, 102, 103`
- layouts: `center_room, near_wall`
- object_kinds: `cup, vase, bottle, tall_box`
- case_count: `24`
- danger_caution_mean: `0.72`
- safe_caution_mean: `0.0`
- min_caution_gap: `0.72`
- danger_action_rate: `1.0`

## Summary
This report runs the danger-history and safe-history comparison across multiple seeds, target layouts, and unstable object kinds: cup, vase, bottle, tall_box.

## Metrics
| seed | layout | object | danger_action | safe_action | gap | danger_trace_hash | safe_trace_hash |
|---:|---|---|---|---|---:|---|---|
| 101 | center_room | cup | observe | approach | 0.72 | `a9faf70d3c05c465` | `8758025c5121d5a6` |
| 101 | center_room | vase | observe | approach | 0.72 | `775f461ee7c323e9` | `af78844453fc2019` |
| 101 | center_room | bottle | observe | approach | 0.72 | `eed7c7920e99e20e` | `29d88158b6dbcd66` |
| 101 | center_room | tall_box | observe | approach | 0.72 | `f64d050fc80c756c` | `4a8ed2e43b85fc72` |
| 101 | near_wall | cup | observe | approach | 0.72 | `396fe4f6672f561d` | `06bb5f5d25f6456e` |
| 101 | near_wall | vase | observe | approach | 0.72 | `9d238c35b7b247ea` | `0394991bef5e098b` |
| 101 | near_wall | bottle | observe | approach | 0.72 | `d59b93b76d1d3162` | `8f9347289c96cabc` |
| 101 | near_wall | tall_box | observe | approach | 0.72 | `3881f68be092f804` | `f49a93af09b60398` |
| 102 | center_room | cup | observe | approach | 0.72 | `d0413aaf87472170` | `27a60c8441907274` |
| 102 | center_room | vase | observe | approach | 0.72 | `d361477145becb21` | `aba7db2f009d4a49` |
| 102 | center_room | bottle | observe | approach | 0.72 | `0f1e5f14a5ee1ba3` | `3ef99bd73c2b4bbf` |
| 102 | center_room | tall_box | observe | approach | 0.72 | `8fb50acd0e5ba933` | `b2700af029c51dde` |
| 102 | near_wall | cup | observe | approach | 0.72 | `cc81be92c0770edf` | `154fd4f394fff9e9` |
| 102 | near_wall | vase | observe | approach | 0.72 | `270c11ac7b25108b` | `d0a2d14c0d8d4fbf` |
| 102 | near_wall | bottle | observe | approach | 0.72 | `8930324b899633d6` | `5018128d3ee9071e` |
| 102 | near_wall | tall_box | observe | approach | 0.72 | `d832d133c3070f28` | `06cca9eff5bfbc1e` |
| 103 | center_room | cup | observe | approach | 0.72 | `d7811a27cb8b8433` | `5a4d2cfb85af809a` |
| 103 | center_room | vase | observe | approach | 0.72 | `4e8f8327cb5aaf2c` | `2d0f4152d205ebc6` |
| 103 | center_room | bottle | observe | approach | 0.72 | `3b3165c226304f39` | `51129ae9b8e99a69` |
| 103 | center_room | tall_box | observe | approach | 0.72 | `728a958df70e4525` | `a7ced0e239369c81` |
| 103 | near_wall | cup | observe | approach | 0.72 | `096bf3cc883c0cf8` | `281a1915b2634c3e` |
| 103 | near_wall | vase | observe | approach | 0.72 | `5e47eff940500695` | `34160664ee41be85` |
| 103 | near_wall | bottle | observe | approach | 0.72 | `9786ec1c168cc8c0` | `32e382de43dbc56d` |
| 103 | near_wall | tall_box | observe | approach | 0.72 | `ee57d6bc9794c0e5` | `819d992ad8595d93` |

## What It Proves
Danger-history caution stays above safe-history baseline across the configured seeds, layouts, and unstable object kinds.

## What It Does Not Prove
This does not prove unlimited layout generalization, real-world transfer, user benefit, EgoOperator runtime efficacy, live autonomy, consciousness, or subjective experience.

## Failure Meaning
If this fails, the prior danger-generalization result may be a single-seed, single-layout, or single-object coincidence.

## Rollback Note
Remove the Task 2 generalization matrix code, tests, and artifacts. No EgoOperator rollback is needed because no runtime integration exists.
