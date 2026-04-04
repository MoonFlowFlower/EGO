# T50_CAUSAL_VALIDATION

```yaml
task_id: T50_CAUSAL_VALIDATION
parent_authority: Tasks/MVS_task_plan.md
phase: WP12
goal: Prove that social proposals change bounded downstream tendency rather than just logging social text.
non_goals:
  - Claim live social maturity
write_scope:
  - OpenEmotion/tests/mvp17/*
  - OpenEmotion/tools/*
  - OpenEmotion/artifacts/mvp17/*
read_scope:
  - Tasks/MVP17_task_plan.md
  - OpenEmotion/openemotion/social_self/*
  - OpenEmotion/openemotion/proto_self_v2/*
dependencies:
  - T30_EGOCORE_RUNTIME_BRIDGE
success_criteria:
  - at least 3 paired intervention/control proofs pass
  - trust or commitment changes alter bounded downstream weighting
  - text-only change with no downstream shift fails
verification_commands:
  - pytest -q OpenEmotion/tests/mvp17/test_social_causal_formal_proof.py
proof_required:
  - causal validation report
rollback_point:
  - revert causal proof tooling only
subagent_ready: true
```
