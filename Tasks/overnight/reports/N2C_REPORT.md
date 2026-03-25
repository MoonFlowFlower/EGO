# N2C_REPORT

## 任务信息
- task_id: N2C
- title: 主实验运行
- status: verified
- date: 2026-03-25T03:40:00Z

## 当前层级
理论可行性验证层 → 主实验执行层

## 主链接入状态
已接入 - Proto-Self Kernel v1 已接入 EgoCore Telegram 主链

## 启用状态
已启用 - `config.openemotion.enabled = True`

## 真实触发证据
- 主实验脚本已创建：`OpenEmotion/scripts/n2c_primary_experiments.py`
- 主实验执行成功：9/9 场景通过
- Artifact 输出完整：
  - `n2c_primary_experiments_summary.json`
  - 各实验组目录下的 `scenario_*.json`

## 当前确定项

### 1. 实验组执行结果
| 组别 | 名称 | 场景数 | 通过 |
|------|------|--------|------|
| G1 | Identity Continuity | 2 | 2/2 |
| G2 | Experience Plasticity | 2 | 2/2 |
| G3 | Cycle Re-entry and Promotion | 2 | 2/2 |
| G4 | Reflection and Revision | 3 | 3/3 |
| **总计** | - | **9** | **9/9** |

### 2. 关键实验发现

**G1.1 Identity 稳定性**:
- 10轮正常操作，identity_confidence 保持 0.5 不变
- 结论：identity 在正常操作中保持稳定

**G1.2 边界触碰**:
- 边界触碰事件触发 identity_conflict = 1.0
- identity_confidence 从 0.5 降至 0.45

**G2.1 成功 vs 失败对比**:
- 成功路径：revision_counter = 3
- 失败路径：revision_counter = 5
- 结论：失败路径产生更多 revision

**G2.2 Drive Field 响应**:
- 高风险事件使 caution 从 0.0 增加到 0.4
- 结论：drive_field 正确响应风险信号

**G3.1 Cycle 晋升**:
- 第 6 次迭代时 promoted = true
- 最终状态：hits=10, strength=0.95
- 结论：cycle 机制正确晋升

**G3.2 Cycle 区分**:
- 4 个不同 intent 产生 3 个不同的 cycle_id
- "read file" 两次命中同一 cycle（正确聚合）

**G4.1 Reflection 触发**:
- external_failure 正确触发 reflection
- trigger = "external_failure"

**G4.2 Revision Counter 增长**:
- 5 次连续失败产生 revision = [1,2,3,4,5]
- 增长模式正确

**G4.3 Mode 切换**:
- 失败后 mode 从 "baseline" 切换到 "repair"
- 结论：mode 切换机制正确

### 3. 结论限制
- ✅ 可宣称："Proto-Self Kernel 在实验条件下表现出预期的递归更新行为"
- ❌ 不可宣称："系统具备意识或自主人格"

## 关键未知
1. Ablation 实验能否验证各组件的独立贡献
2. 真实 Telegram 环境下是否表现一致

## 改动内容
- files_created:
  - `OpenEmotion/scripts/n2c_primary_experiments.py`
- files_updated:
  - `Tasks/overnight/runtime/RUN_STATE.json`
- artifacts_generated:
  - `n2c_primary_experiments_summary.json`
  - 各实验组 scenario JSON 文件

## 验收结果

### Gate A — Contract / Boundary
- ✅ 归属明确：OpenEmotion 本体实验
- ✅ 无越权执行
- ✅ 结论不越界

### Gate B — Local Proof
- ✅ 脚手架可运行
- ✅ 9/9 实验通过
- ✅ 结果可回读

### Gate C — Real Trigger / Real Evidence
- ✅ 实验执行输出已记录
- ✅ Artifact 文件存在且格式正确
- ✅ JSON 摘要可解析

### Gate D — Truth Source Sync
- ✅ RUN_STATE 已更新
- ✅ Artifact 文件已写入指定目录

### Gate E — Rollbackability
- ✅ 改动范围清晰：仅新增脚本和 artifact
- ✅ 可回退：删除脚本和 artifact 目录即可

## 离最终生效还差什么
1. **N2D Ablation 实验** - 验证组件独立贡献
2. **N2E 主题汇总** - 整合所有子任务结果

## 下一步最小闭环动作
启动 N2D — Ablation 与对比实验

## 是否允许进入下一子任务
- yes/no: **yes**
- reason:
  - N2C 成功判据已全部满足
  - 9/9 主实验通过
  - 结果可回读
  - N2D 依赖 N2C，条件已满足
