# CLOSURE_TRACE_SCHEMA_DIFF

## 变更目的

为了让 `cycle identity` 对闭环敏感，而不是只对输入桶敏感，本轮给 trace 增加了 closure-level 字段。

---

## 升级前

`proto_self.trace.v1` 重点字段：

- `event_id`
- `perceived`
- `appraisal_delta`
- `self_model_delta`
- `cycle_delta`
- `identity_delta`
- `reflection_trigger`
- `policy_hint`
- `timestamp`

---

## 升级后

新增顶层字段：

- `closure_signature`
- `closure_family_id`
- `action_signature`
- `outcome_signature`
- `closure_consistency_score`
- `order_invariance_candidate`

同时 `cycle_delta` 内也新增：

- `closure_signature`
- `closure_family_id`
- `action_signature`
- `outcome_signature`
- `mode_signature`
- `closure_consistency_score`
- `repair_closure`
- `order_invariance_candidate`

---

## 语义说明

### `closure_signature`

当前正式 `cycle_id` 的等价表达，表示当前 closure-sensitive identity。

### `closure_family_id`

把同类 closure 聚成一个 family。

当前实现中：

- 同一 `psi_bucket + action_signature` 会归入同一 family
- success/failure 可以 family 相同但 `cycle_id` 不同

### `action_signature`

稳定离散化后的动作族，不使用原始自由文本。

当前最小实现示例：

- `tool:shell`
- `tool:file`
- `ingress:user_request`
- `system:event`

### `outcome_signature`

当前支持：

- `success`
- `failure`
- `blocked`
- `partial`
- `unknown`

### `closure_consistency_score`

用于 promotion gating 的最小一致性指标。

当前考虑：

- 同 family 下相同 outcome 的支持度
- 同 family 下相同 `phi_signature` 的支持度
- repair closure 的额外抬升

### `order_invariance_candidate`

当前不是正式 invariant 证明，只是最小候选字段。

它基于最近若干前驱事件 bucket 的排序后签名，用于识别“微顺序不同但 closure 等价”的候选样本。

---

## replay 兼容性

本轮保持不退化：

- 旧字段全部保留
- 新字段只是追加
- `ProtoSelfTracePayload.from_dict()` 对新旧 payload 都兼容

---

## 状态格式影响

`CycleSignature` 新增持久字段：

- `closure_signature`
- `closure_family_id`
- `action_signature`
- `outcome_signature`
- `mode_signature`
- `closure_consistency_score`

兼容性策略：

- `from_dict()` 对旧 state 使用默认值回填
- 不要求强制迁移脚本
- 老镜像可直接加载
