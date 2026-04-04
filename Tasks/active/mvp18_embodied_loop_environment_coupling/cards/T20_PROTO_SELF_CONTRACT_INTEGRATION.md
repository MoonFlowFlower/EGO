# T20_PROTO_SELF_CONTRACT_INTEGRATION

```yaml
task_id: T20_PROTO_SELF_CONTRACT_INTEGRATION
parent_authority: Tasks/MVS_task_plan.md
phase: WP13
goal: Connect embodied_self through a bounded proto_self_v2 contract.
non_goals:
  - Implement EgoCore runtime bridge
  - Grant any action authority
write_scope:
  - OpenEmotion/openemotion/proto_self_v2/*
  - OpenEmotion/tests/mvp18/test_embodied_proto_self_integration.py
read_scope:
  - Tasks/MVP18_task_plan.md
  - OpenEmotion/openemotion/embodied_self/*
dependencies:
  - T10_FORMAL_OWNER_PACKAGE
success_criteria:
  - proto_self_v2 consumes embodied_self_context and environment_context
  - embodied outputs stay proposal-only with behavioral_authority none
verification_commands:
  - pytest -q OpenEmotion/tests/mvp18/test_embodied_proto_self_integration.py
proof_required:
  - contract integration tests
rollback_point:
  - revert embodied proto-self changes only
subagent_ready: true
```
