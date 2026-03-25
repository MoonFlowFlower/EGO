# Proto-Self 夜间批任务包 v3

## 一句话结论

本包默认承认以下已确认状态，不允许从头重复排查：

- N1 已 verified
- Proto-Self Kernel v1 已接入 EgoCore Telegram 主链
- 已启用
- 已通过真实 Telegram E2E
- 已证实：cycle strengthen、external_result 回流、external_failure reflection、revision_counter 增长

当前夜间主线不是“重新证明有没有启用”，而是：

1. 把 **N2** 改成可跑一整夜的“递归核实验主题批次”
2. 把 **N3** 改成可跑一整夜的“泛化与反证主题批次”
3. 把 **N4** 改成可跑一整夜的“用户可测入口主题批次”

## 当前层级

从“治理收尾层已完成”进入“实验化验证层 / 泛化验证层 / 用户可体验收口层”。

## 当前确定项

- `runtime/RUN_STATE.json` 默认承认 N1 已完成且已 verified
- `reports/N1_REPORT.md` 已纳入本包
- 本包的默认起点是：**从 N2 或其后续主题开始，不再回头做 N1**

## 本批次唯一主目标

把 Proto-Self Kernel v1 从“已过一次最小主链 E2E”推进到：

- 可默认回归
- 可反驳实验
- 可识别边界
- 可由用户亲测
- 可整夜连续推进但不失真

## 目录说明

- `01_GLOBAL_RULES.md`：全局硬规则
- `02_QUEUE.yaml`：主题队列、子任务顺序、依赖和停机策略
- `03_ACCEPTANCE.md`：统一验收口径
- `04_STOP_RULES.md`：强制停止条件
- `05_CLAUDE_ASSIGNMENT_GUIDE.md`：如何把主题批次分配给 Claude
- `06_CONTEXT_AND_COMPACT_RULES.md`：上下文、交接、compact 规则
- `tasks/`：主题说明与子任务说明
- `runtime/RUN_STATE.json`：运行态
- `runtime/SESSION_HANDOFF.md`：跨子任务/跨会话交接
- `reports/`：N1 报告与模板
- `prompts/`：可直接粘贴给 Claude 的提示词

## 推荐执行方式

最稳方式：**一晚一个主题批次，一个新会话**。

同一主题内允许连续跑多个子任务，但必须在每个子任务后：

1. 更新 `runtime/RUN_STATE.json`
2. 生成 `reports/<SUBTASK_ID>_REPORT.md`
3. 若继续跑下一个子任务：
   - 更新 `runtime/SESSION_HANDOFF.md`
   - 必要时 compact
   - 再继续

## 推荐夜间节奏

- Night A：N2 递归核有效性实验主题
- Night B：N3 泛化、误聚合与反证主题
- Night C：N4 用户可测入口与诊断主题

默认一晚只跑 **一个主题**，但主题内可以连续推进多个子任务，直到：
- 当前主题完成
- 触发 stop rule
- 环境异常导致验证结果不可信
