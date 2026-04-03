# T40_EGOCORE_RUNTIME_BRIDGE

```yaml
task_id: T40_EGOCORE_RUNTIME_BRIDGE
parent_authority: Tasks/MVS_task_plan.md
phase: WP10
goal: Bridge reflective owner input/output through runtime_v2 and the OpenEmotion adapter without granting new authority.
non_goals:
  - Let EgoCore interpret reflection semantics as owner
write_scope:
  - EgoCore/app/runtime_v2/*
  - EgoCore/app/openemotion_adapter/*
  - EgoCore/tests/*
read_scope:
  - Tasks/MVP15_task_plan.md
  - OpenEmotion/openemotion/proto_self_v2/*
dependencies:
  - T30_PROTO_SELF_CONTRACT_INTEGRATION
success_criteria:
  - runtime summary carries reflection-relevant structured inputs
  - adapter returns bounded reflection outputs to host context
  - Governor boundary remains intact
verification_commands:
  - pytest -q EgoCore/tests/test_runtime_v2_proto_self_runtime.py -k reflection
proof_required:
  - bridge tests
rollback_point:
  - revert EgoCore reflection bridge patch only
subagent_ready: true
```
