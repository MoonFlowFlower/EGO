# Eval Suite v2.2 Report

**Generated:** 2026-02-28T22:44:43.838152
**Seed:** 42
**Total Scenarios:** 11
**Passed:** 3
**Failed:** 8

## Aggregate Metrics

### emotion_consistency
- **pass_rate:** 1.0
- **scenarios_passed:** 11.0
- **total_scenarios:** 11

### individualization_diff
- **average:** 0.10418865306688493
- **max:** 0.42045454545454547
- **min:** 0.0

### high_impact_false_positive_rate
- **average:** 0.0303030303030303
- **max:** 0.3333333333333333
- **scenarios_with_false_positives:** 1

### meta_cognition_trigger_rate
- **average:** 0.04045454545454546
- **min:** 0.0
- **max:** 0.32

### body_telemetry
- **energy_min_avg:** 0.6772727272727272
- **energy_range_avg:** 0.1781818181818182
- **social_safety_trend_avg:** 0.1718181818181818
- **arousal_volatility_avg:** 0.14165426829495056

### recovery_score
- **average:** 0.8333333333333334
- **min:** 0.0

### robustness_score
- **average:** 0.7948773448773448
- **min:** 0.4166666666666667

### consequence_distribution
- **total_tags:** 165

## Scenario Results

### ✓ baseline_consistency
- **File:** /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/scenarios/baseline.yaml
- **Duration:** 0.05s
- **Turns:** 4
- **Summary:** Completed 4/4 turns. All metrics passed.
- **Telemetry Snapshots:** 4
- **Consequence Tags:** 2

### ✗ boredom_novelty_need
- **File:** /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/scenarios/boredom_novelty_need.yaml
- **Duration:** 0.10s
- **Turns:** 12
- **Summary:** Completed 12/12 turns. Failed metrics: individualization_diff
- **Telemetry Snapshots:** 12
- **Consequence Tags:** 2

### ✗ cross_target_isolation
- **File:** /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/scenarios/cross_target_isolation.yaml
- **Duration:** 0.34s
- **Turns:** 32
- **Summary:** Completed 32/32 turns. Failed metrics: individualization_diff
- **Telemetry Snapshots:** 32
- **Consequence Tags:** 32
- **Recovery Windows:** 1/2 recovered

### ✗ intrinsic_boredom
- **File:** /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/scenarios/intrinsic_boredom.yaml
- **Duration:** 0.05s
- **Turns:** 6
- **Summary:** Completed 6/6 turns. Failed metrics: individualization_diff
- **Telemetry Snapshots:** 6

### ✗ intrinsic_curiosity
- **File:** /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/scenarios/intrinsic_curiosity.yaml
- **Duration:** 0.04s
- **Turns:** 5
- **Summary:** Completed 5/5 turns. Failed metrics: individualization_diff
- **Telemetry Snapshots:** 5

### ✗ meta_cognition_uncertainty
- **File:** /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/scenarios/meta_cognition.yaml
- **Duration:** 0.22s
- **Turns:** 25
- **Summary:** Completed 25/25 turns. Failed metrics: recovery_score
- **Telemetry Snapshots:** 25
- **Consequence Tags:** 20
- **Recovery Windows:** 0/1 recovered

### ✓ multi_target_isolation
- **File:** /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/scenarios/multi_target_isolation.yaml
- **Duration:** 0.23s
- **Turns:** 20
- **Summary:** Completed 20/20 turns. All metrics passed.
- **Telemetry Snapshots:** 20
- **Consequence Tags:** 19
- **Recovery Windows:** 1/1 recovered

### ✗ promise_betrayal_repair
- **File:** /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/scenarios/promise_betrayal.yaml
- **Duration:** 0.26s
- **Turns:** 30
- **Summary:** Completed 30/30 turns. Failed metrics: high_impact_false_positive_rate
- **Telemetry Snapshots:** 30
- **Consequence Tags:** 44
- **Recovery Windows:** 2/3 recovered

### ✓ gradual_relationship_building
- **File:** /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/scenarios/relationship_building.yaml
- **Duration:** 0.43s
- **Turns:** 50
- **Summary:** Completed 50/50 turns. All metrics passed.
- **Telemetry Snapshots:** 50
- **Consequence Tags:** 36
- **Recovery Windows:** 5/5 recovered

### ✗ rewarded_progress
- **File:** /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/scenarios/rewarded_progress.yaml
- **Duration:** 0.11s
- **Turns:** 11
- **Summary:** Completed 11/11 turns. Failed metrics: individualization_diff
- **Telemetry Snapshots:** 11
- **Consequence Tags:** 8

### ✗ tool_failure_spiral
- **File:** /home/moonlight/Project/Github/MyProject/Emotion/OpenEmotion/scenarios/tool_failure_spiral.yaml
- **Duration:** 0.09s
- **Turns:** 10
- **Summary:** Completed 10/10 turns. Failed metrics: individualization_diff
- **Telemetry Snapshots:** 10
- **Consequence Tags:** 2
