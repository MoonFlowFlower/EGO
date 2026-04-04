# T10_FORMAL_OWNER_PACKAGE

```yaml
task_id: T10_FORMAL_OWNER_PACKAGE
parent_authority: Tasks/MVS_task_plan.md
phase: WP12
goal: Create the OpenEmotion social_self formal owner package under openemotion/.
non_goals:
  - Implement live social behavior
  - Keep historical materials as formal owner
write_scope:
  - OpenEmotion/openemotion/social_self/*
  - OpenEmotion/tests/mvp17/test_social_owner_infra.py
read_scope:
  - Tasks/MVP17_task_plan.md
  - OpenEmotion/roadmap/SELF_AWARE_AI_ROADMAP.md
  - OpenEmotion/roadmap/VersionRoadmap.md
  - OpenEmotion/docs/archive/mvp9/MVP9_SPEC.md
dependencies:
  - T00_AUTHORITY_FREEZE
success_criteria:
  - social owner package exists under openemotion/
  - owner state covers relation memory, trust, commitment, repair, boundary, and governance ledger
  - owner schema/state are replayable and audit-friendly
verification_commands:
  - pytest -q OpenEmotion/tests/mvp17/test_social_owner_infra.py
proof_required:
  - owner package tests
rollback_point:
  - revert social_self owner package only
subagent_ready: true
```
