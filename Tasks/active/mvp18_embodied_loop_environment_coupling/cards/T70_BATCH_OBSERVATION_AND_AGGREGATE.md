# T70_BATCH_OBSERVATION_AND_AGGREGATE

```yaml
task_id: T70_BATCH_OBSERVATION_AND_AGGREGATE
parent_authority: Tasks/MVS_task_plan.md
phase: WP13
goal: Push embodied controlled observation from single-sample E4 to batch E5.
non_goals:
  - Maintenance closeout
  - Authority expansion
write_scope:
  - OpenEmotion/scenarios/mvp18_observation_bank/*
  - OpenEmotion/tools/run_mvp18_controlled_observation_batch.py
  - OpenEmotion/tests/mvp18/test_controlled_observation_batch.py
  - OpenEmotion/artifacts/mvp18/*
read_scope:
  - Tasks/MVP18_task_plan.md
dependencies:
  - T60_CONTROLLED_OBSERVATION_SINGLE
success_criteria:
  - report_count >= 3
  - proposal_only and behavioral_authority none stay preserved across batch
verification_commands:
  - pytest -q OpenEmotion/tests/mvp18/test_controlled_observation_batch.py
  - python3 OpenEmotion/tools/run_mvp18_controlled_observation_batch.py
proof_required:
  - V5/E5 batch artifact
rollback_point:
  - revert embodied batch observation changes only
subagent_ready: true
```
