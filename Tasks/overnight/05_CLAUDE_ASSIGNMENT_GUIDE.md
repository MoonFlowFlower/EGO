# 如何把这些主题批次分配给 Claude

## 结论

不要再按“今晚只给一个很小任务”去跑。
也不要一次性放开让 Claude 自由跑整包。

最稳的方式是：

> **一晚一个主题，一个新会话；主题内允许连续推进 3–5 个子任务。**

## 推荐分配顺序

### Night A
执行 `N2` 主题：
- N2A 实验合同冻结
- N2B 实验脚手架与 artifact 通道
- N2C 主实验运行
- N2D Ablation 与对比实验
- N2E 主题汇总与结论报告

### Night B
执行 `N3` 主题：
- N3A 样本合同与观测指标冻结
- N3B 应聚合样本与命中检查
- N3C 应区分样本与误聚合检查
- N3D Replay 一致性与风险清单

### Night C
执行 `N4` 主题：
- N4A 用户测试合同冻结
- N4B 只读诊断入口或等价脚本
- N4C 固定测试场景包
- N4D 操作手册、对照表与主题报告

## 主题内允许怎样跑

允许 Claude 在同一主题内连续推进多个子任务，但必须遵守：

1. 每个子任务结束先写文件化交接
2. 没有真实证据不得报 verified
3. 当前子任务若失败，先决定：
   - 是否以 `partial` 收口
   - 是否允许继续下一个子任务
4. 不允许跨主题跳转

## 分配前准备

把本包解压到工作目录外或固定目录中，然后在 Claude 的首条消息里同时给出：

1. 仓库路径
2. 本任务包路径
3. 本夜主题 ID（N2 / N3 / N4）
4. 明确要求它先读：
   - `00_START_HERE.md`
   - `01_GLOBAL_RULES.md`
   - `02_QUEUE.yaml`
   - `03_ACCEPTANCE.md`
   - `04_STOP_RULES.md`
   - `06_CONTEXT_AND_COMPACT_RULES.md`
   - `runtime/RUN_STATE.json`
   - 该主题说明文件
   - 该主题的所有子任务文件
5. 明确要求：
   - 先检查依赖
   - 主题内可连续推进
   - 只做指定主题
   - 每个子任务后都更新 `runtime/RUN_STATE.json`
   - 每个子任务后都写 `reports/<SUBTASK_ID>_REPORT.md`
   - 若还要继续，更新 `runtime/SESSION_HANDOFF.md`
   - 必要时 compact
   - 主题结束后写 `reports/<THEME_ID>_THEME_REPORT.md`

## 不推荐的分配方式

- N2 -> N3 -> N4 一夜全自动串行
- 只靠会话上下文硬接续
- 只靠 compact 摘要继续跑
- 让 Claude 自己决定今晚是否改主题
