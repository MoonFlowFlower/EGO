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
| 101 | center_room | cup | observe | approach | 0.72 | `bd7e64aad876aaa4` | `9fcd89c08e68753b` |
| 101 | center_room | vase | observe | approach | 0.72 | `a7ce24841039a649` | `177f3390c2304b12` |
| 101 | center_room | bottle | observe | approach | 0.72 | `27f9f65d6d118490` | `d357f60edc069d5f` |
| 101 | center_room | tall_box | observe | approach | 0.72 | `2ad35b3793cc98ab` | `f79151b798fe2cdb` |
| 101 | near_wall | cup | observe | approach | 0.72 | `dfaaf5cee54ad78f` | `fd97502306e73b23` |
| 101 | near_wall | vase | observe | approach | 0.72 | `6ce9baf65154d997` | `5367129c5aa5ad01` |
| 101 | near_wall | bottle | observe | approach | 0.72 | `69a95504af97e3a8` | `78b385d52bafeaf1` |
| 101 | near_wall | tall_box | observe | approach | 0.72 | `309bb879cdd3129d` | `98a69fccf7f6444a` |
| 102 | center_room | cup | observe | approach | 0.72 | `871e8b1eff30b1f6` | `3c2cd6f9ad501028` |
| 102 | center_room | vase | observe | approach | 0.72 | `63b413a25fe473e9` | `ac9366ede7e36b86` |
| 102 | center_room | bottle | observe | approach | 0.72 | `b552ea5601619ced` | `868b3c76d86a1f9f` |
| 102 | center_room | tall_box | observe | approach | 0.72 | `07424c8e0066f2f0` | `f1898981a6f8d679` |
| 102 | near_wall | cup | observe | approach | 0.72 | `1c8db91e9456f64b` | `c6da58572998b47b` |
| 102 | near_wall | vase | observe | approach | 0.72 | `53e798501a4c441b` | `144012941deb9916` |
| 102 | near_wall | bottle | observe | approach | 0.72 | `623b917034e7864f` | `e81a6bc14995572f` |
| 102 | near_wall | tall_box | observe | approach | 0.72 | `47b1e06de0ba0c39` | `455fc3b295363b6a` |
| 103 | center_room | cup | observe | approach | 0.72 | `2461c048d3757552` | `acaec29dbf136fa9` |
| 103 | center_room | vase | observe | approach | 0.72 | `1df061cf8b6de086` | `e133ded03034e3d3` |
| 103 | center_room | bottle | observe | approach | 0.72 | `5bf021c142d0a347` | `2f67b1a5964d084e` |
| 103 | center_room | tall_box | observe | approach | 0.72 | `e20130420c93c30b` | `4715e5ed36676c85` |
| 103 | near_wall | cup | observe | approach | 0.72 | `1b551509c0c0da19` | `d5e83f097ecf4b23` |
| 103 | near_wall | vase | observe | approach | 0.72 | `aee3b4766f2f31ca` | `930b0beb15453331` |
| 103 | near_wall | bottle | observe | approach | 0.72 | `ef875edc3a64ead6` | `81710eb5f75dc93a` |
| 103 | near_wall | tall_box | observe | approach | 0.72 | `ca636a3f5605609c` | `2ad934d790bb28f0` |

## What It Proves
Danger-history caution stays above safe-history baseline across the configured seeds, layouts, and unstable object kinds.

## What It Does Not Prove
This does not prove unlimited layout generalization, real-world transfer, user benefit, EgoOperator runtime efficacy, live autonomy, consciousness, or subjective experience.

## Failure Meaning
If this fails, the prior danger-generalization result may be a single-seed, single-layout, or single-object coincidence.

## Rollback Note
Remove the Task 2 generalization matrix code, tests, and artifacts. No EgoOperator rollback is needed because no runtime integration exists.
