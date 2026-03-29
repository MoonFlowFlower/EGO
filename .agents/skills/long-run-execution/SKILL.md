---
name: "long-run-execution"
description: "Use when the task is a multi-step long run with milestones, continuous verification, and status accounting, especially when a docs/codex/tasks/<slug>/ directory already exists or the prompt includes LONGRUN. Do not use when the task is a small single-file fix, a small bug, a small refactor, pure planning, pure review, or pure Q&A. Boundary: this skill executes an existing long-run task loop one milestone at a time; it does not replace initial planning and it should not invent a second task-tracking system."
---

# Long-Run Execution

先读：`AGENTS.md`、`docs/codex/README.md`、当前任务目录下的 `SPEC.md`、`PLAN.md`、`IMPLEMENT.md`、`STATUS.md`，以及其中引用的 authority refs。

必要时再读根 `AGENTS.md` 引用的 repo reference docs，以及已存在的 `Tasks/active/*.md` / review / report 文档。

## Input

- 必填：`docs/codex/tasks/<slug>/`
- 可选：当前任务引用的 `Tasks/active/*.md`、spec、review、report、acceptance 文档

## Output

- 更新后的 `PLAN.md / STATUS.md`
- 当前 milestone 的验证结果
- 已做决策、风险、下一步、rollback notes
- 最终收口时的结果摘要

## Workflow

1. 如果 `docs/codex/tasks/<slug>/` 不存在，先用 `python3 scripts/codex/new_task.py <slug>` 创建任务目录。
2. 先按固定顺序读取：`SPEC -> PLAN -> IMPLEMENT -> STATUS`。
3. 用 `STATUS.md` 的 `Current milestone` 锁定当前执行切片；没有锁定前，不进入正式实现。
4. 只推进当前 milestone；不要顺手做下一个。
5. 完成 milestone 后运行统一验证脚本：
   - 默认：`python3 scripts/codex/verify_repo.py --mode fast`
   - milestone 收口、高风险改动、或最终 closeout：`python3 scripts/codex/verify_repo.py --mode full`
6. 把验证结果、decisions、risks、next step、rollback notes、commands run、evidence 写回 `PLAN.md / STATUS.md`。
7. 只有当前 milestone 验证通过或已明确记录 blocker，才决定继续、停留、或切换到下一个 milestone。

## LONGRUN explicit mode

当 prompt 含 `LONGRUN` 时：

- 默认不为常规实现细节征求用户
- 采用最小合理假设推进，并把假设写进 `PLAN.md` 的 `Decision log`
- 当前 milestone 收口后，如果下一 milestone 已解锁且无 blocker，继续推进
- 只有以下硬 blocker 才停：
  - 缺少外部凭据、密钥、服务或人工审批
  - destructive action 需要明确确认
  - authority source 相互矛盾，继续实现会失真
  - 当前 milestone 经验证后证明无法在原范围内闭环，需要回到规划

## Stopping rule

- 当前 milestone 未验证，不进入下一个 milestone
- 验证失败且无法在当前范围修复时，记录 blocker 并停止
- 任务达到 acceptance 或最终 handoff 条件后停止

## Boundary

- 这不是初始规划 skill；还没锁定 task dir / milestone 时，先回到 `ego-plan-from-spec`
- 这也不是单 milestone 实现 skill；它负责长程推进与持续记账
- 不创建第二套任务体系；已有 `Tasks/active/*.md` 只作为 authority refs 引入
