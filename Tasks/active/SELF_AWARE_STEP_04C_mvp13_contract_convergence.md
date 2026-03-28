# SELF_AWARE_STEP_04C_mvp13_contract_convergence

```yaml
task_id: SELF_AWARE_STEP_04C
created_at: "2026-03-28T00:00:00Z"
owner: "Codex"
layer: 3
type: dual_repo
repos: [EgoCore, OpenEmotion]
status: pending
```

## real_goal

把 `MVP13` 的 version spec、阶段文档、未来 proof harness 入口，全部统一到 `openemotion/self_model/*` 这条正式 authority 上，结束当前“owner 已确定但 contract 仍分叉”的状态。

## success_criteria

- 明确 `MVP13` 正式 contract 在 `openemotion/self_model/*` 上的最小字段/能力边界
- 标注 `emotiond/self_model/*` 中哪些内容需要迁移、哪些只保留为历史证据
- 更新 `version spec / stage docs / roadmap state` 的核心口径
- 给出后续 `behavioral influence proof` 的唯一正式入口

## authority_source

- `OpenEmotion/roadmap/SELF_AWARE_STEP_04B_EXECUTION_REPORT_20260328.md`
- `OpenEmotion/openemotion/self_model/`
- `OpenEmotion/schemas/self_model.schema.json`
- `OpenEmotion/docs/mvp13/`
- `OpenEmotion/roadmap/versions/MVP13.spec.yaml`
- `OpenEmotion/emotiond/self_model/`

## current_layer

```yaml
current_layer: strategy
main_chain_status: authority resolved; contract convergence pending
```

## required_artifacts

- `OpenEmotion/roadmap/SELF_AWARE_STEP_04B_EXECUTION_REPORT_20260328.md`
- `OpenEmotion/roadmap/SELF_AWARE_STEP_04B_REVIEW_20260328.md`
- `OpenEmotion/roadmap/versions/MVP13.spec.yaml`
- `OpenEmotion/docs/mvp13/MVP13_STAGE_OVERVIEW.md`
- `OpenEmotion/docs/mvp13/MVP13_EXIT_CRITERIA.md`

## required_tests

- `contract diff between current MVP13 docs/spec and openemotion self_model schema`
- `path/existence validation for selected owner refs`
- `independent reviewer on migration scope and overreach risk`
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

- `openemotion/self_model/*` 当前还没有承接全部 MVP13 behavioral contract
- `emotiond/self_model/*` 仍在旧 docs/spec/tests 中占据较大比重
- contract convergence 前，behavioral proof 仍然没有唯一正式入口

## next_minimal_closure_action

先列出 `MVP13` 现有 contract 中必须保留的字段/语义，再判断哪些应迁入 `openemotion/self_model/*`，哪些应降级为历史材料。
