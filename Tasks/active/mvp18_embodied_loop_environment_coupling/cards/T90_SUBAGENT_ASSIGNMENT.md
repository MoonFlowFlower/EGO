# T90_SUBAGENT_ASSIGNMENT

```yaml
task_id: T90_SUBAGENT_ASSIGNMENT
parent_authority: Tasks/MVS_task_plan.md
phase: WP13
goal: Keep the WP13 subagent routing table synchronized with the authority package.
non_goals:
  - Implement any phase code
write_scope:
  - Tasks/active/mvp18_embodied_loop_environment_coupling/SUBAGENT_ASSIGNMENT.md
read_scope:
  - Tasks/MVP18_task_plan.md
  - Tasks/active/mvp18_embodied_loop_environment_coupling/cards/*
dependencies:
  - T00_AUTHORITY_FREEZE
success_criteria:
  - assignment table matches current cards and write scopes
verification_commands:
  - rg -n "T00|T10|T20|T30|T40|T50|T60|T70|T80|T90" Tasks/active/mvp18_embodied_loop_environment_coupling/SUBAGENT_ASSIGNMENT.md
proof_required:
  - docs consistency only
rollback_point:
  - revert subagent assignment only
subagent_ready: true
```
