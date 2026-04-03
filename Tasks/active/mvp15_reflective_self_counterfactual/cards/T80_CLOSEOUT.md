# T80_CLOSEOUT

```yaml
task_id: T80_CLOSEOUT
parent_authority: Tasks/MVS_task_plan.md
phase: WP10
goal: Close WP10 on the controlled observation axis and switch it to maintenance mode when evidence is sufficient.
non_goals:
  - Claim live autonomy or transport maturity
write_scope:
  - Tasks/active/mvp15_reflective_self_counterfactual/README.md
  - Tasks/active/mvp15_reflective_self_counterfactual/STATUS.md
  - Tasks/active/mvp15_reflective_self_counterfactual/MAINTENANCE_LEDGER.md
  - PROJECT_MEMORY.md
  - OpenEmotion/artifacts/mvp15/MVP15_COMPLETION_CURRENT.*
read_scope:
  - OpenEmotion/artifacts/mvp15/*
dependencies:
  - T70_CONTROLLED_OBSERVATION
success_criteria:
  - closure documents agree on what is proven and not proven
  - maintenance ledger intake rule is defined
  - completion artifact exists
verification_commands:
  - git diff --check
  - rg -n "maintenance_mode|E5|direct reply authority|broader transport" Tasks/active/mvp15_reflective_self_counterfactual/* Tasks/MVP15_task_plan.md
proof_required:
  - closure artifact
rollback_point:
  - revert closeout docs only
subagent_ready: true
```
