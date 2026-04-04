# T40_LEGACY_DEMOTION_AND_COMPAT_MAP

```yaml
task_id: T40_LEGACY_DEMOTION_AND_COMPAT_MAP
parent_authority: Tasks/MVS_task_plan.md
phase: WP11
goal: Demote old developmental and MVP16 legacy surfaces to reference-only or input-only and publish a compat map.
non_goals:
  - Delete legacy developmental code
write_scope:
  - OpenEmotion/emotiond/*
  - OpenEmotion/tools/verify_mvp16_mainline_wiring.py
  - OpenEmotion/tests/mvp16/test_mainline_reference_demotion.py
  - Tasks/active/mvp16_host_governed_developmental_continuity/LEGACY_REFERENCE_REGISTER.md
read_scope:
  - Tasks/MVP16_task_plan.md
  - OpenEmotion/emotiond/developmental/*
  - OpenEmotion/emotiond/developmental_core/*
  - OpenEmotion/tools/mvp16_*
dependencies:
  - T10_FORMAL_OWNER_PACKAGE
success_criteria:
  - legacy developmental owner paths are explicitly demoted
  - wiring verifier checks current runtime consumer vs legacy reference-only surfaces
  - no second-truth owner claim remains
verification_commands:
  - pytest -q OpenEmotion/tests/mvp16/test_mainline_reference_demotion.py
  - python3 OpenEmotion/tools/verify_mvp16_mainline_wiring.py --json
proof_required:
  - demotion / verifier proof
rollback_point:
  - revert legacy demotion and compat-map changes only
subagent_ready: true
```
