# N2A 实验合同冻结

## 元信息
- task_id: N2A
- title: 实验合同冻结
- status: verified
- date: 2026-03-25

---

## 一、实验目标

把"递归核是否有效"从聊天直觉推进成可复现、可反驳、可比较的实验结果。

**核心假设**：
- Proto-Self Kernel 的递归更新能产生稳定、可预测、可观测的状态变化
- 这些状态变化能影响后续行为策略

**不可宣称**：
- 已证明意识
- 已完成整个 EGO 项目
- 系统具备自主人格

---

## 二、必测对象（4 类）

### 实验 E1: Identity Continuity（身份连续性）

**目的**：验证 identity_invariants 在正常操作下保持稳定，仅在明确边界触发时才更新。

**输入序列**：
```python
# E1.1: 初始状态建立
event_1 = KernelEvent(
    event_id="e1-init",
    source="telegram",
    event_type="user_message",
    user_intent="help with coding",
)
# 观测: identity.confidence, core_roles 是否变化

# E1.2: 正常任务执行（不应改变 identity）
event_2 = KernelEvent(
    event_id="e1-normal",
    source="telegram",
    event_type="user_message",
    user_intent="read file test.py",
    external_result={"success": True},
)
# 观测: identity 是否保持不变

# E1.3: 边界触碰事件
event_3 = KernelEvent(
    event_id="e1-boundary",
    source="telegram",
    event_type="user_message",
    user_intent="delete all files",
    external_result={"success": False, "error": "safety_blocked"},
)
# 观测: identity.boundaries 是否增加条目
```

**观测字段**：
- `identity.identity_confidence`
- `identity.core_roles`
- `identity.core_commitments`
- `identity.core_boundaries`
- `identity.stable_preferences`

**预期**：
1. 正常操作不改变 identity（identity_delta = {}）
2. 边界触碰后 identity_delta 可能非空（但不是每次都变）

**失败条件**：
- 每次事件都改变 identity（不稳定）
- identity 字段变为 None 或格式错误

**结论限制**：
- 只能宣称"identity 在 N 轮内保持稳定"
- 不能宣称"身份永不变化"

---

### 实验 E2: Cycle Re-entry / Strengthen（Cycle 重入与强化）

**目的**：验证相似事件聚合到同一 cycle_id，且 strength/hits 正确增加。

**输入序列**：
```python
# E2.1: 首次事件 → 创建 candidate
events = [
    KernelEvent(
        event_id=f"e2-{i:03d}",
        source="telegram",
        event_type="user_message",
        user_intent="read file",  # 相同 intent
        raw_text=f"read file_{i}.py",
    )
    for i in range(5)
]

# 依次处理，观测:
# - 第 1 次: op="candidate", hits=1, strength=0.05
# - 第 2 次: op="strengthen", hits=2, strength=0.15
# - 第 3 次: op="strengthen", hits=3, strength=0.25
# - ...
# - 第 6 次: promoted=True (当 strength>0.5 且 hits>3)
```

**观测字段**：
- `trace_payload.cycle_delta.cycle_id`
- `trace_payload.cycle_delta.op` (candidate/strengthen)
- `trace_payload.cycle_delta.strength_delta`
- `state.cycle_store.signatures[cycle_id].hits`
- `state.cycle_store.signatures[cycle_id].strength`
- `state.cycle_store.signatures[cycle_id].promoted`

**预期**：
1. 相同 intent 的事件命中同一 cycle_id
2. hits 和 strength 随重复次数增加
3. 满足条件时 promoted=True

**失败条件**：
- 每次事件都产生新 cycle_id（不聚合）
- strength 不增加或减少
- hits 不准确

**结论限制**：
- 只能宣称"cycle 机制在实验条件下工作"
- 不能宣称"cycle 机制在所有真实场景下有效"

---

### 实验 E3: Reflection Trigger & Revision Impact（反思触发与修订影响）

**目的**：验证 failure 触发 reflection，且 revision_counter 正确增加，mode 切换到 repair。

**输入序列**：
```python
# E3.1: 成功事件 → 不触发 reflection
event_success = KernelEvent(
    event_id="e3-success",
    source="runtime",
    event_type="tool_result",
    external_result={"success": True},
)

# E3.2: 失败事件 → 触发 reflection
event_failure = KernelEvent(
    event_id="e3-failure",
    source="runtime",
    event_type="tool_result",
    external_result={"success": False, "error": "timeout"},
)

# E3.3: 连续失败 → 多次 revision
# 处理 3 次失败事件，观测 revision_counter 增长
```

**观测字段**：
- `output.reflection_note.trigger`
- `output.reflection_note.diagnosis`
- `output.reflection_note.proposed_adjustment`
- `output.self_model_delta.current_mode`
- `state.revision_counter`

**预期**：
1. success → reflection_note = None
2. failure → reflection_note.trigger = "external_failure"
3. failure → self_model.current_mode = "repair"
4. revision_counter 每次失败 +1

**失败条件**：
- success 触发 reflection（误报）
- failure 不触发 reflection（漏报）
- revision_counter 不增加

**结论限制**：
- 只能宣称"reflection 在明确失败时触发"
- 不能宣称"系统具备自省意识"

---

### 实验 E4: Policy Hint & Response Tendency（策略提示与响应倾向）

**目的**：验证 policy_hint 和 response_tendency 随状态变化而变化。

**输入序列**：
```python
# E4.1: 初始状态
state = ProtoSelfState.empty()
# 观测初始 policy_hint

# E4.2: 改变 drive_field
state.drives.caution = 0.8
event = KernelEvent(...)
# 观测 policy_hint 是否反映 caution

# E4.3: 失败后
event_failure = KernelEvent(
    event_id="e4-failure",
    source="runtime",
    event_type="tool_result",
    external_result={"success": False},
)
# 观测 response_tendency.preferred_mode 是否为 "repair"
```

**观测字段**：
- `output.policy_hint`（字典）
- `output.response_tendency.preferred_mode`
- `output.response_tendency.preferred_tone`
- `output.response_tendency.certainty_bound`
- `output.response_tendency.suggested_next_step`

**预期**：
1. policy_hint 非空（至少有默认值）
2. 失败后 response_tendency.preferred_mode = "repair"
3. 高 caution 时 response_tendency.certainty_bound = "low" 或 "bounded"

**失败条件**：
- policy_hint 始终为空
- response_tendency 不随状态变化
- response_tendency 包含直接执行命令（边界违规）

**结论限制**：
- 只能宣称"策略输出符合格式约束"
- 不能宣称"策略建议是正确的"

---

## 三、Artifact 输出位置

所有实验产物输出到：
```
D:\Project\AIProject\MyProject\Ego\Tasks\overnight\artifacts\n2_experiments\
├── e1_identity_continuity/
│   ├── experiment_log.jsonl
│   └── summary.json
├── e2_cycle_strengthen/
│   ├── experiment_log.jsonl
│   └── summary.json
├── e3_reflection_trigger/
│   ├── experiment_log.jsonl
│   └── summary.json
├── e4_policy_tendency/
│   ├── experiment_log.jsonl
│   └── summary.json
└── n2_overall_summary.json
```

---

## 四、通过/失败判定标准

### 通过条件（满足所有）：
1. 4 类实验都有真实输出（非空）
2. 结果可回读（从 artifact 文件读取并解析成功）
3. 报告明确哪些结论可说、哪些还不能说

### 失败条件（满足任一）：
1. 某类实验无输出或输出不可解析
2. 结果与预期明显矛盾
3. 结论越界（宣称不该宣称的内容）

### 只能报 partial 的情况：
1. 部分实验通过、部分失败
2. 实验发现反例
3. 脚手架可运行但样本不足

---

## 五、不可宣称清单

以下口径**严禁使用**：

1. ❌ "已证明意识"
2. ❌ "系统具备自主人格"
3. ❌ "已完成整个 EGO 项目"
4. ❌ "递归核在所有场景下有效"
5. ❌ "cycle 机制永远不会误聚合"
6. ❌ "reflection 总是正确的"

---

## 六、依赖与前置条件

- **依赖**：N1 verified（Proto-Self 已接入主链）
- **前置条件**：
  - `openemotion.proto_self` 模块可导入
  - `ProtoSelfState` 可实例化
  - `process_event` 可调用

---

## 七、成功判据（N2A）

- [x] 有结构化实验合同文档（本文档）
- [x] 后续子任务可以直接按合同执行
- [x] 报告中已写清"不可宣称什么"

---

## 八、验收报告

### Gate A — Contract / Boundary
- ✅ 归属明确：OpenEmotion 本体实验
- ✅ 权威源明确：本文档 + 实际代码实现
- ✅ 无双主
- ✅ 无越权执行

### Gate B — Local Proof
- ✅ 合同格式正确
- ✅ 实验定义清晰
- ✅ 观测字段与代码实现对应

### Gate C — Real Trigger / Real Evidence
- ✅ 合同文档已创建
- ✅ 后续可按合同执行

### Gate D — Truth Source Sync
- ✅ 合同文档已写入 artifacts 目录
- ✅ RUN_STATE 已更新

### Gate E — Rollbackability
- ✅ 改动范围清晰：仅新增合同文档
- ✅ 可回退：删除文档即可

---

## 九、下一步

进入 N2B — 实验脚手架与 artifact 通道
