# SELF_AWARE_STEP_04F_behavioral_influence_formal_proof

```yaml
task_id: SELF_AWARE_STEP_04F
created_at: "2026-03-29T03:15:00Z"
owner: "Codex"
layer: 3
type: dual_repo
repos: [EgoCore, OpenEmotion]
status: published
```

## real_goal

在已建立的 formal-owner-backed decision surface 上，完成一条受治理、可 replay、可比较的 `behavioral influence` formal proof，证明 `openemotion/self_model/*` 的受控字段干预会改变至少一个真实下游决策点。

## success_criteria

- 存在一条唯一正式 proof path，消费 `openemotion/self_model/*` 的 authoritative 字段
- paired intervention/control 样本能稳定改变同一主链 decision point
- proof 不依赖 legacy-only `emotiond/self_model/*` 字段
- governor / sandbox / replay discipline 保持成立

## authority_source

- `OpenEmotion/roadmap/SELF_AWARE_STEP_04E_EXECUTION_REPORT_20260329.md`
- `OpenEmotion/openemotion/self_model/model.py`
- `OpenEmotion/emotiond/self_model_adapter.py`
- `OpenEmotion/emotiond/core.py`
- `OpenEmotion/docs/mvp13/MVP13_EXIT_CRITERIA.md`
- `OpenEmotion/roadmap/versions/MVP13.spec.yaml`

## current_layer

```yaml
current_layer: verification
main_chain_status: owner-backed behavioral influence established on the emotiond decision mainline; stage pass still not claimed
```

## required_artifacts

- `OpenEmotion/roadmap/SELF_AWARE_STEP_04E_EXECUTION_REPORT_20260329.md`
- `OpenEmotion/roadmap/SELF_AWARE_STEP_04E_REVIEW_20260329.md`
- `OpenEmotion/roadmap/SELF_AWARE_STEP_04F_REVIEW_20260329.md`
- `OpenEmotion/docs/mvp13/SELF_MODEL_STATE_SCHEMA.md`

## required_tests

- `pytest -q OpenEmotion/tests/mvp13/test_owner_backed_decision_surface.py`
- `paired intervention/control harness with real mainline call path`
- `independent reviewer on authority and overreach risk`
- `git diff --check`

## workflow_requirements

```yaml
full_spec_required: true
self_reviewer_required: true
independent_reviewer_required: true
verifier_required: true
publisher_required: true
```

## promotion_blockers

- long-stage / Stage 4 admission 仍未建立
- MVP15 formal proof 仍未完成，`OE_MVP:16` 继续 blocked

## next_minimal_closure_action

本步已完成并发布；下一步切到 `SELF_AWARE_STEP_05_mvp14_formal_proof.md`。
