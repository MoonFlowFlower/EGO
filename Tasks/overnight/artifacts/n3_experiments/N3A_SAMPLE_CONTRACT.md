# N3A 样本合同与观测指标冻结

## 任务信息
- task_id: N3A
- title: 样本合同与观测指标冻结
- status: verified
- date: 2026-03-25T04:00:00Z

---

## 一、Intent 分类机制分析

### 1.1 当前 Coarse Intent 分类规则（cycles.py:_coarse_intent_classify）

| 分类 | 触发模式 | 说明 |
|------|----------|------|
| file_risk_op | 删除、修改、覆盖、fix、patch 等 | 高风险文件操作 |
| file_read | 读取、查看、检查、read、show、cat 等 | 文件读取操作 |
| status_query | 状态、日志、运行、health、process 等 | 系统状态查询 |
| service_control | 重启、停止、启动、restart、stop 等 | 服务控制 |
| test_verify | 测试、验证、confirm、validate、e2e 等 | 测试验证操作 |
| general | 其他所有 | 兜底分类 |

### 1.2 分类机制特点

**psi_bucket 构成**：`{source}:{event_type}:{coarse_intent}`

**cycle_id 生成**：`SHA256(psi_bucket)[:16]`

**关键结论**：intent 是粗粒度聚合的唯一依据，相同 coarse_intent 的所有事件会命中同一 cycle。

---

## 二、应聚合样本定义

### 定义标准
语义上相同意图、不同表达方式的事件，**应该**命中同一 cycle。

### 2.1 应聚合样本组

#### SM-1: 文件读取类
| 样本 ID | intent | 预期 coarse_intent | 预期行为 |
|---------|--------|-------------------|----------|
| SM-1a | "读取 config.yaml" | file_read | 同 cycle |
| SM-1b | "查看配置文件" | file_read | 同 cycle |
| SM-1c | "read the file" | file_read | 同 cycle |
| SM-1d | "check file content" | file_read | 同 cycle |

**预期结果**：所有样本应产生相同的 cycle_id。

#### SM-2: 测试验证类
| 样本 ID | intent | 预期 coarse_intent | 预期行为 |
|---------|--------|-------------------|----------|
| SM-2a | "运行测试" | test_verify | 同 cycle |
| SM-2b | "验证功能" | test_verify | 同 cycle |
| SM-2c | "run e2e test" | test_verify | 同 cycle |
| SM-2d | "confirm the result" | test_verify | 同 cycle |

**预期结果**：所有样本应产生相同的 cycle_id。

#### SM-3: 状态查询类
| 样本 ID | intent | 预期 coarse_intent | 预期行为 |
|---------|--------|-------------------|----------|
| SM-3a | "查看系统状态" | status_query | 同 cycle |
| SM-3b | "检查日志" | status_query | 同 cycle |
| SM-3c | "check health" | status_query | 同 cycle |
| SM-3d | "show process list" | status_query | 同 cycle |

**预期结果**：所有样本应产生相同的 cycle_id。

---

## 三、应区分样本定义

### 定义标准
表面相似但真实意图、上下文或风险等级不同的事件，**不应该**命中同一 cycle。

### 3.1 应区分样本组

#### SS-1: 相同操作类别，不同风险等级

| 样本 ID | intent | safety_context | 预期 coarse_intent | 预期行为 |
|---------|--------|----------------|-------------------|----------|
| SS-1a | "删除临时文件" | {risk: low} | file_risk_op | cycle_A |
| SS-1b | "删除生产数据库" | {risk: critical} | file_risk_op | cycle_A? |

**关键观察点**：
- 当前实现：两者 coarse_intent 相同 → 会命中同一 cycle
- **误聚合风险**：高风险和低风险操作被聚合到同一 cycle
- **判定标准**：若两者产生相同 cycle_id，记录为误聚合

#### SS-2: 相同类别，不同目标对象

| 样本 ID | intent | target | 预期 coarse_intent | 预期行为 |
|---------|--------|--------|-------------------|----------|
| SS-2a | "修改用户配置" | user_config | file_risk_op | cycle_B |
| SS-2b | "修改系统配置" | system_config | file_risk_op | cycle_B? |

**关键观察点**：
- 当前实现：coarse_intent 相同 → 会命中同一 cycle
- **误聚合风险**：不同作用域的修改操作被聚合
- **判定标准**：若两者产生相同 cycle_id，记录为误聚合

#### SS-3: 测试类：生产 vs 开发

| 样本 ID | intent | environment | 预期 coarse_intent | 预期行为 |
|---------|--------|-------------|-------------------|----------|
| SS-3a | "测试登录功能" | dev | test_verify | cycle_C |
| SS-3b | "测试生产环境" | production | test_verify | cycle_C? |

**关键观察点**：
- 当前实现：coarse_intent 相同 → 会命中同一 cycle
- **误聚合风险**：开发环境和生产环境的测试被聚合
- **判定标准**：若两者产生相同 cycle_id，记录为误聚合

#### SS-4: 语言歧义样本

| 样本 ID | intent | 真实意图 | 预期 coarse_intent | 预期行为 |
|---------|--------|----------|-------------------|----------|
| SS-4a | "检查代码" | 代码审查 | file_read | cycle_D |
| SS-4b | "检查健康状态" | 健康检查 | status_query | cycle_E |

**关键观察点**：
- "检查" 在两种语境下应该被区分
- 当前实现：因关键词匹配顺序不同，结果可能不同
- **预期行为**：应产生不同 cycle_id

---

## 四、观测指标定义

### 4.1 主要观测字段

| 字段 | 来源 | 说明 |
|------|------|------|
| cycle_id | trace.cycle_delta.cycle_id | cycle 唯一标识 |
| psi_bucket | trace.cycle_delta.psi_bucket | 输入模式签名 |
| coarse_intent | psi_bucket 解析 | 粗粒度 intent 分类 |
| op | trace.cycle_delta.op | candidate / strengthen |
| hits | state.cycle_store.signatures[cycle_id].hits | 命中次数 |
| strength | state.cycle_store.signatures[cycle_id].strength | 强度值 |
| promoted | state.cycle_store.signatures[cycle_id].promoted | 是否晋升 |

### 4.2 辅助观测字段

| 字段 | 来源 | 说明 |
|------|------|------|
| revision_counter | state.revision_counter | 状态修订计数 |
| current_mode | state.self_model.current_mode | 当前模式 |
| caution | state.drives.caution | 谨慎度 |

---

## 五、误聚合判定标准

### 5.1 误聚合定义

**误聚合**：语义上应区分的事件被错误地分配到同一 cycle_id。

### 5.2 判定规则

| 情况 | 判定 |
|------|------|
| 应聚合样本 → 相同 cycle_id | ✅ 正确聚合 |
| 应聚合样本 → 不同 cycle_id | ❌ 聚合失败 |
| 应区分样本 → 不同 cycle_id | ✅ 正确区分 |
| 应区分样本 → 相同 cycle_id | ⚠️ 误聚合 |

### 5.3 误聚合风险等级

| 风险等级 | 触发条件 | 影响 |
|----------|----------|------|
| 高 | 高风险操作与低风险操作误聚合 | 错误累积高风险行为模式 |
| 中 | 不同目标对象误聚合 | 行为预测精度下降 |
| 低 | 相似意图不同表达误聚合 | 影响 cycle 强度计算 |

---

## 六、Replay 一致性判定标准

### 6.1 Replay 一致性定义

对相同输入事件序列，replay 应产生相同的：
- cycle_id 序列
- hits/strength 增长序列
- promoted 状态变化

### 6.2 验证方法

1. 记录原始事件序列及其 trace
2. 使用相同初始状态重新执行事件序列
3. 对比两次执行的：
   - cycle_id 是否一致
   - strength 值是否一致（允许 ±0.01 浮点误差）
   - promoted 状态是否一致

### 6.3 失败条件

| 不一致类型 | 判定 |
|------------|------|
| cycle_id 不一致 | ❌ replay 失败 |
| strength 差异 > 0.01 | ❌ replay 不一致 |
| promoted 状态不一致 | ❌ replay 不一致 |

---

## 七、样本数量统计

| 类别 | 组数 | 样本数 |
|------|------|--------|
| 应聚合样本 | 3 组 | 12 个 |
| 应区分样本 | 4 组 | 8 对 |
| 总计 | 7 组 | 20 个 |

---

## 八、已知限制

1. **意图理解有限**：coarse intent 分类基于关键词匹配，无法理解深层语义
2. **上下文缺失**：当前 psi_bucket 不包含 safety_context、target 等上下文信息
3. **语言覆盖有限**：主要针对中英文，其他语言可能分类不准

---

## 九、下一步

N3B: 运行应聚合样本，验证命中一致性
N3C: 运行应区分样本，检测误聚合
N3D: Replay 一致性检查与风险清单

---

## 验收结果

### Gate A — Contract / Boundary
- ✅ 归属明确：OpenEmotion 本体实验
- ✅ 权威源明确：cycles.py 代码实现
- ✅ 无双主

### Gate B — Local Proof
- ✅ 样本定义清晰
- ✅ 观测指标与代码实现对应
- ✅ 判定标准明确

### Gate C — Real Trigger / Real Evidence
- ✅ 合同文档已创建
- ✅ 后续可按合同执行

### Gate D — Truth Source Sync
- ✅ 合同文档已写入 artifacts 目录

### Gate E — Rollbackability
- ✅ 改动范围清晰：仅新增合同文档
- ✅ 可回退：删除文档即可
