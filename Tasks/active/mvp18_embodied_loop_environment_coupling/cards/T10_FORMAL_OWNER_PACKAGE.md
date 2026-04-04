# T10_FORMAL_OWNER_PACKAGE

```yaml
task_id: T10_FORMAL_OWNER_PACKAGE
parent_authority: Tasks/MVS_task_plan.md
phase: WP13
goal: Create the OpenEmotion embodied_self formal owner package under openemotion/.
non_goals:
  - Implement live embodied behavior
  - Keep historical materials as formal owner
write_scope:
  - OpenEmotion/openemotion/embodied_self/*
  - OpenEmotion/tests/mvp18/test_embodied_owner_infra.py
read_scope:
  - Tasks/MVP18_task_plan.md
  - OpenEmotion/roadmap/VersionRoadmap.md
  - OpenEmotion/emotiond/consequence.py
  - OpenEmotion/emotiond/science/interventions.py
dependencies:
  - T00_AUTHORITY_FREEZE
success_criteria:
  - embodied owner package exists under openemotion/
  - owner state covers embodied, environment coupling, resource pressure, boundary pressure, and consequence memory
  - owner schema/state are replayable and audit-friendly
verification_commands:
  - pytest -q OpenEmotion/tests/mvp18/test_embodied_owner_infra.py
proof_required:
  - owner package tests
rollback_point:
  - revert embodied_self owner package only
subagent_ready: true
```
