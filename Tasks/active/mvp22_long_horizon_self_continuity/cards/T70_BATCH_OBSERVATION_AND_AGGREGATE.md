# T70_BATCH_OBSERVATION_AND_AGGREGATE

```yaml
task_id: T70_BATCH_OBSERVATION_AND_AGGREGATE
parent_authority: Tasks/MVS_task_plan.md
phase: WP17
goal: Promote MVP22 from a single controlled sample to repeated batch E5.
non_goals:
  - Maintenance closeout
write_scope:
  - OpenEmotion/scenarios/mvp22_observation_bank/*
  - OpenEmotion/tests/mvp22/*
  - OpenEmotion/tools/*
  - OpenEmotion/artifacts/mvp22/*
dependencies:
  - T60_CONTROLLED_OBSERVATION_SINGLE
success_criteria:
  - report_count >= 3
  - accepted_count == report_count
  - proposal_only_discipline_count == report_count
  - behavioral_authority_none_count == report_count
verification_commands:
  - pytest -q OpenEmotion/tests/mvp22/test_controlled_observation_batch.py
  - python3 OpenEmotion/tools/run_mvp22_controlled_observation_batch.py
rollback_point:
  - revert batch continuity observation only
```
