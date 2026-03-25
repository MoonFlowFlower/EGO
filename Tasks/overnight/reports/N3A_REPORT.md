# N3A_REPORT

## 任务信息
- task_id: N3A
- title: 样本合同与观测指标冻结
- status: verified
- date: 2026-03-25T08:15:00Z

## 当前层级
泛化验证层 → 样本合同定义层

## 主链接入状态
已接入 - Proto-Self Kernel v1 已接入 EgoCore Telegram 主链

## 启用状态
已启用 - `config.openemotion.enabled = True`

## 真实触发证据
- 样本合同已创建：`artifacts/n3_experiments/N3A_SAMPLE_CONTRACT.md`
- 实验脚本已创建：`OpenEmotion/scripts/n3_experiment_harness.py`
- 定义了 3 组应聚合样本（12 个）、4 组应区分样本（8 对）
- 观测指标与 cycles.py 代码实现对应

## 当前确定项

### 1. Intent 分类机制分析

**psi_bucket 构成**：`{source}:{event_type}:{coarse_intent}`

**cycle_id 生成**：`SHA256(psi_bucket)[:16]`

**关键发现**：`safety_context` 和 `target` 等上下文信息**未纳入** psi_bucket 计算。

### 2. 样本定义

| 类别 | 组数 | 样本数 |
|------|------|--------|
| 应聚合样本 (SM) | 3 组 | 12 个 |
| 应区分样本 (SS) | 4 组 | 8 对 |

### 3. 误聚合判定标准已定义

| 情况 | 判定 |
|------|------|
| 应聚合样本 → 相同 cycle_id | ✅ 正确聚合 |
| 应聚合样本 → 不同 cycle_id | ❌ 聚合失败 |
| 应区分样本 → 不同 cycle_id | ✅ 正确区分 |
| 应区分样本 → 相同 cycle_id | ⚠️ 误聚合 |

### 4. Replay 一致性判定标准已定义

- cycle_id 序列一致
- strength 值一致（允许 ±0.01 浮点误差）
- promoted 状态一致

## 关键未知
1. 应聚合样本实际命中率如何
2. 应区分样本误聚合比例
3. Replay 是否真正一致

## 改动内容
- files_created:
  - `Tasks/overnight/artifacts/n3_experiments/N3A_SAMPLE_CONTRACT.md`
  - `OpenEmotion/scripts/n3_experiment_harness.py`
- files_updated:
  - `Tasks/overnight/runtime/RUN_STATE.json`

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
- ✅ 实验脚本已创建
- ✅ 后续可按合同执行

### Gate D — Truth Source Sync
- ✅ 合同文档已写入 artifacts 目录

### Gate E — Rollbackability
- ✅ 改动范围清晰：仅新增合同文档和实验脚本
- ✅ 可回退：删除文档和脚本即可

## 离最终生效还差什么
1. **N3B 应聚合样本测试** - 验证命中率
2. **N3C 应区分样本测试** - 检测误聚合
3. **N3D Replay 一致性与风险清单** - 最终收口

## 下一步最小闭环动作
执行 N3B/N3C 实验并记录结果

## 是否允许进入下一子任务
- yes/no: **yes**
- reason:
  - N3A 成功判据已全部满足
  - 样本合同已冻结
  - 观测指标和判定标准明确
  - 实验脚本可运行
