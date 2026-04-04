# T20_PROTO_SELF_CONTRACT_INTEGRATION

```yaml
task_id: T20_PROTO_SELF_CONTRACT_INTEGRATION
parent_authority: Tasks/MVS_task_plan.md
phase: WP12
goal: Add bounded social_self read/write contract surfaces to proto_self_v2 without creating a second truth source.
non_goals:
  - Move social owner logic into proto_self_v2
write_scope:
  - OpenEmotion/openemotion/proto_self_v2/*
  - OpenEmotion/tests/mvp17/test_social_proto_self_integration.py
read_scope:
  - Tasks/MVP17_task_plan.md
  - OpenEmotion/openemotion/proto_self_v2/*
  - OpenEmotion/openemotion/self_model/*
  - OpenEmotion/openemotion/endogenous_drives/*
  - OpenEmotion/openemotion/reflective_self/*
  - OpenEmotion/openemotion/developmental_self/*
dependencies:
  - T10_FORMAL_OWNER_PACKAGE
success_criteria:
  - proto_self_v2 consumes runtime_summary.social_self_context and social_context
  - KernelOutputV2 exposes the locked WP12 outputs
  - trace payload mirrors social context and writeback candidate
verification_commands:
  - pytest -q OpenEmotion/tests/mvp17/test_social_proto_self_integration.py
proof_required:
  - proto_self contract tests
rollback_point:
  - revert proto_self_v2 social integration only
subagent_ready: true
```
