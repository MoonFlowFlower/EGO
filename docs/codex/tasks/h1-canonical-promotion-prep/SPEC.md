# H1 Canonical Promotion Prep - SPEC

## Goal

把 `Trial-2` 已关闭的 bounded 研究结果：

- `H1 counterfactual low-success guard = current bounded active public driver`

翻译成一个 **canonical proto_self kernel** 可接受的、**shadow-only / flag-guarded / rollback-safe** 的 promotion prep 方案。

这次任务不实现 patch，只回答：

- H1 能否用现有 canonical kernel surfaces 小改表达
- 若能，最小 shadow-only canonical patch 应该长什么样
- EgoCore 最小桥接、feature flag、rollback、E4 采样如何设计

## Hard constraints

- `Trial-1` / `Trial-2` 已关闭，只能作为 evidence source
- 不得把 `trial1_shadow.py` 或 Trial-2 artifact 当成新的 authority implementation
- 不得创建 parallel proto-self engine
- 不改 scorer ontology
- 不升级 repo-level state
- 不宣称 runtime efficacy
- 任何 canonical proto_self 改动都必须：
  - shadow-only
  - feature-flagged
  - rollback-safe

## Decision rule

- 若 H1 **不能**用现有 canonical kernel surface 的小改表达：
  - 停止
  - recommendation = `canonical-contract-stabilization first`
- 若 H1 **能**用现有 canonical kernel surface 的小改表达：
  - 输出 mapping / patch / flag / bridge / E4 plan
  - 但仍不实现

## Working hypothesis

- 当前初步判断：
  - `H1` 可以被表达为 canonical proto_self 的小改
- 原因：
  - `SelfModel.counterfactual_success_by_action` 已存在
  - `policy_hint.ask_preferred` 与 `policy_hint.shadow_counterfactual_guard` 已存在
  - `response_tendency.ask_needed` 已存在
  - `confidence_meta` 与 `trace_payload` 已是可扩的 shadow telemetry surface

## Deliverables

1. `H1_TO_CANONICAL_MAPPING_SPEC.md`
2. `CANONICAL_PATCH_PLAN.md`
3. `FEATURE_FLAG_ROLLBACK_PLAN.md`
4. `EGOCORE_FRONTEND_BRIDGE_PLAN.md`
5. `E4_SAMPLE_COLLECTION_PLAN.md`

## Acceptance criteria

- [ ] 明确回答 H1 是否需要 `canonical-contract-stabilization first`
- [ ] 明确写出 H1 到 canonical proto_self surface 的字段映射
- [ ] 明确写出 patch 只能是 shadow-only 的原因与边界
- [ ] 明确写出 EgoCore 最小桥接不改变 host authority 的路径
- [ ] 明确写出 E4 sample collection 只收证、不报 efficacy
- [ ] 全程不触 repo-level state

## Disallowed premature claims

- `H1 已 canonicalized`
- `H1 已接入 runtime 生效`
- `当前系统已证明 H1 在 real-channel 成立`
- `repo-level state 应升级`

## Authority refs

- `docs/codex/tasks/identify-public-causal-driver-for-mvs-trial-2/STATUS.md`
- `artifacts/self_awareness_research/TRIAL2_PUBLIC_DRIVER_DECISION_CURRENT.json`
- `OpenEmotion/openemotion/proto_self/kernel.py`
- `OpenEmotion/openemotion/proto_self/state.py`
- `OpenEmotion/openemotion/proto_self/schemas.py`
- `OpenEmotion/openemotion/proto_self/self_model.py`
- `OpenEmotion/openemotion/proto_self/reducers.py`
- `EgoCore/app/openemotion_adapter/proto_self_adapter.py`
- `EgoCore/app/runtime_v2/proto_self_runtime.py`
- `EgoCore/app/runtime_v2/decision_engine.py`
- `scripts/runtime_mainline_observation_common.py`
