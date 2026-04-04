# T80_CLOSEOUT_AND_QA_BASELINE

```yaml
task_id: T80_CLOSEOUT_AND_QA_BASELINE
parent_authority: Tasks/MVS_task_plan.md
phase: WP13
goal: Freeze closeout docs, QA baseline, and maintenance ledger for WP13.
non_goals:
  - Start WP14
  - Relax any authority boundary
write_scope:
  - Tasks/active/mvp18_embodied_loop_environment_coupling/*
  - Tasks/MVP18_task_plan.md
  - PROJECT_MEMORY.md
  - OpenEmotion/artifacts/mvp18/MVP18_COMPLETION_CURRENT.*
read_scope:
  - Tasks/MVS_task_plan.md
dependencies:
  - T70_BATCH_OBSERVATION_AND_AGGREGATE
success_criteria:
  - WP13 status becomes maintenance_mode only after controlled E5
  - QA baseline exists and claim ceiling is explicit
verification_commands:
  - rg -n "maintenance_mode|E5|direct reply authority|broader transport" Tasks/active/mvp18_embodied_loop_environment_coupling/* Tasks/MVP18_task_plan.md
proof_required:
  - closeout docs and completion artifact
rollback_point:
  - revert WP13 closeout docs only
subagent_ready: true
```
