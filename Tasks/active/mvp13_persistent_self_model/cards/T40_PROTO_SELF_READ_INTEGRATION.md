# T40_PROTO_SELF_READ_INTEGRATION

```yaml
task_id: T40_PROTO_SELF_READ_INTEGRATION
parent_authority: Tasks/MVS_task_plan.md
phase: WP8
goal: Wire formal self-model read context into proto_self_v2 without creating a second truth source.
non_goals:
  - Formal writeback
  - Transport or delivery changes
write_scope:
  - OpenEmotion/openemotion/proto_self_v2/*
read_scope:
  - OpenEmotion/openemotion/self_model/*
  - EgoCore/app/runtime_v2/proto_self_runtime.py
  - OpenEmotion/openemotion/proto_self_v2/schemas.py
dependencies:
  - T10_OWNER_CONTRACT_CONVERGENCE
success_criteria:
  - runtime_summary.self_model_context is defined
  - proto_self_v2 consumes self-model read-only
  - proto_self_v2.state.self_model remains projection semantics only
verification_commands:
  - pytest -q OpenEmotion/openemotion/proto_self_v2/tests -k self_model
proof_required:
  - read-integration tests and trace evidence
rollback_point:
  - revert proto_self_v2 read wiring only
subagent_ready: true
```
