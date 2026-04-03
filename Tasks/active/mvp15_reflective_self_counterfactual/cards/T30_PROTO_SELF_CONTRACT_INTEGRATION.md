# T30_PROTO_SELF_CONTRACT_INTEGRATION

```yaml
task_id: T30_PROTO_SELF_CONTRACT_INTEGRATION
parent_authority: Tasks/MVS_task_plan.md
phase: WP10
goal: Extend proto_self_v2 to consume bounded reflection context and emit structured downstream proposal hooks.
non_goals:
  - Give proto_self_v2 ownership of reflective state
write_scope:
  - OpenEmotion/openemotion/proto_self_v2/*
  - OpenEmotion/tests/mvp15/test_reflection_proto_self_integration.py
read_scope:
  - Tasks/MVP15_task_plan.md
  - OpenEmotion/openemotion/reflective_self/*
dependencies:
  - T10_FORMAL_OWNER_PACKAGE
  - T20_REPLAY_AUDIT_PROPOSAL_STATE
success_criteria:
  - proto_self_v2 consumes bounded reflection projection
  - downstream outputs remain structured and proposal-disciplined
  - trace payload exposes reflection_context
verification_commands:
  - pytest -q OpenEmotion/tests/mvp15/test_reflection_proto_self_integration.py
proof_required:
  - contract and trace tests
rollback_point:
  - revert proto_self reflection integration only
subagent_ready: true
```
