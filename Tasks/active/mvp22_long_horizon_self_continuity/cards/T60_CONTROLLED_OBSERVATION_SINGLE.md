# T60_CONTROLLED_OBSERVATION_SINGLE

```yaml
task_id: T60_CONTROLLED_OBSERVATION_SINGLE
parent_authority: Tasks/MVS_task_plan.md
phase: WP17
goal: Capture the first controlled runtime-mainline self-continuity observation at V4/E4.
non_goals:
  - Batch stability claim
  - Maintenance closeout
write_scope:
  - OpenEmotion/tests/mvp22/*
  - OpenEmotion/tools/*
  - OpenEmotion/artifacts/mvp22/*
dependencies:
  - T50_CAUSAL_VALIDATION
success_criteria:
  - self_continuity_writeback_gate = allow_writeback
  - behavioral_authority_none = true
  - single controlled observation passes
verification_commands:
  - pytest -q OpenEmotion/tests/mvp22/test_controlled_observation.py
  - python3 OpenEmotion/tools/run_mvp22_controlled_observation.py
rollback_point:
  - revert single continuity observation only
```
