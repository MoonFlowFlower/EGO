# T10_OWNER_CONTRACT_CONVERGENCE

```yaml
task_id: T10_OWNER_CONTRACT_CONVERGENCE
parent_authority: Tasks/MVS_task_plan.md
phase: WP8
goal: Converge MVP13 on openemotion/self_model formal owner contract only.
non_goals:
  - Reintroduce legacy behavioral_tendencies or mirror ownership
write_scope:
  - OpenEmotion/openemotion/self_model/*
  - OpenEmotion/schemas/self_model.schema.json
  - OpenEmotion/tests/mvp13/test_self_model_owner_contract.py
read_scope:
  - OpenEmotion/docs/mvp13/SELF_MODEL_STATE_SCHEMA.md
  - OpenEmotion/docs/mvp13/MVP13_STAGE_OVERVIEW.md
dependencies:
  - T00_AUTHORITY_FREEZE
success_criteria:
  - formal owner files and schema agree
  - allowed proof levers are explicit
  - legacy owner paths are excluded from proof claims
verification_commands:
  - pytest -q OpenEmotion/tests/mvp13/test_self_model_owner_contract.py
proof_required:
  - owner contract tests
rollback_point:
  - revert owner contract convergence patch only
subagent_ready: true
```
