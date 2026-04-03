# T60_EGOCORE_BRIDGE

```yaml
task_id: T60_EGOCORE_BRIDGE
parent_authority: Tasks/MVS_task_plan.md
phase: WP8
goal: Add runtime and adapter orchestration for formal self-model read/write flow without giving EgoCore interpretation authority.
non_goals:
  - EgoCore-owned self-model semantics
  - Governor bypass
write_scope:
  - EgoCore/app/runtime_v2/*
  - EgoCore/app/openemotion_adapter/*
  - EgoCore/tests/*
read_scope:
  - OpenEmotion/openemotion/self_model/*
  - OpenEmotion/openemotion/proto_self_v2/*
dependencies:
  - T40_PROTO_SELF_READ_INTEGRATION
  - T50_GOVERNED_WRITEBACK
success_criteria:
  - runtime injects self_model_context
  - adapter carries self_model_delta/writeback results
  - EgoCore never becomes self-model owner
verification_commands:
  - pytest -q EgoCore/tests -k "proto_self_runtime or proto_self_v2_contracts or self_model"
proof_required:
  - bridge regression tests
rollback_point:
  - revert EgoCore bridge wiring only
subagent_ready: true
```
