# T30_IDENTITY_INVARIANTS_AND_DRIFT

```yaml
task_id: T30_IDENTITY_INVARIANTS_AND_DRIFT
parent_authority: Tasks/MVS_task_plan.md
phase: WP8
goal: Implement identity invariant classes, drift detection, and hold/rollback policy.
non_goals:
  - Transport behavior changes
  - Live autonomy changes
write_scope:
  - OpenEmotion/openemotion/self_model/*
  - OpenEmotion/tests/mvp13/*
read_scope:
  - OpenEmotion/docs/mvp13/IDENTITY_INVARIANTS_AND_DRIFT_POLICY.md
  - OpenEmotion/docs/mvp13/SELF_MODEL_UPDATE_POLICY.md
dependencies:
  - T20_PERSISTENCE_AUDIT_REPLAY
success_criteria:
  - hard invariants reject invalid writes
  - drift thresholds produce hold or rollback
  - invariant/drift decisions are auditable
verification_commands:
  - pytest -q OpenEmotion/tests/mvp13 -k "invariant or drift"
proof_required:
  - invariant and drift regression tests
rollback_point:
  - revert invariant/drift policy implementation only
subagent_ready: true
```
