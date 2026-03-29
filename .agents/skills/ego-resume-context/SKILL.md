---
name: "ego-resume-context"
description: "Use when the user says continue, resume, restore context, pick up where we left off, or asks what state the current task is in. Do not use when starting a brand-new task, doing a focused bugfix from a fresh error report, or implementing a clearly scoped milestone from scratch. Boundary: this skill reconstructs current state and next action; it does not automatically launch broad implementation unless the user explicitly asks to proceed."
---

# Ego Resume Context

先读：

1. `AGENTS.md`
2. `PROJECT_MEMORY.md`
3. 当前任务的 spec / plan / acceptance / status / review
4. 最近的 evidence report 或 status report

必要时参考：

- `.agents/references/task-state-and-handoff.md`
- `.agents/references/engineering-evidence-model.md`

## Workflow

1. 识别当前任务和 authority source。
2. 恢复当前状态：
   - real goal
   - success criteria
   - current layer
   - main-chain status
   - blocker
   - verification level
3. 区分已证实与未证实，不把历史计划当事实。
4. 给出唯一最高优先级的下一步最小闭环动作。
5. 默认先恢复上下文，不直接进入大范围改动。

## Output

至少给出：

- 当前进度
- 已证实项
- 未证实项
- 当前 blocker
- 下一步最小闭环动作

## Boundary

- 若用户只说“继续”，先恢复状态再推进。
- 若用户明确要求“继续并直接做”，恢复完最小状态后可进入当前最小动作。
