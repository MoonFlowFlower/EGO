# N3D_REPORT

## 任务信息
- task_id: N3D
- title: Replay 一致性与风险清单
- status: verified
- date: 2026-03-25T08:23:00Z

## 当前层级
泛化验证层 → 收口层

## 主链接入状态
已接入 - Proto-Self Kernel v1 已接入 EgoCore Telegram 主链

## 启用状态
已启用 - `config.openemotion.enabled = True`

## 真实触发证据
- Replay 测试已执行：`artifacts/n3_experiments/n3_summary.json`
- 1/1 Replay 测试通过
- 风险清单已生成

## 当前确定项

### 1. Replay 一致性测试结果

| 测试 ID | 事件数 | cycle_id 一致 | strength 一致 | 结果 |
|---------|--------|---------------|---------------|------|
| replay-001 | 5 | ✅ 是 | ✅ 是 | ✅ 通过 |

**详情**：
- 原始 cycle_ids: `['30aa24ef0787e022'] * 5`
- Replay cycle_ids: `['30aa24ef0787e022'] * 5`
- 原始 strengths: `[0.05, 0.15, 0.25, 0.35, 0.45]`
- Replay strengths: `[0.05, 0.15, 0.25, 0.35, 0.45]`

**结论**：Replay 一致性验证通过，状态演进是确定性的。

### 2. 风险清单汇总

#### 已证实范围
1. ✅ Replay 一致性 - 相同输入序列产生相同 cycle_id 和 strength
2. ✅ 应聚合样本（文件读取类、状态查询类）可以正确聚合
3. ✅ Cycle 机制确定性可复现

#### 未证实范围
1. ❌ 所有应聚合样本都能正确聚合（SM-2 失败）
2. ❌ 应区分样本能被正确区分（4/4 误聚合）
3. ❌ safety_context 影响聚合决策

#### 已发现误聚合风险

| 风险 | 等级 | 触发条件 | 影响 |
|------|------|----------|------|
| 高风险操作误聚合 | **HIGH** | 高风险操作与低风险操作 intent 相似 | 错误累积高风险行为模式 |
| 不同作用域误聚合 | MEDIUM | 不同目标对象的修改操作 intent 相似 | 行为预测精度下降 |
| 环境上下文误聚合 | MEDIUM | 开发/生产环境测试 intent 相似 | 环境敏感决策失误 |
| 语言歧义误聚合 | LOW | 关键词重叠但语义不同 | cycle 强度计算偏差 |
| 分类优先级冲突 | LOW | 关键词匹配顺序导致分类不一致 | 应聚合样本被分开 |

#### 根因分析

**核心问题**：`psi_bucket = "{source}:{event_type}:{coarse_intent}"` 仅包含三个维度，缺失：
- `safety_context`（风险等级）
- `target`（目标对象）
- `environment`（环境上下文）
- `extra_context`（额外语义信息）

**影响**：coarse intent 过于粗粒度，无法区分上下文差异。

### 3. 改进建议

#### 短期（可选）
1. 将 `safety_context.risk` 纳入 psi_bucket 计算
2. 调整 `_coarse_intent_classify` 关键词匹配优先级

#### 长期（需要架构变更）
1. 引入多级 cycle 聚合（粗粒度 + 细粒度）
2. 使用语义相似度替代关键词匹配
3. 引入上下文感知的 cycle 区分机制

## 关键未知
1. 这些误聚合在实际使用中会造成多大影响
2. 用户是否会在意这些区分

## 改动内容
- artifacts_generated:
  - `artifacts/n3_experiments/n3_summary.json`（已在 N3B/N3C 生成）

## 验收结果

### Gate A — Contract / Boundary
- ✅ 归属明确：OpenEmotion 本体实验
- ✅ 无越权执行
- ✅ 结论不越界

### Gate B — Local Proof
- ✅ Replay 测试通过
- ✅ 风险清单明确

### Gate C — Real Trigger / Real Evidence
- ✅ Replay 结果有证据
- ✅ 误聚合有具体样本

### Gate D — Truth Source Sync
- ✅ 结果已写入 artifacts
- ✅ 主题报告待生成

### Gate E — Rollbackability
- ✅ 无状态污染

## 离最终生效还差什么
主题报告生成

## 下一步最小闭环动作
生成 N3_THEME_REPORT.md

## 是否允许进入下一子任务
- yes/no: **yes**
- reason:
  - N3D 成功判据已满足
  - 风险清单明确
  - Replay 一致性验证通过
