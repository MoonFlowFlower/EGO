# T90_SUBAGENT_ASSIGNMENT

```yaml
task_id: T90_SUBAGENT_ASSIGNMENT
parent_authority: Tasks/MVS_task_plan.md
phase: WP10
goal: Keep subagent decomposition synchronized with the current MVP15 authority package.
non_goals:
  - Implement MVP15 runtime code
write_scope:
  - Tasks/active/mvp15_reflective_self_counterfactual/SUBAGENT_ASSIGNMENT.md
read_scope:
  - Tasks/active/mvp15_reflective_self_counterfactual/cards/*
dependencies:
  - T00_AUTHORITY_FREEZE
success_criteria:
  - write scopes are disjoint
  - dependency order is explicit
  - handoff requirements are explicit
verification_commands:
  - rg -n "Repo Owner|可并行|写入范围" Tasks/active/mvp15_reflective_self_counterfactual/SUBAGENT_ASSIGNMENT.md
proof_required:
  - assignment matrix
rollback_point:
  - revert subagent assignment doc only
subagent_ready: true
```
