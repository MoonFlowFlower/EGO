# T70_BATCH_OBSERVATION_AND_AGGREGATE

```yaml
task_id: T70_BATCH_OBSERVATION_AND_AGGREGATE
parent_authority: Tasks/MVS_task_plan.md
phase: WP12
goal: Use repeated scenario-bank observations to move WP12 from single-sample E4 to controlled E5.
non_goals:
  - Claim live transport evidence
write_scope:
  - OpenEmotion/scenarios/mvp17_observation_bank/*
  - OpenEmotion/tools/*
  - OpenEmotion/tests/mvp17/test_controlled_observation_batch.py
  - OpenEmotion/artifacts/mvp17/*
read_scope:
  - Tasks/MVP17_task_plan.md
  - OpenEmotion/tools/run_mvp17_controlled_observation.py
dependencies:
  - T60_CONTROLLED_OBSERVATION_SINGLE
success_criteria:
  - report_count >= 3
  - accepted_count == report_count
  - proposal_only_discipline_count == report_count
  - behavioral_authority_none_count == report_count
verification_commands:
  - pytest -q OpenEmotion/tests/mvp17/test_controlled_observation_batch.py
proof_required:
  - aggregate observation report
rollback_point:
  - revert batch observation tooling only
subagent_ready: true
```
