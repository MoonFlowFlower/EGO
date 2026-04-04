# T60_CONTROLLED_OBSERVATION_SINGLE

```yaml
task_id: T60_CONTROLLED_OBSERVATION_SINGLE
parent_authority: Tasks/MVS_task_plan.md
phase: WP12
goal: Capture the first controlled mainline observation for social proposal-only writeback.
non_goals:
  - Enable live social outreach
write_scope:
  - OpenEmotion/tools/*
  - OpenEmotion/tests/mvp17/test_controlled_observation.py
  - OpenEmotion/artifacts/mvp17/*
read_scope:
  - Tasks/MVP17_task_plan.md
  - OpenEmotion/openemotion/social_self/*
  - EgoCore/app/runtime_v2/*
dependencies:
  - T50_CAUSAL_VALIDATION
success_criteria:
  - single controlled observation reaches V4/E4
  - social_writeback_gate allows writeback
  - behavioral_authority remains none
verification_commands:
  - pytest -q OpenEmotion/tests/mvp17/test_controlled_observation.py
proof_required:
  - controlled observation report
rollback_point:
  - revert single-observation tooling only
subagent_ready: true
```
