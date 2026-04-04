# WP12 / MVP17 Legacy Reference Register

## Purpose

登记 `WP12` 启动前仓内已有的 social / relation / trust / commitment / repair 相关材料。它们可以作为参考输入、迁移线索或历史对照，但不能直接充当新的 `WP12` authority、formal owner 或 formal proof。

## Technical Reference, Not Authority

以下文件可作为技术参考，但与 `Tasks/MVS_task_plan.md + Tasks/MVP17_task_plan.md` 冲突时，不拥有裁决权：

- `OpenEmotion/roadmap/SELF_AWARE_AI_ROADMAP.md`
- `OpenEmotion/roadmap/VersionRoadmap.md`
- `OpenEmotion/docs/archive/mvp9/MVP9_SPEC.md`
- `OpenEmotion/docs/SCENARIOS-self-awareness.md`

## Reference-only / Input-only Surfaces

当前仓库扫描结果中，没有已落地的 `WP12` 级正式 social owner 路径，但存在以下历史 social / relationship / repair surfaces：

- `EgoCore/app/response/relationship_context.py`
  - `input-only`
  - 会话内短期关系辅助，不是 `WP12` formal owner
- `EgoCore/app/handlers/social_chat_handler.py`
  - `reference-only`
  - 历史 handler / ingress 参考，不是当前正式 social mainline
- `EgoCore/app/runtime/repair_context_manager.py`
  - `input-only`
  - failure-repair context 辅助，不是 `WP12` repair semantics authority
- `EgoCore/app/bridges/openemotion_bridge.py`
  - `reference-only`
  - placeholder / historical bridge，不是当前 `WP12` formal path
- `OpenEmotion/emotiond/api.py`
  - `reference-only`
  - 历史 daemon API surface，不是 `WP12` current-mainline proof
- `OpenEmotion/emotiond/db.py`
  - `reference-only`
  - 历史 daemon persistence surface，不是 `WP12` formal owner store
- `OpenEmotion/emotiond/state.py`
  - `reference-only`
  - 历史 bond/trust state，不是 `WP12` formal owner
- `OpenEmotion/emotiond/models.py`
  - `reference-only`
  - 历史 emotiond request/response models，不是 `WP12` social contract
- `OpenEmotion/emotiond/other_minds.py`
  - `reference-only`
  - 历史 social inference baseline，不是 `WP12` other-model authority
- `OpenEmotion/emotiond/persistence.py`
  - `reference-only`
  - 历史 persistence/repair pressure baseline，不是 `WP12` commitment/repair owner
- `OpenEmotion/emotiond/offline_rollouts.py`
  - `reference-only`
  - 历史 rollout baseline，不是 `WP12` current-mainline reasoning path
- `OpenEmotion/emotiond/memory_legacy.py`
  - `reference-only`
  - 历史 relationship memory helper，不是 `WP12` relation memory authority

历史材料中与 `trust / commitment / repair / other-modeling` 相关的内容，在 `WP12` 中最多只允许承担：

- migration reference
- scenario design reference
- causal validation baseline
- historical comparison

它们不得承担：

- formal owner state
- final social semantics
- current-mainline closeout proof

其中：

- `relationship_context.py` 只允许继续承担会话内短期表达辅助
- `social_chat_handler.py` 只允许继续承担历史 handler / ingress reference
- `repair_context_manager.py` 只允许继续承担 failure-repair context reference
- `openemotion_bridge.py` 只允许继续承担 placeholder / bridge reference
- `emotiond/db.py`、`state.py`、`api.py` 中的 relationships / trust / repair 结构只允许作为旧数据模型和 historical comparison，不得升级为 `WP12` formal owner
- `emotiond/models.py`、`other_minds.py`、`persistence.py`、`offline_rollouts.py`、`memory_legacy.py` 只允许作为迁移线索、baseline 或 historical comparison，不得作为 `WP12` social semantics authority

## Current Authority Reminder

- `Tasks/MVS_task_plan.md` 是顶层裁决
- `Tasks/MVP17_task_plan.md` 是 `WP12` phase-detail authority
- `Tasks/active/mvp17_social_self_other_modeling/*` 是当前执行包

All listed legacy docs above are `technical reference`, `reference-only`, or `input-only` for `WP12`.

Current formal owner reminder:

- `OpenEmotion/openemotion/social_self/*` is the only formal owner target
- `runtime_v2 -> proto_self_runtime -> proto_self_adapter -> proto_self_v2` is the only planned current-mainline consumer path
