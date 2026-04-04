# T90_SUBAGENT_ASSIGNMENT

```yaml
task_id: T90_SUBAGENT_ASSIGNMENT
parent_authority: Tasks/MVS_task_plan.md
phase: WP11
goal: Keep subagent decomposition synchronized with the current MVP16 authority package.
non_goals:
  - Implement MVP16 runtime code
write_scope:
  - Tasks/active/mvp16_host_governed_developmental_continuity/SUBAGENT_ASSIGNMENT.md
read_scope:
  - Tasks/MVP16_task_plan.md
  - Tasks/active/mvp16_host_governed_developmental_continuity/cards/*
dependencies:
  - T00_AUTHORITY_FREEZE
success_criteria:
  - each task has one owner and one write scope
  - dependency order matches the authority package
verification_commands:
  - rg -n "T00|T10|T20|T30|T40|T50|T60|T70|T80|T90" Tasks/active/mvp16_host_governed_developmental_continuity/SUBAGENT_ASSIGNMENT.md
proof_required:
  - synchronized assignment table
rollback_point:
  - revert subagent assignment docs only
subagent_ready: true
```
