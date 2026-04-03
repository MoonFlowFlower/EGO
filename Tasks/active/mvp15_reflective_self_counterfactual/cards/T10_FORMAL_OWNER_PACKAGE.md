# T10_FORMAL_OWNER_PACKAGE

```yaml
task_id: T10_FORMAL_OWNER_PACKAGE
parent_authority: Tasks/MVS_task_plan.md
phase: WP10
goal: Create the OpenEmotion reflective_self formal owner package under openemotion/.
non_goals:
  - Keep emotiond/reflection_engine as formal owner
write_scope:
  - OpenEmotion/openemotion/reflective_self/*
  - OpenEmotion/tests/mvp15/test_reflective_owner_infra.py
read_scope:
  - OpenEmotion/docs/mvp15/REFLECTIVE_SELF_ARCHITECTURE.md
  - OpenEmotion/docs/mvp15/REFLECTION_STATE_SCHEMA.md
  - OpenEmotion/docs/mvp15/COUNTERFACTUAL_SELF_EVALUATION.md
dependencies:
  - T00_AUTHORITY_FREEZE
success_criteria:
  - reflective owner package exists under openemotion/
  - owner state covers reflection queue, diagnosis records, counterfactual records, revision proposals, unresolved items, reflection history
  - owner schema/state are replayable and audit-friendly
verification_commands:
  - pytest -q OpenEmotion/tests/mvp15/test_reflective_owner_infra.py
proof_required:
  - owner package tests
rollback_point:
  - revert reflective_self owner package only
subagent_ready: true
```
