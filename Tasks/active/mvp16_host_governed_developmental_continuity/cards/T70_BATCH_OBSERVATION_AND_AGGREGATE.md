# T70_BATCH_OBSERVATION_AND_AGGREGATE

```yaml
task_id: T70_BATCH_OBSERVATION_AND_AGGREGATE
parent_authority: Tasks/MVS_task_plan.md
phase: WP11
goal: Aggregate repeated controlled developmental samples to the E5 maintenance threshold.
non_goals:
  - Broader transport or live evidence
write_scope:
  - OpenEmotion/scenarios/mvp16_observation_bank/*
  - OpenEmotion/tools/mvp16_scenario_bank.py
  - OpenEmotion/tools/run_mvp16_controlled_observation_batch.py
  - OpenEmotion/tools/aggregate_mvp16_observations.py
  - OpenEmotion/tests/mvp16/test_controlled_observation_batch.py
  - OpenEmotion/artifacts/mvp16/*
read_scope:
  - Tasks/MVP16_task_plan.md
  - OpenEmotion/artifacts/mvp16/*
dependencies:
  - T60_CONTROLLED_OBSERVATION_SINGLE
success_criteria:
  - batch report_count >= 3
  - accepted_count == report_count
  - replay_consistent_count == report_count
  - proposal_only_discipline_count == report_count
  - behavioral_authority_none_count == report_count
  - bounded_influence_present_count == report_count
  - identity_preservation_violation_count == 0
verification_commands:
  - pytest -q OpenEmotion/tests/mvp16/test_controlled_observation_batch.py
  - python3 OpenEmotion/tools/run_mvp16_controlled_observation_batch.py
proof_required:
  - batch observation aggregate
rollback_point:
  - revert batch observation tooling only
subagent_ready: true
```
