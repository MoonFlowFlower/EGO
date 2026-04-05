# T00_AUTHORITY_FREEZE

```yaml
task_id: T00_AUTHORITY_FREEZE
parent_authority: Tasks/MVS_task_plan.md
phase: WP17
goal: Freeze WP17/MVP22 authority, ownership, IO contract, upstream boundary terms, and claim ceiling.
non_goals:
  - Implement self_continuity owner/runtime code
  - Reopen WP8~WP16
  - Claim implementation, mainline wiring, E4/E5, observation, or maintenance
write_scope:
  - Tasks/MVS_task_plan.md
  - Tasks/MVP22_task_plan.md
  - Tasks/active/mvp22_long_horizon_self_continuity/*
  - PROJECT_MEMORY.md
read_scope:
  - Tasks/MVP21_task_plan.md
  - OpenEmotion/roadmap/SELF_AWARE_AI_ROADMAP.md
dependencies: []
success_criteria:
  - WP17 appears in Tasks/MVS_task_plan.md
  - MVP22 phase-detail plan and active package exist
  - claim ceiling is explicitly frozen to authority_frozen/task_package_ready
verification_commands:
  - rg -n "WP17|MVP22|authority_frozen|task_package_ready|self_continuity|proposal_only|behavioral_authority = none" Tasks/MVS_task_plan.md Tasks/MVP22_task_plan.md Tasks/active/mvp22_long_horizon_self_continuity/*
proof_required:
  - docs consistency only
rollback_point:
  - revert WP17 docs only
subagent_ready: true
```
