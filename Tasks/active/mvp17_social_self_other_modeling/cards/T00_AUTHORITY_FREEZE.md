# T00_AUTHORITY_FREEZE

```yaml
task_id: T00_AUTHORITY_FREEZE
parent_authority: Tasks/MVS_task_plan.md
phase: WP12
goal: Freeze MVP17 authority, owner target, IO contract, and boundary rules before any code changes.
non_goals:
  - Implement MVP17 runtime code
write_scope:
  - Tasks/MVS_task_plan.md
  - Tasks/MVP17_task_plan.md
  - Tasks/active/mvp17_social_self_other_modeling/*
  - PROJECT_MEMORY.md
read_scope:
  - OpenEmotion/roadmap/SELF_AWARE_AI_ROADMAP.md
  - OpenEmotion/roadmap/VersionRoadmap.md
  - OpenEmotion/docs/archive/mvp9/MVP9_SPEC.md
dependencies: []
success_criteria:
  - WP12 authority package exists
  - historical social lines are marked reference-only or input-only
  - boundary with WP11 is frozen
verification_commands:
  - git diff --check
  - rg -n "WP12|MVP17|social_self|authority_frozen" Tasks/MVS_task_plan.md Tasks/MVP17_task_plan.md Tasks/active/mvp17_social_self_other_modeling/*
proof_required:
  - doc consistency
rollback_point:
  - revert WP12 authority-package docs only
subagent_ready: true
```
