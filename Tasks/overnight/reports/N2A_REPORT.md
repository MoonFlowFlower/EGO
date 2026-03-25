# N2A_REPORT

## 任务信息
- task_id: N2A
- title: 实验合同冻结
- status: verified
- date: 2026-03-25T03:15:00Z

## 当前层级
理论可行性验证层 → 实验合同定义层

## 主链接入状态
已接入 - Proto-Self Kernel v1 已接入 EgoCore Telegram 主链

## 启用状态
已启用 - `config.openemotion.enabled = True`

## 真实触发证据
- 合同文档已创建：`artifacts/n2_experiments/N2A_EXPERIMENT_CONTRACT.md`
- 4 类实验定义完整：
  - E1: Identity Continuity
  - E2: Cycle Re-entry / Strengthen
  - E3: Reflection Trigger & Revision Impact
  - E4: Policy Hint & Response Tendency
- 每类实验包含：输入序列、观测字段、预期、失败条件、结论限制
- Artifact 输出位置明确
- 不可宣称清单已定义

## 当前确定项

### 1. 实验合同已冻结
合同文档定义了：
- 4 类必测对象
- 每类的输入序列模板
- 每类的观测字段（与代码实现对应）
- 每类的预期结果
- 每类的失败条件
- 结论限制（哪些不能宣称）

### 2. 观测字段与代码映射
| 实验类 | 观测字段 | 代码来源 |
|--------|----------|----------|
| E1 | identity.* | state.py:IdentityInvariants |
| E2 | cycle_delta.* | cycles.py:consolidate_cycles |
| E3 | reflection_note.*, revision_counter | reflection.py, state.py |
| E4 | policy_hint, response_tendency | kernel.py reducers |

### 3. 禁止口径清单
- ❌ 已证明意识
- ❌ 系统具备自主人格
- ❌ 已完成整个 EGO 项目
- ❌ 递归核在所有场景下有效
- ❌ cycle 机制永远不会误聚合
- ❌ reflection 总是正确的

## 关键未知
1. 实验脚手架能否在真实环境中运行
2. 真实 Telegram 消息是否会产生预期内的 state 变化
3. Ablation 实验是否可行（需要组件开关）

## 改动内容
- files_created:
  - `Tasks/overnight/artifacts/n2_experiments/N2A_EXPERIMENT_CONTRACT.md`
- files_updated:
  - `Tasks/overnight/runtime/RUN_STATE.json`
- artifacts_generated:
  - 实验合同文档（本文档引用的源）

## 验收结果

### Gate A — Contract / Boundary
- ✅ 归属明确：OpenEmotion 本体实验
- ✅ 权威源明确：合同文档 + 代码实现
- ✅ 无双主
- ✅ 无越权执行

### Gate B — Local Proof
- ✅ 合同格式正确
- ✅ 实验定义清晰
- ✅ 观测字段与代码实现对应
- ✅ 通过/失败标准明确

### Gate C — Real Trigger / Real Evidence
- ✅ 合同文档已创建
- ✅ 后续可按合同执行
- ✅ 文档可回读

### Gate D — Truth Source Sync
- ✅ 合同文档已写入 artifacts 目录
- ✅ RUN_STATE 已更新
- ✅ 本报告已生成

### Gate E — Rollbackability
- ✅ 改动范围清晰：仅新增合同文档
- ✅ 可回退：删除文档即可
- ✅ 无后续任务依赖不可信中间状态

## 离最终生效还差什么
1. **N2B 实验脚手架** - 需要实现可运行的实验入口
2. **N2C 主实验运行** - 需要执行实验并收集数据
3. **N2D Ablation 实验** - 需要对比有无组件的差异

## 下一步最小闭环动作
启动 N2B — 实验脚手架与 artifact 通道

## 是否允许进入下一子任务
- yes/no: **yes**
- reason:
  - N2A 成功判据已全部满足
  - 实验合同已冻结
  - 合同文档可回读
  - N2B 依赖 N2A，条件已满足
