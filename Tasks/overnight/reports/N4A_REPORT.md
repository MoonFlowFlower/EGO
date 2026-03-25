# N4A_REPORT

## 任务信息
- task_id: N4A
- title: 用户测试合同冻结
- status: verified
- date: 2026-03-25T09:00:00Z

## 当前层级
用户可体验收口层 → 测试合同定义层

## 主链接入状态
已接入 - Proto-Self Kernel v1 已接入 EgoCore Telegram 主链

## 启用状态
已启用 - `config.openemotion.enabled = True`

## 真实触发证据
- 合同文档已创建：`artifacts/n4_user_test/N4A_USER_TEST_CONTRACT.md`
- 定义了 3 组固定测试场景
- 定义了每一步用户要看什么

## 当前确定项

### 1. 测试目标已冻结
- 验证 Cycle 聚合机制
- 验证 Reflection 触发机制
- 验证已知误聚合风险可见性

### 2. 固定测试场景

| 场景 | 目的 | 类型 |
|------|------|------|
| S1 | 重复相似事件 | Cycle 聚合测试 |
| S2 | 失败回流事件 | Reflection 触发测试 |
| S3 | 可区分意图事件 | 误聚合风险验证 |

### 3. 诊断信号已定义

| 字段 | 路径 | 说明 |
|------|------|------|
| cycle_count | state.cycle_store.signatures | cycle 数量 |
| cycle_id | trace.cycle_delta.cycle_id | 命中的 cycle |
| hits | state.cycle_store.signatures[id].hits | 命中次数 |
| strength | state.cycle_store.signatures[id].strength | 强度 |
| revision_counter | state.revision_counter | 修订计数 |
| current_mode | state.self_model.current_mode | 当前模式 |

## 关键未知
1. 用户实际测试时是否能成功
2. 真实 Telegram 环境下诊断是否有效

## 改动内容
- files_created:
  - `Tasks/overnight/artifacts/n4_user_test/N4A_USER_TEST_CONTRACT.md`

## 验收结果

### Gate A — Contract / Boundary
- ✅ 归属明确：用户测试指导
- ✅ 不修改核心代码
- ✅ 诊断入口只读

### Gate B — Local Proof
- ✅ 场景定义清晰
- ✅ 观测字段明确
- ✅ 判定标准可操作

### Gate C — Real Trigger / Real Evidence
- ✅ 合同文档已创建
- ✅ 后续可按合同执行

### Gate D — Truth Source Sync
- ✅ 合同文档已写入 artifacts 目录

### Gate E — Rollbackability
- ✅ 改动范围清晰：仅新增合同文档
- ✅ 可回退：删除文档即可

## 离最终生效还差什么
1. **N4B 只读诊断入口** - 需要实现诊断脚本
2. **N4C 固定测试场景包** - 需要扩展场景
3. **N4D 操作手册** - 需要编写手册

## 下一步最小闭环动作
执行 N4B — 只读诊断入口实现

## 是否允许进入下一子任务
- yes/no: **yes**
- reason:
  - N4A 成功判据已满足
  - 测试合同已冻结
  - 场景定义清晰
