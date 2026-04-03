# T00_AUTHORITY_FREEZE

```yaml
task_id: T00_AUTHORITY_FREEZE
parent_authority: Tasks/MVS_task_plan.md
phase: WP10
goal: Freeze MVP15 authority, owner target, IO contract, and boundary rules before any code changes.
non_goals:
  - Implement MVP15 runtime code
write_scope:
  - Tasks/MVS_task_plan.md
  - Tasks/MVP15_task_plan.md
  - Tasks/active/mvp15_reflective_self_counterfactual/*
  - PROJECT_MEMORY.md
read_scope:
  - OpenEmotion/roadmap/versions/MVP15.spec.yaml
  - OpenEmotion/docs/mvp15/*
  - Tasks/active/SELF_AWARE_STEP_06*.md
dependencies: []
success_criteria:
  - WP10 authority package exists
  - legacy reflection lines are marked reference-only
  - boundary with WP9 is frozen
verification_commands:
  - git diff --check
  - rg -n "WP10|MVP15|reflective_self|maintenance_mode" Tasks/MVS_task_plan.md Tasks/MVP15_task_plan.md Tasks/active/mvp15_reflective_self_counterfactual/*
proof_required:
  - doc consistency
rollback_point:
  - revert WP10 authority-package docs only
subagent_ready: true
```
