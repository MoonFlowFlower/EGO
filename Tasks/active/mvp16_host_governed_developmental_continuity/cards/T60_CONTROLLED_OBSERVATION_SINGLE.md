# T60_CONTROLLED_OBSERVATION_SINGLE

```yaml
task_id: T60_CONTROLLED_OBSERVATION_SINGLE
parent_authority: Tasks/MVS_task_plan.md
phase: WP11
goal: Produce the first controlled mainline developmental observation sample without opening live external authority.
non_goals:
  - Live or Telegram authority expansion
write_scope:
  - OpenEmotion/tools/run_mvp16_controlled_observation.py
  - OpenEmotion/tests/mvp16/test_controlled_observation.py
  - OpenEmotion/artifacts/mvp16/*
read_scope:
  - Tasks/MVP16_task_plan.md
  - OpenEmotion/openemotion/developmental_self/*
  - OpenEmotion/openemotion/proto_self_v2/*
dependencies:
  - T50_CAUSAL_VALIDATION
success_criteria:
  - single controlled observation passes at V4/E4
  - developmental_writeback_gate allows writeback
  - replay_valid is true
  - identity_preservation_violation_count is zero
verification_commands:
  - pytest -q OpenEmotion/tests/mvp16/test_controlled_observation.py
  - python3 OpenEmotion/tools/run_mvp16_controlled_observation.py
proof_required:
  - single-sample observation report
rollback_point:
  - revert single-observation tooling only
subagent_ready: true
```
