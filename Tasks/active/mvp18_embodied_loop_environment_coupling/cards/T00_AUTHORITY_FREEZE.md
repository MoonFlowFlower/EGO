# T00_AUTHORITY_FREEZE

```yaml
task_id: T00_AUTHORITY_FREEZE
parent_authority: Tasks/MVS_task_plan.md
phase: WP13
goal: Freeze WP13/MVP18 authority, ownership, IO contract, and upstream boundary terms.
non_goals:
  - Implement embodied owner/runtime code
  - Reopen WP12
write_scope:
  - Tasks/MVS_task_plan.md
  - Tasks/MVP18_task_plan.md
  - Tasks/active/mvp18_embodied_loop_environment_coupling/*
  - PROJECT_MEMORY.md
read_scope:
  - OpenEmotion/roadmap/VersionRoadmap.md
  - OpenEmotion/emotiond/consequence.py
  - OpenEmotion/emotiond/science/interventions.py
dependencies: []
success_criteria:
  - WP13 appears in Tasks/MVS_task_plan.md
  - MVP18 phase-detail plan and active package exist
  - legacy/reference surfaces are explicitly registered
verification_commands:
  - rg -n "WP13|MVP18|embodied_self|proposal_only|behavioral_authority = none" Tasks/MVS_task_plan.md Tasks/MVP18_task_plan.md Tasks/active/mvp18_embodied_loop_environment_coupling/*
proof_required:
  - docs consistency only
rollback_point:
  - revert WP13 docs only
subagent_ready: true
```
