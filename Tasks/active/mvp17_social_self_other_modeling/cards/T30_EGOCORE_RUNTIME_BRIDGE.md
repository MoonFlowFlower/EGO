# T30_EGOCORE_RUNTIME_BRIDGE

```yaml
task_id: T30_EGOCORE_RUNTIME_BRIDGE
parent_authority: Tasks/MVS_task_plan.md
phase: WP12
goal: Bridge runtime_summary social inputs and governed social writeback hooks through the current EgoCore mainline.
non_goals:
  - Grant direct reply or tool authority to social_self
write_scope:
  - EgoCore/app/runtime_v2/*
  - EgoCore/app/openemotion_adapter/*
  - EgoCore/tests/*
read_scope:
  - Tasks/MVP17_task_plan.md
  - OpenEmotion/openemotion/social_self/*
  - OpenEmotion/openemotion/proto_self_v2/*
dependencies:
  - T20_PROTO_SELF_CONTRACT_INTEGRATION
success_criteria:
  - runtime_v2 injects social_context and social_self_context
  - governed social writeback candidate reaches the current mainline
  - behavioral_authority remains none
verification_commands:
  - pytest -q EgoCore/tests/test_runtime_v2_proto_self_runtime.py -k social
proof_required:
  - runtime bridge tests
rollback_point:
  - revert EgoCore social bridge only
subagent_ready: true
```
