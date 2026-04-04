# T30_EGOCORE_RUNTIME_BRIDGE

```yaml
task_id: T30_EGOCORE_RUNTIME_BRIDGE
parent_authority: Tasks/MVS_task_plan.md
phase: WP13
goal: Inject bounded embodied context into the current EgoCore runtime mainline.
non_goals:
  - Direct environment execution authority
  - Live autonomy or transport expansion
write_scope:
  - EgoCore/app/runtime_v2/*
  - EgoCore/app/openemotion_adapter/*
  - EgoCore/tests/test_runtime_v2_proto_self_runtime.py
read_scope:
  - Tasks/MVP18_task_plan.md
  - OpenEmotion/openemotion/proto_self_v2/*
dependencies:
  - T20_PROTO_SELF_CONTRACT_INTEGRATION
success_criteria:
  - runtime_v2 injects embodied_self_context and environment_context
  - embodied_writeback remains gated and proposal-only
verification_commands:
  - pytest -q EgoCore/tests/test_runtime_v2_proto_self_runtime.py -k embodied
proof_required:
  - runtime bridge tests
rollback_point:
  - revert embodied runtime bridge only
subagent_ready: true
```
