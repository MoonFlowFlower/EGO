# T20_REPLAY_AUDIT_PROPOSAL_STATE

```yaml
task_id: T20_REPLAY_AUDIT_PROPOSAL_STATE
parent_authority: Tasks/MVS_task_plan.md
phase: WP10
goal: Implement replay, audit, and proposal-discipline state transitions for the reflective owner.
non_goals:
  - Direct behavioral authority
write_scope:
  - OpenEmotion/openemotion/reflective_self/*
  - OpenEmotion/tests/mvp15/test_reflective_replay_and_governance.py
read_scope:
  - OpenEmotion/docs/mvp15/REFLECTIVE_GOVERNANCE_POLICY.md
  - OpenEmotion/docs/mvp15/MVP15_EXIT_CRITERIA.md
dependencies:
  - T10_FORMAL_OWNER_PACKAGE
success_criteria:
  - reflection jobs and counterfactual runs are replayable
  - proposals remain proposal_only
  - audit history and gate metadata are explicit
verification_commands:
  - pytest -q OpenEmotion/tests/mvp15/test_reflective_replay_and_governance.py
proof_required:
  - replay / governance tests
rollback_point:
  - revert reflective replay/governance patch only
subagent_ready: true
```
