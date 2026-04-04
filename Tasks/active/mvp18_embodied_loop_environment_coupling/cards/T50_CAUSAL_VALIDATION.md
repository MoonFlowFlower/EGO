# T50_CAUSAL_VALIDATION

```yaml
task_id: T50_CAUSAL_VALIDATION
parent_authority: Tasks/MVS_task_plan.md
phase: WP13
goal: Prove embodied proposals alter bounded downstream weighting rather than only logging text.
non_goals:
  - Controlled observation
  - Full maintenance closeout
write_scope:
  - OpenEmotion/tests/mvp18/*
  - OpenEmotion/tools/run_mvp18_causal_validation.py
  - OpenEmotion/artifacts/mvp18/*
read_scope:
  - Tasks/MVP18_task_plan.md
dependencies:
  - T30_EGOCORE_RUNTIME_BRIDGE
success_criteria:
  - at least three paired intervention/control proofs pass
  - text-only consequence wording changes do not count as proof
verification_commands:
  - pytest -q OpenEmotion/tests/mvp18/test_embodied_causal_formal_proof.py
proof_required:
  - V3/E3 causal artifact
rollback_point:
  - revert embodied causal proof changes only
subagent_ready: true
```
