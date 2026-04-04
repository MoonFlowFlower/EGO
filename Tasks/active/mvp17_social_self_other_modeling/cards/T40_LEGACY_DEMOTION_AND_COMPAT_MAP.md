# T40_LEGACY_DEMOTION_AND_COMPAT_MAP

```yaml
task_id: T40_LEGACY_DEMOTION_AND_COMPAT_MAP
parent_authority: Tasks/MVS_task_plan.md
phase: WP12
goal: Mark historical social / relation materials as reference-only or input-only and add verifier coverage for no-second-truth rules.
non_goals:
  - Implement MVP17 owner/runtime code
write_scope:
  - OpenEmotion/tools/*
  - OpenEmotion/tests/mvp17/test_mainline_reference_demotion.py
  - EgoCore/app/response/*
  - EgoCore/app/handlers/*
  - EgoCore/app/runtime/*
  - EgoCore/app/bridges/*
  - OpenEmotion/emotiond/*
  - reference docs touching WP12 legacy classification
read_scope:
  - Tasks/MVP17_task_plan.md
  - Tasks/active/mvp17_social_self_other_modeling/LEGACY_REFERENCE_REGISTER.md
  - OpenEmotion/roadmap/SELF_AWARE_AI_ROADMAP.md
  - OpenEmotion/docs/archive/mvp9/MVP9_SPEC.md
dependencies:
  - T10_FORMAL_OWNER_PACKAGE
success_criteria:
  - historical social materials are labeled reference-only or input-only
  - existing relationship / repair code surfaces are explicitly registered
  - no current runtime path claims them as formal owner
verification_commands:
  - pytest -q OpenEmotion/tests/mvp17/test_mainline_reference_demotion.py
proof_required:
  - reference demotion verifier
rollback_point:
  - revert legacy-demotion docs and verifier only
subagent_ready: true
```
