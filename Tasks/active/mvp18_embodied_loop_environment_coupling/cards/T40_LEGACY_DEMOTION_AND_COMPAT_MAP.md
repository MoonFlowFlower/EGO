# T40_LEGACY_DEMOTION_AND_COMPAT_MAP

```yaml
task_id: T40_LEGACY_DEMOTION_AND_COMPAT_MAP
parent_authority: Tasks/MVS_task_plan.md
phase: WP13
goal: Demote historical consequence/intervention surfaces to reference-only or input-only.
non_goals:
  - Delete legacy files
  - Use legacy surfaces as current formal proof
write_scope:
  - OpenEmotion/emotiond/*
  - OpenEmotion/tools/verify_mvp18_mainline_wiring.py
  - OpenEmotion/tests/mvp18/test_mainline_reference_demotion.py
  - Tasks/active/mvp18_embodied_loop_environment_coupling/LEGACY_REFERENCE_REGISTER.md
read_scope:
  - Tasks/MVP18_task_plan.md
  - OpenEmotion/emotiond/consequence.py
  - OpenEmotion/emotiond/science/interventions.py
dependencies:
  - T10_FORMAL_OWNER_PACKAGE
success_criteria:
  - legacy embodied surfaces are explicitly demoted
  - no-second-truth verifier exists
verification_commands:
  - pytest -q OpenEmotion/tests/mvp18/test_mainline_reference_demotion.py
proof_required:
  - demotion tests and verifier
rollback_point:
  - revert embodied legacy demotion only
subagent_ready: true
```
