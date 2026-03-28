# SELF_AWARE_STEP_02_version_specs

```yaml
task_id: SELF_AWARE_STEP_02
created_at: "2026-03-28T00:00:00Z"
owner: "Codex"
layer: 3
type: dual_repo
repos: [EgoCore, OpenEmotion]
status: published
```

## real_goal

为 `MVP12-16` 补齐正式 version spec，把已有 overview、exit criteria、tests、artifacts 编译成可执行版本 contract。

## success_criteria

- `MVP12.spec.yaml` 至 `MVP16.spec.yaml` 全部存在
- 每版至少包含 `goal / in_scope / out_of_scope / required_artifacts / required_tests / promotion_criteria / stop_conditions`
- 路线图入口能导航到这些 spec

## authority_source

- `OpenEmotion/roadmap/versions/MVP11_5.spec.yaml`
- `OpenEmotion/docs/archive/mvp12/`
- `OpenEmotion/docs/mvp13/`
- `OpenEmotion/docs/mvp14/`
- `OpenEmotion/docs/mvp15/`
- `OpenEmotion/docs/mvp16/`

## current_layer

```yaml
current_layer: representation
main_chain_status: 构件
```

## required_artifacts

- `OpenEmotion/roadmap/versions/MVP12.spec.yaml`
- `OpenEmotion/roadmap/versions/MVP13.spec.yaml`
- `OpenEmotion/roadmap/versions/MVP14.spec.yaml`
- `OpenEmotion/roadmap/versions/MVP15.spec.yaml`
- `OpenEmotion/roadmap/versions/MVP16.spec.yaml`

## required_tests

- 校验每版 spec 引用的 docs/tests/artifacts 路径存在或被明确声明为未来 required_artifacts
- 校验 `ROADMAP_INDEX` 已接入新 spec

## workflow_requirements

```yaml
full_spec_required: true
self_reviewer_required: true
independent_reviewer_required: true
verifier_required: true
publisher_required: true
```

## promotion_blockers

- 仍未完成阶段 formal proof
- `MVP16` 仍处于 `blocked`

## next_minimal_closure_action

执行 `SELF_AWARE_STEP_03_mvp12_formal_proof.md`，并在下一轮真实任务试运行中强制走 `Independent Reviewer -> Verifier`。
