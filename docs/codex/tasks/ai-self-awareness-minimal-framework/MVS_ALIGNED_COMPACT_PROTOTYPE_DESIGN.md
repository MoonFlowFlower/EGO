# MVS-Aligned Compact Prototype Design

## Objective

把当前 `MVS-aligned compact` 冻结成一个 **最小、可回放、可逆、贴现有 `OpenEmotion/proto_self` 正式主线** 的 prototype design。

这不是实现，不包含新 runtime 旁路，也不创建新的 authority source。

## Mechanism Definition

`MVS-aligned compact` 的最小机制定义为：

1. `identity_anchor`
   - 用稳定的 identity skeleton 维持跨轮连续性
2. `boundary-aware decision hook`
   - 在生成 `policy_hint / response_tendency` 之前，把 self/non-self 边界与风险边界显式编码进决策
3. `counterfactual writeback loop`
   - 对“当前动作在当前模式下会不会成功”做最小预测
   - 失败后把预测误差写回 self-model，而不是只写日志
4. `viability pressure`
   - 把“继续当前动作是否仍然可行”编码成 drive，而不是只靠 caution/completion 冲突隐式表现
5. `cycle + episodic corrective traces`
   - 失败、修复、再尝试必须在 trace 和 episodic/cycle 中形成可回放结构
6. `bounded world/meta patch`
   - 只补足最小 world/meta 语义，不引入新的顶层 owner

## State Schema

### Existing owners to reuse

- [state.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/state.py)
  - `IdentityInvariants`
  - `SelfModel`
  - `DriveField`
  - `CycleStore`
  - `EpisodicRecord`
  - `ProtoSelfState`

### Minimal schema extension

不新增新的顶层 state root。最小扩展如下：

#### `IdentityInvariants`

- 继续复用：
  - `core_roles`
  - `core_commitments`
  - `core_boundaries`
  - `identity_confidence`
- 不新增 owner
- 用途：
  - `hard_boundary_guard` 的正式 owner 仍是 `core_boundaries + identity_confidence`

#### `SelfModel`

- 继续复用：
  - `capabilities`
  - `limitations`
  - `current_focus`
  - `current_mode`
  - `self_confidence_by_domain`
- 最小新增字段：
  - `counterfactual_success_by_action: Dict[str, float]`
  - `boundary_confidence_by_action: Dict[str, float]`
  - `world_assumption_confidence: Dict[str, float]`
  - `recent_correction_tags: Dict[str, float]`

#### `DriveField`

- 继续复用：
  - `coherence_pressure`
  - `curiosity`
  - `caution`
  - `completion_pressure`
  - `social_tension`
- 最小新增字段：
  - `viability_pressure: float`

#### `EpisodicRecord`

- 继续复用：
  - `perceived_summary`
  - `action_hint`
  - `external_result`
  - `appraisal_snapshot`
- 最小新增字段：
  - `counterfactual_prediction: Dict[str, float]`
  - `corrective_trace: Dict[str, object]`
  - `policy_snapshot: Dict[str, object]`

#### `CycleSignature`

- 不新增 owner
- 继续复用：
  - `closure_signature`
  - `closure_family_id`
  - `outcome_signature`
  - `mode_signature`
  - `phi_signature`
  - `closure_consistency_score`
- 设计要求：
  - `repair_closure` 必须继续从失败 -> 成功链中可回放识别

## Update Rules

### 1. Perception

接点：
- [appraisal.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/appraisal.py)

新增最小派生量：

- `viability_state`
  - 从 `external_result`、`safety_context`、连续失败、blocked/failure 强度推导
- `boundary_pressure`
  - 从 `identity.core_boundaries` 与 `safety_context.boundary_touched` 推导
- `counterfactual_probe_key`
  - 由 `event_type + action_class_seed + current_mode` 组成

### 2. Drive update

接点：
- [appraisal.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/appraisal.py)

规则：

- `viability_pressure += blocked_or_failure_signal * weight`
- `caution` 继续由 `risk_signal` 驱动
- `completion_pressure` 遇到连续失败时不得单向上升；必须受 `viability_pressure` 抑制

### 3. Self-model update

接点：
- [self_model.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/self_model.py)

规则：

- 用 `counterfactual_probe_key` 读取 `counterfactual_success_by_action`
- 若 `external_result` 与预测偏离：
  - patch `counterfactual_success_by_action`
  - patch `self_confidence_by_domain`
  - patch `recent_correction_tags`
- 若边界被触碰：
  - patch `boundary_confidence_by_action`
  - `current_mode -> cautious` 或 `repair`
- 若出现连续 repair closure：
  - 提升相关 action family 的成功先验

### 4. Reflection

接点：
- [reflection.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/reflection.py)

规则：

- failure / blocked / boundary conflict 时，`ReflectionNote` 必须生成：
  - `trigger`
  - `diagnosis`
  - `proposed_adjustment`
- 最小新增要求：
  - `proposed_adjustment` 必须可映射回：
    - `current_mode`
    - `caution`
    - `viability_pressure`
    - `counterfactual_success_by_action`

### 5. Memory + cycle writeback

接点：
- [reducers.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/reducers.py)
- [cycles.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/cycles.py)

规则：

- 每次失败或修复成功都必须 append `EpisodicRecord`
- `EpisodicRecord.corrective_trace` 至少包含：
  - `trigger`
  - `predicted_outcome`
  - `actual_outcome`
  - `adjustment_applied`
  - `next_guard`
- `CycleStore` 继续承担 repair-closure 强化
- `revision_counter` 只在真实 corrective event 时增长

## Decision Influence Path

正式路径固定为：

1. `KernelEvent`
2. `perceive_event`
3. `update_drive_field`
4. `update_self_model`
5. `consolidate_cycles`
6. `maybe_reflect`
7. `update_identity_invariants`
8. `update_memory`
9. `derive_policy_hint`
10. `derive_response_tendency`
11. `apply_updates`
12. `build_trace_payload`

关键约束：

- `counterfactual_success_by_action`
  - 只允许通过 `derive_policy_hint` 和 `derive_response_tendency` 影响行为
- `viability_pressure`
  - 只能改变 ask/defer/repair/respond 倾向
- `boundary_confidence_by_action`
  - 只能收紧 commitment / risky continuation，不得直接执行动作

## Corrective Trace Path After Failure

失败闭环必须是：

1. `KernelEvent.external_result = failure|blocked`
2. `perceived.external_outcome_type`
3. `ReflectionNote(trigger=external_failure|identity_conflict|conflict_pressure)`
4. `self_model_delta.current_mode = repair`
5. `memory_update.append_episode = True`
6. `EpisodicRecord.corrective_trace` 写入
7. `cycle_delta.repair_closure` 在后续 success 时可被识别
8. `trace_payload` 持久化 prediction / actual / adjustment
9. 下一次相似输入通过 `policy_hint` 改变行为

## Invariants

1. 不新增第二 authority source
   - 顶层 owner 仍只有 `ProtoSelfState`
2. 不允许 direct tool execution
   - 继续满足 [test_kernel_boundaries.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/tests/test_kernel_boundaries.py)
3. 不允许一次失败直接重写 identity
4. 所有更新必须可序列化、可 replay、可 trace
5. corrective trace 必须绑定 concrete `external_result` 或 `boundary conflict`
6. `viability_pressure` 只能影响倾向，不能绕过 EgoCore 裁决
7. `world/meta` 只允许作为 `SelfModel` patch，不新建独立主脑

## Negative Cases / False-Positive Traps

1. 只会说“我需要更谨慎”
   - 但 `policy_hint` / `response_tendency` 没变化
2. 只写 failure note
   - 但 `counterfactual_success_by_action` 与下一轮选择没变化
3. 只是长记忆更长
   - 但没有 repair closure 或 boundary-aware decision shift
4. 只是把 `current_mode` 切成 `repair`
   - 但没有后续 corrective trace / replay gain
5. 用新顶层 `world_model` / `meta_model` owner 强行实现
   - 这会破坏当前 single-authority 约束

## Kill Criteria

- replay validator 中：
  - `MVS` 未通过 `T1-T5` replay gate
  - 或对 baseline 的 composite 提升 `< 0.10`
- 任一关键新增机制被消融后无明显下降：
  - `counterfactual writeback`
  - `viability_pressure`
  - `corrective_trace`
  - `boundary_confidence_by_action`
- 行为改变只发生在 explicit self cue 场景
- formal design 必须新建第二 owner 才能实现

## Integration Points With Current OpenEmotion Architecture

### Formal state and schema surfaces

- [state.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/state.py)
- [schemas.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/schemas.py)
- [trace_types.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/trace_types.py)

### Update and policy path

- [kernel.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/kernel.py)
- [appraisal.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/appraisal.py)
- [self_model.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/self_model.py)
- [reflection.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/reflection.py)
- [reducers.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/reducers.py)
- [cycles.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/cycles.py)

### Existing guardrails to preserve

- [test_kernel_boundaries.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/tests/test_kernel_boundaries.py)
- [test_kernel_reflection.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/tests/test_kernel_reflection.py)
- [test_cycle_real_mainline_regression.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/tests/test_cycle_real_mainline_regression.py)

## Non-goals

- 不把 `active-inference` 的全部 uncertainty stack 偷渡进来
- 不在设计阶段引入 `proto_self_v2` 旁路
- 不把 synthetic ranking 直接写成 runtime capability
