# SELF_MODEL_OWNER_CONTRACT

## Formal Owner

- `OpenEmotion/openemotion/self_model/*`
- `OpenEmotion/schemas/self_model.schema.json`

## Owner Semantics

`WP8/MVP13` 的 self-model 是同一主体在正式 owner store 中的结构化自我模型，不是宿主镜像，也不是 `proto_self_v2` 内部自生状态。

## Phase 1 Authoritative Fields

- `schema_version`
- `identity_handle`
- `capabilities`
- `limitations`
- `active_goals`
- `standing_commitments`
- `tool_authority_boundary`
- `dependency_map`
- `confidence_by_domain`
- `known_unknowns`
- `created_at`
- `last_modified_at`
- `modification_audit_trail`

## Allowed Proof Levers

Phase 1 只允许使用 formal owner 已有字段做 proof：
- `active_goals`
- `standing_commitments`
- `confidence_by_domain`
- `capabilities`
- `limitations`

## Compatibility Semantics

`proto_self_v2.state.self_model` 在 `WP8 Phase 1` 中只表示：
- formal owner self-model 的 runtime-local projection
- 可用于内部 evaluation / candidate priors / continuity-aware reasoning
- 不可被解释为 formal owner state 本身

## Reference-Only Legacy Fields

以下字段仅为迁移参考，不进入 Phase 1 formal contract：
- `behavioral_tendencies`
- `active_tensions`
- `continuity_trace`
- `revision_history`
- `SelfModelManager`

## Hard Rules

- EgoCore 不拥有 self-model 语义解释权
- `proto_self_v2` 不拥有持久化 owner 身份
- 任何 behavioral influence proof 不得依赖 legacy-only 字段
