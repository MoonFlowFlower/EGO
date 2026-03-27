# CLOSURE_UPGRADE_REPORT

## 当前层级

本次变更是 **Proto-Self `cycle identity` 的本体升级**，目标是把当前实现从：

- `psi_bucket` 命中 + `hits/strength` 累计

升级到：

- 对 **event-action-outcome-sensitive closure** 敏感的 `closure_signature`

这次升级仍然不是完整 invariant prototype，也不是 planner；它只是把 `cycle` 从“输入桶记忆”推进到“最小 closure-sensitive identity”。

---

## 主链接入状态

- OpenEmotion `proto_self` 主链仍是当前变更对象
- EgoCore 侧没有改工具裁决、Governor、contract runtime 主权
- 旧 `/cycle` HTTP 链仍然存在，仍是命名冲突技术债

**判定**：边界归属未变，宿主现实裁决主权未变。

---

## 启用状态

- `OpenEmotion/openemotion/proto_self/cycles.py` 已升级为 closure-sensitive identity
- `OpenEmotion/openemotion/proto_self/trace_types.py` 已新增 closure-level trace 字段
- `OpenEmotion/openemotion/proto_self/state.py` 的 `CycleSignature` 已扩展为 closure-aware 持久状态
- `OpenEmotion/openemotion/proto_self/tests/` 全量回归通过

---

## 真实触发证据是否变化

**本轮没有新增真实 Telegram 触发证据。**

原因：

- 本轮任务是本体升级 + 补测，不是重新跑真实 Telegram 验证
- 已有真实证据链仍然成立，但它们对应的是升级前后连续演进的同一 `proto_self` 主链

因此当前口径应写成：

- **代码与本地测试已升级并通过**
- **真实触发证据未在本轮重新补采**

---

## 当前确定项

1. `cycle_id` 已不再只由 `psi_bucket` 决定
2. `closure_signature` 现在编码：
   - `psi_bucket`
   - `action_signature`
   - `outcome_signature`
3. `closure_family_id` 用于表达“同类闭环家族”，允许 success/failure 属于同一家族但不同 identity
4. `mode_signature` 与 `phi_signature` 已不再只是 trace 附属物：
   - `mode_signature` 进入 trace/state，并参与 closure 语义
   - `phi_signature` 进入 promotion gating 的一致性计算
5. promotion 已不再只看 `strength / hits`
6. unknown-outcome / 非闭合轨迹不会轻易 promote

---

## 关键未知

1. 当前 `closure_signature` 仍偏单轮 closure，不是多步完整闭环图结构
2. `order_invariance_candidate` 目前只是最小多前驱哈希，不是正式的 invariant proof
3. 宿主侧对 `policy_hint / response_tendency` 的消费仍主要是软约束/提示偏置，不是硬动作路由

---

## 本次变更分类

- 分类：**本体升级**
- 范围：**OpenEmotion `proto_self` 内部**
- 不变项：
  - 不改 EgoCore 工具主权
  - 不改 Governor / contract runtime 裁决归属
  - 不把 OpenEmotion 输出直接变成执行命令

---

## 升级前后 `cycle_id` 语义差异

### 升级前

`cycle_id = stable_hash(psi_bucket)`

结果：

- success/failure 可能命中同一 cycle
- `phi_signature` 只是被记在 trace 里
- promotion 更像“重复输入模式加权”

### 升级后

`closure_signature = stable_hash(psi_bucket + action_signature + outcome_signature)`

并新增：

- `closure_family_id = stable_hash(psi_bucket + action_signature)`
- `mode_signature`
- `closure_consistency_score`
- `order_invariance_candidate`

结果：

- success/failure 已能分裂到不同 `cycle_id`
- 同类 closure 仍可归入同一 family
- repair closure 可在重复后 strengthen / promote

---

## 新增测试清单

- `openemotion/proto_self/tests/test_cycle_closure_identity.py`
  - T1 `success/failure` 分裂测试
  - T2 repair closure 测试
  - T3 order invariance 最小测试
  - T4 non-closure suppression 测试
- `openemotion/proto_self/tests/test_cycle_truth_audit.py`
  - 已从 P1 的“反证旧缺口”更新为 P2 的“验证新闭环语义”
- `openemotion/proto_self/tests/test_kernel_replay.py`
  - 已补 closure-level replay 字段断言

---

## 测试结果

已执行：

```text
pytest --capture=no openemotion/proto_self/tests/test_cycle_closure_identity.py \
                     openemotion/proto_self/tests/test_cycle_truth_audit.py \
                     openemotion/proto_self/tests/test_kernel_cycles.py \
                     openemotion/proto_self/tests/test_kernel_reflection.py \
                     openemotion/proto_self/tests/test_kernel_replay.py -q
=> 24 passed

pytest --capture=no openemotion/proto_self/tests/test_schema_contract.py \
                     openemotion/proto_self/tests/test_kernel_drive_field.py \
                     openemotion/proto_self/tests/test_kernel_identity.py \
                     openemotion/proto_self/tests/test_kernel_boundaries.py -q
=> 14 passed

pytest --capture=no openemotion/proto_self/tests -q
=> 38 passed
```

---

## 哪个前提一旦为假应回退

只要下面任一项被证伪，就要重新评估本次升级：

1. 线上消费链并未真正使用当前 `proto_self` 实现，而是仍走旧 `/cycle` 链
2. `closure_signature` 在真实样本中引入了不可接受的 identity 抖动，导致 replay / determinism 退化
3. repair closure 的 promotion 在真实样本里被大量偶发噪声误触发

---

## 仍未实现什么

1. 还没有正式的多步 closure graph identity
2. 还没有“failure -> repair -> success”之外更通用的 closure archetype 框架
3. 还没有严格意义上的 invariant prototype 证明
4. 旧 `/cycle` HTTP 链与 `proto_self` 链的命名冲突仍未收口

**因此 P2 完成不等于“已经实现完整 invariant prototype”。**

---

## 下一步唯一优先动作

**在真实样本链上补一轮 closure-level evidence，验证升级后的 `closure_signature / closure_family_id / order_invariance_candidate` 是否在真实 Telegram 工具闭环里稳定出现。**
