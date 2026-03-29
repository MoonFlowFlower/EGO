---
name: "ego-handoff-brief"
description: "Use when the user explicitly asks for a handoff, delegation brief, subagent brief, or execution brief for another agent or operator. Do not use when the user wants normal planning, implementation, review, or context recovery. Boundary: this skill packages the current task state for another executor; it does not implement the task itself and should not trigger implicitly."
---

# Ego Handoff Brief

先读：

1. `AGENTS.md`
2. 当前任务的 spec / plan / acceptance / status / review
3. `PROJECT_MEMORY.md`
4. 最新 evidence / blocker / status report

必要时参考：

- `.agents/references/task-state-and-handoff.md`
- `.agents/references/engineering-evidence-model.md`

## Workflow

1. 提炼当前任务的真实目标和成功判据。
2. 固定当前层级、主链状态、authority source。
3. 写清 proof required：
   - 什么证据才算有效
   - 现在缺什么
4. 写清 change classification、风险、边界。
5. 写清下一步最小动作与失败回退方案。

## Output

handoff brief 至少包含：

- task type
- real goal
- success criteria
- current layer
- authority source
- current blocker
- proof required
- minimal decision point
- next action
- rollback / exit plan

## Boundary

- 不隐式触发。
- 不负责实际实现，只负责把当前任务状态交给下一个执行者。
