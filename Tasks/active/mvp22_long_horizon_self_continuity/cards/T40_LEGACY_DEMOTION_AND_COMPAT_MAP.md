# T40_LEGACY_DEMOTION_AND_COMPAT_MAP

```yaml
task_id: T40_LEGACY_DEMOTION_AND_COMPAT_MAP
parent_authority: Tasks/MVS_task_plan.md
phase: WP17
goal: Demote historical continuity, restart, and roadmap materials to reference-only without creating a second truth source.
non_goals:
  - New runtime functionality
  - Closeout claims
write_scope:
  - Tasks/active/mvp22_long_horizon_self_continuity/*
  - OpenEmotion/tools/verify_mvp22_mainline_wiring.py
  - OpenEmotion/tests/mvp22/test_mvp22_mainline_reference_demotion.py
dependencies:
  - T00_AUTHORITY_FREEZE
success_criteria:
  - continuity-related legacy surfaces are explicitly registered as reference-only to WP17 semantics
  - no-second-truth verifier exists
verification_commands:
  - pytest -q OpenEmotion/tests/mvp22/test_mvp22_mainline_reference_demotion.py
  - python3 OpenEmotion/tools/verify_mvp22_mainline_wiring.py --json
rollback_point:
  - revert continuity demotion docs and verifier only
```
