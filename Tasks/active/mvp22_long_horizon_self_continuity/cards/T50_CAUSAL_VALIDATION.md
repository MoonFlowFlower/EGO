# T50_CAUSAL_VALIDATION

```yaml
task_id: T50_CAUSAL_VALIDATION
parent_authority: Tasks/MVS_task_plan.md
phase: WP17
goal: Prove that continuity and persistence proposals cause bounded downstream shifts rather than text-only differences.
non_goals:
  - Controlled observation
  - Maintenance closeout
write_scope:
  - OpenEmotion/tests/mvp22/*
  - OpenEmotion/tools/*
  - OpenEmotion/artifacts/mvp22/*
dependencies:
  - T30_EGOCORE_RUNTIME_BRIDGE
success_criteria:
  - paired intervention/control proofs show bounded downstream change
  - wording-only changes do not produce structural effects
verification_commands:
  - pytest -q OpenEmotion/tests/mvp22/test_self_continuity_causal_formal_proof.py
  - python3 OpenEmotion/tools/run_mvp22_causal_validation.py
rollback_point:
  - revert self_continuity causal proof only
```
