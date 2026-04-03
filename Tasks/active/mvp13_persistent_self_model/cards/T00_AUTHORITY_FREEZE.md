# T00_AUTHORITY_FREEZE

```yaml
task_id: T00_AUTHORITY_FREEZE
parent_authority: Tasks/MVS_task_plan.md
phase: WP8
goal: Freeze WP8 authority, parent-child routing, and legacy reference-only boundaries.
non_goals:
  - Implement MVP13 code
  - Migrate legacy mirror logic
write_scope:
  - Tasks/MVS_task_plan.md
  - Tasks/MVP13_task_plan.md
  - Tasks/active/mvp13_persistent_self_model/*
read_scope:
  - OpenEmotion/docs/mvp13/*
  - OpenEmotion/artifacts/mvp13/TASK.md
  - legacy MVP13 mirror files
dependencies: []
success_criteria:
  - WP8 exists in parent authority
  - child authority exists and declares parent-child routing
  - legacy reference register exists
verification_commands:
  - rg -n "WP8|Persistent Self-Model" Tasks/MVS_task_plan.md Tasks/MVP13_task_plan.md
proof_required:
  - repo-tracked authority docs
rollback_point:
  - revert new WP8/task-pack docs only
subagent_ready: true
```
