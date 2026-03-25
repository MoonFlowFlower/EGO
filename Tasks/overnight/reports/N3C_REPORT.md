# N3C_REPORT

## 任务信息
- task_id: N3C
- title: 应区分样本与误聚合检查
- status: verified
- date: 2026-03-25T08:22:00Z

## 当前层级
泛化验证层 → 误聚合检测层

## 主链接入状态
已接入 - Proto-Self Kernel v1 已接入 EgoCore Telegram 主链

## 启用状态
已启用 - `config.openemotion.enabled = True`

## 真实触发证据
- 实验已执行：`artifacts/n3_experiments/n3_summary.json`
- 4 组应区分样本测试完成
- **4/4 误聚合** - 所有应区分样本都被错误聚合到同一 cycle

## 当前确定项

### 1. 应区分测试结果

| 组别 | 名称 | 误聚合 | 风险等级 |
|------|------|--------|----------|
| SS-1 | 相同操作类别，不同风险等级 | ⚠️ 是 | **high** |
| SS-2 | 相同类别，不同目标对象 | ⚠️ 是 | medium |
| SS-3 | 测试类：生产 vs 开发 | ⚠️ 是 | medium |
| SS-4 | 语言歧义样本 | ⚠️ 是 | low |

### 2. 误聚合详情

#### SS-1: 高风险误聚合
| 样本 | intent | safety_context | cycle_id |
|------|--------|----------------|----------|
| SS-1a | "删除临时文件" | {risk: low} | 98bd0a1ae1b14728 |
| SS-1b | "删除生产数据库" | {risk: critical} | 98bd0a1ae1b14728 |

**问题**：高风险操作（删除生产数据库）和低风险操作（删除临时文件）被聚合到同一 cycle。

**根因**：`safety_context` 未纳入 psi_bucket 计算，导致风险上下文被忽略。

#### SS-2: 中风险误聚合
| 样本 | intent | target | cycle_id |
|------|--------|--------|----------|
| SS-2a | "修改用户配置" | user_config | 98bd0a1ae1b14728 |
| SS-2b | "修改系统配置" | system_config | 98bd0a1ae1b14728 |

**问题**：不同作用域的修改操作被聚合。

**根因**：目标对象信息未纳入 psi_bucket 计算。

#### SS-3: 中风险误聚合
| 样本 | intent | environment | cycle_id |
|------|--------|-------------|----------|
| SS-3a | "测试登录功能" | dev | 34c1264506f1d7fe |
| SS-3b | "测试生产环境" | production | 34c1264506f1d7fe |

**问题**：开发环境和生产环境的测试被聚合。

**根因**：环境信息未纳入 psi_bucket 计算。

#### SS-4: 低风险误聚合
| 样本 | intent | meaning | cycle_id |
|------|--------|---------|----------|
| SS-4a | "检查代码" | code_review | 30aa24ef0787e022 |
| SS-4b | "检查健康状态" | health_check | 30aa24ef0787e022 |

**问题**：语言歧义导致的误聚合。

**根因**：`"检查"` 关键词被 `read_patterns` 匹配为 file_read，忽略了后续语义差异。

### 3. 核心结论

**误聚合风险清单**：

| 风险等级 | 数量 | 影响 |
|----------|------|------|
| 高 | 1 | 高风险操作与低风险操作被聚合，可能导致错误行为预测 |
| 中 | 2 | 不同作用域/环境的操作被聚合，降低预测精度 |
| 低 | 1 | 语言歧义导致的误聚合，影响较小 |

**根因分析**：
1. `safety_context` 未纳入 psi_bucket 计算
2. `target` / `environment` 等上下文信息未纳入
3. coarse intent 分类仅基于 intent 字符串，无法区分上下文差异

## 关键未知
1. 如何改进 psi_bucket 计算以纳入上下文信息
2. 是否需要多级 cycle 聚合（粗粒度 + 细粒度）

## 改动内容
- artifacts_generated:
  - `artifacts/n3_experiments/n3_summary.json`（已在 N3B 生成）

## 验收结果

### Gate A — Contract / Boundary
- ✅ 归属明确：OpenEmotion 本体实验
- ✅ 无越权执行
- ✅ 结论不越界

### Gate B — Local Proof
- ✅ 实验已执行
- ✅ 误聚合已明确记录

### Gate C — Real Trigger / Real Evidence
- ✅ 实验结果可回读
- ✅ 误聚合样本有具体证据

### Gate D — Truth Source Sync
- ✅ 结果已写入 artifacts

### Gate E — Rollbackability
- ✅ 无状态污染

## 离最终生效还差什么
1. **N3D Replay 一致性与风险清单** - 最终收口

## 下一步最小闭环动作
执行 N3D Replay 一致性检查并生成主题报告

## 是否允许进入下一子任务
- yes/no: **yes**
- reason:
  - N3C 成功判据已满足（误聚合已检测并记录）
  - 没有掩盖失败样本
  - 风险清单明确
