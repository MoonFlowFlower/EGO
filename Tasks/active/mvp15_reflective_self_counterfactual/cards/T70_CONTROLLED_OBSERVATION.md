# T70_CONTROLLED_OBSERVATION

```yaml
task_id: T70_CONTROLLED_OBSERVATION
parent_authority: Tasks/MVS_task_plan.md
phase: WP10
goal: Run controlled runtime-mainline observation for MVP15 without opening live external authority.
non_goals:
  - live autonomous reflection delivery
write_scope:
  - OpenEmotion/tools/*
  - OpenEmotion/artifacts/mvp15/*
  - OpenEmotion/tests/mvp15/test_controlled_observation.py
read_scope:
  - Tasks/MVP15_task_plan.md
  - OpenEmotion/openemotion/reflective_self/*
dependencies:
  - T60_CAUSAL_VALIDATION
success_criteria:
  - governance_violation_count = 0
  - replay_consistent = true
  - controlled observation reports can explain hold/pass
verification_commands:
  - pytest -q OpenEmotion/tests/mvp15/test_controlled_observation.py
  - python OpenEmotion/tools/run_mvp15_controlled_observation.py
proof_required:
  - controlled observation report(s)
rollback_point:
  - revert observation tooling patch only
subagent_ready: true
```
