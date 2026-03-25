# N3B_REPORT

## 任务信息
- task_id: N3B
- title: 应聚合样本与命中检查
- status: partial
- date: 2026-03-25T08:22:00Z

## 当前层级
泛化验证层 → 应聚合样本测试层

## 主链接入状态
已接入 - Proto-Self Kernel v1 已接入 EgoCore Telegram 主链

## 启用状态
已启用 - `config.openemotion.enabled = True`

## 真实触发证据
- 实验已执行：`artifacts/n3_experiments/n3_summary.json`
- 3 组应聚合样本测试完成
- 2/3 通过，1/3 失败

## 当前确定项

### 1. 应聚合测试结果

| 组别 | 名称 | 预期 cycle 数 | 实际 cycle 数 | 结果 |
|------|------|---------------|---------------|------|
| SM-1 | 文件读取类 | 1 | 1 | ✅ 通过 |
| SM-2 | 测试验证类 | 1 | 2 | ❌ 失败 |
| SM-3 | 状态查询类 | 1 | 1 | ✅ 通过 |

### 2. SM-2 失败分析

**样本分类情况**：
| 样本 | intent | 实际 coarse_intent | cycle_id |
|------|--------|-------------------|----------|
| SM-2a | "运行测试" | status_query | 5031b09d340c9fb7 |
| SM-2b | "验证功能" | test_verify | 34c1264506f1d7fe |
| SM-2c | "run e2e test" | test_verify | 34c1264506f1d7fe |
| SM-2d | "confirm the result" | test_verify | 34c1264506f1d7fe |

**根因**：`_coarse_intent_classify` 按优先级匹配，"运行测试"包含"运行"关键词，先被 `status_patterns` 匹配为 `status_query`，而其他样本被 `test_patterns` 匹配为 `test_verify`。

### 3. SM-3 意外发现

**预期**：status_query 类样本应聚合
**实际**：被分类为 file_read

| 样本 | intent | 实际 coarse_intent |
|------|--------|-------------------|
| SM-3a | "查看系统状态" | file_read |
| SM-3b | "检查日志" | file_read |
| SM-3c | "check health" | file_read |
| SM-3d | "show process list" | file_read |

**根因**：`"检查"` 和 `"查看"` 关键词被 `read_patterns` 优先匹配，导致 status_query 样本被错误分类为 file_read。

### 4. 关键发现

1. **关键词优先级冲突**：多个分类规则包含重叠关键词，导致预期分类失败
2. **中文关键词覆盖不完整**：部分中文关键词未被正确处理
3. **测试通过不代表预期正确**：SM-3 虽然通过（所有样本聚合到同一 cycle），但 coarse_intent 分类与预期不符

## 关键未知
1. 如何解决关键词优先级冲突
2. 是否需要改进 coarse intent 分类算法

## 改动内容
- artifacts_generated:
  - `artifacts/n3_experiments/n3_summary.json`

## 验收结果

### Gate A — Contract / Boundary
- ✅ 归属明确：OpenEmotion 本体实验
- ✅ 无越权执行

### Gate B — Local Proof
- ✅ 实验已执行
- ⚠️ 2/3 通过（partial）

### Gate C — Real Trigger / Real Evidence
- ✅ 实验结果可回读
- ✅ 失败样本已明确记录

### Gate D — Truth Source Sync
- ✅ 结果已写入 artifacts

### Gate E — Rollbackability
- ✅ 无状态污染

## 离最终生效还差什么
1. **N3C 应区分样本测试** - 检测误聚合
2. **N3D Replay 一致性与风险清单** - 最终收口

## 下一步最小闭环动作
执行 N3C 应区分样本测试

## 是否允许进入下一子任务
- yes/no: **yes**
- reason:
  - N3B 虽然有失败样本，但已明确记录原因
  - 失败揭示了真实的设计缺陷（关键词优先级冲突）
  - 符合 N3 主题目标：暴露边界条件
  - 不掩盖失败，不把"暂未发现问题"写成"问题不存在"
