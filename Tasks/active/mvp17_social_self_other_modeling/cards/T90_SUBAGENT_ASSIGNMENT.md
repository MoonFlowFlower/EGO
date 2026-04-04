# T90_SUBAGENT_ASSIGNMENT

```yaml
task_id: T90_SUBAGENT_ASSIGNMENT
parent_authority: Tasks/MVS_task_plan.md
phase: WP12
goal: Keep subagent decomposition synchronized with the current MVP17 authority package.
non_goals:
  - Implement MVP17 runtime code
write_scope:
  - Tasks/active/mvp17_social_self_other_modeling/SUBAGENT_ASSIGNMENT.md
read_scope:
  - Tasks/MVP17_task_plan.md
  - Tasks/active/mvp17_social_self_other_modeling/cards/*
dependencies:
  - T00_AUTHORITY_FREEZE
success_criteria:
  - each task has one owner and one write scope
  - dependency order matches the authority package
verification_commands:
  - rg -n "T00|T10|T20|T30|T40|T50|T60|T70|T80|T90" Tasks/active/mvp17_social_self_other_modeling/SUBAGENT_ASSIGNMENT.md
proof_required:
  - synchronized assignment table
rollback_point:
  - revert subagent assignment docs only
subagent_ready: true
```
