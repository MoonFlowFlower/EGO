# T60_CAUSAL_VALIDATION

```yaml
task_id: T60_CAUSAL_VALIDATION
parent_authority: Tasks/MVS_task_plan.md
phase: WP10
goal: Prove bounded causal relevance of reflection/counterfactual proposals on the current runtime mainline.
non_goals:
  - Direct action takeover by reflection
write_scope:
  - OpenEmotion/tests/mvp15/*
  - OpenEmotion/tools/*
  - proof artifacts
read_scope:
  - OpenEmotion/roadmap/versions/MVP15.spec.yaml
  - OpenEmotion/docs/mvp15/MVP15_EXIT_CRITERIA.md
dependencies:
  - T30_PROTO_SELF_CONTRACT_INTEGRATION
  - T40_EGOCORE_RUNTIME_BRIDGE
  - T50_LEGACY_DEMOTION_AND_MIGRATION
success_criteria:
  - at least 3 paired intervention/control proofs pass
  - proposal discipline remains intact
  - differences are measurable and replayable
verification_commands:
  - pytest -q OpenEmotion/tests/mvp15 -k causal
proof_required:
  - paired proof artifacts
rollback_point:
  - revert causal validation patch only
subagent_ready: true
```
