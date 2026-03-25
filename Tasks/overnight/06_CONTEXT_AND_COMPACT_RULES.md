# 上下文、交接与 compact 规则

## 核心原则

- 会话上下文不是权威源
- `runtime/RUN_STATE.json` + `reports/*.md` + `artifacts/` 才是权威交接链
- `compact` 只是减负工具，不是闭环保障

## 默认主方案

### 每主题一个新会话
- 一晚只跑一个主题
- 主题内允许多个子任务连续推进
- 子任务间靠文件交接，而不是靠自然会话记忆

## 主题内子任务切换顺序

每完成一个子任务，必须按这个顺序：

1. 更新 `runtime/RUN_STATE.json`
2. 写 `reports/<SUBTASK_ID>_REPORT.md`
3. 如需继续：
   - 更新 `runtime/SESSION_HANDOFF.md`
   - 判断是否需要 compact
4. 下一个子任务开始前重新读取：
   - `01_GLOBAL_RULES.md`
   - `03_ACCEPTANCE.md`
   - `04_STOP_RULES.md`
   - `runtime/RUN_STATE.json`
   - `runtime/SESSION_HANDOFF.md`
   - 上一个子任务报告

## 何时应该 compact

满足任一条件即可：
- 已读取长日志
- 已查看大 diff
- 已跨过 2 个以上子任务
- 当前会话历史已明显过长
- 当前主题仍要继续，但上下文开始拥挤

## compact 前必须先落地的内容

不能只留在会话里，必须写文件：

- 当前子任务状态
- 是否 verified / partial / blocked
- stop_reason
- 关键证据路径
- 下一子任务入口条件
- 当前主题是否允许继续

## SESSION_HANDOFF 必须包含

- 当前主题
- 当前子任务
- 已完成子任务
- 当前 verified / partial / blocked 状态
- 关键 artifacts / reports
- 当前关键未知
- 下一子任务入口动作
- 是否建议继续 / 停止
