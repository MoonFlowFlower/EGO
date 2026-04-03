# T50_LEGACY_DEMOTION_AND_MIGRATION

```yaml
task_id: T50_LEGACY_DEMOTION_AND_MIGRATION
parent_authority: Tasks/MVS_task_plan.md
phase: WP10
goal: Demote legacy emotiond reflection/counterfactual surfaces to compatibility/reference and add a migration map.
non_goals:
  - Remove legacy files before the new owner path exists
write_scope:
  - OpenEmotion/emotiond/*
  - OpenEmotion/tools/verify_mvp15_mainline_wiring.py
  - OpenEmotion/tests/mvp15/test_mainline_reference_demotion.py
  - reference docs
read_scope:
  - Tasks/active/mvp15_reflective_self_counterfactual/LEGACY_REFERENCE_REGISTER.md
dependencies:
  - T10_FORMAL_OWNER_PACKAGE
success_criteria:
  - legacy surfaces are explicitly labeled compatibility/reference
  - old verifier is updated to current authority assumptions
  - no second truth source remains in claims
verification_commands:
  - pytest -q OpenEmotion/tests/mvp15/test_mainline_reference_demotion.py
  - python OpenEmotion/tools/verify_mvp15_mainline_wiring.py --json
proof_required:
  - legacy demotion tests
rollback_point:
  - revert legacy demotion patch only
subagent_ready: true
```
