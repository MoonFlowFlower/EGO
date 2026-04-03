# T80_SUBAGENT_ASSIGNMENT

```yaml
task_id: T80_SUBAGENT_ASSIGNMENT
parent_authority: Tasks/MVS_task_plan.md
phase: WP8
goal: Freeze subagent-ready work partition, ordering, and write-scope boundaries.
non_goals:
  - Implement the subtasks
  - Review code changes
write_scope:
  - Tasks/active/mvp13_persistent_self_model/SUBAGENT_ASSIGNMENT.md
  - Tasks/active/mvp13_persistent_self_model/cards/*
read_scope:
  - all WP8 authority and contract docs
dependencies:
  - T00_AUTHORITY_FREEZE
success_criteria:
  - every card has owner, write_scope, dependencies, verification, rollback
  - parallel boundaries are explicit
verification_commands:
  - rg -n "subagent_ready|write_scope|dependencies|verification_commands" Tasks/active/mvp13_persistent_self_model/cards
proof_required:
  - repo-tracked task cards
rollback_point:
  - revert task-pack assignment docs only
subagent_ready: true
```
