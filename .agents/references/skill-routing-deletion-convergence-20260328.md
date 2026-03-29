# Skill Routing Deletion Convergence 2026-03-28

目标：检查根 `AGENTS.md` 与 6 个 skills 里是否还有可以继续合并删除、但不会削弱路由边界或执行流程的重复句子。

## Scope

- `AGENTS.md`
- `.agents/skills/ego-plan-from-spec/SKILL.md`
- `.agents/skills/ego-implement-milestone/SKILL.md`
- `.agents/skills/ego-bugfix-root-cause/SKILL.md`
- `.agents/skills/ego-review-against-acceptance/SKILL.md`
- `.agents/skills/ego-resume-context/SKILL.md`
- `.agents/skills/ego-handoff-brief/SKILL.md`

## Findings

### 1. The largest safe repetition was the reference-doc block

删除前：

- 6 个 skills 都重复列出
  - `.agents/references/engineering-evidence-model.md`
  - `.agents/references/task-state-and-handoff.md`

处理：

- 保留根 `AGENTS.md` 的 reference 入口
- 各 skill 改成统一一句：
  - `必要时再读根 AGENTS.md 引用的 repo reference docs。`

原因：

- 不改变技能行为
- 保留 discoverability
- 明显减少逐 skill 的重复 token

### 2. The numbered `先读` lists were longer than necessary

删除前：

- 6 个 skills 都使用 4 项以上的编号列表
- 实际内容高度相似，只是任务文档类型略有不同

处理：

- 压成每个 skill 一句 `先读：...`
- 保留差异化部分：
  - plan 仍点名 playbook
  - bugfix 仍点名 failure case / stack trace
  - resume 仍点名 evidence/status
  - handoff 仍点名 blocker/status

原因：

- 这些信息仍然必要
- 但编号列表本身不提供额外路由价值

### 3. Root references could be shorter without losing function

删除前：

- 根 `AGENTS.md` references 只是两个裸路径

处理：

- 改成两条更短、更语义化的标签：
  - 方法论与完成口径
  - 状态字段与 handoff

原因：

- 没有增加常驻长度
- 让 skill 中的“读根 AGENTS 引用的 reference docs”更可理解

## What Was Not Deleted

以下内容本轮刻意保留：

- skill description 中的冲突裁决句
  - 这些是当前隐式路由的关键边界
- 根 `AGENTS.md` 里的 mixed-intent routing rules
  - 这些是最近几轮压测新增的有效收敛结果
- 每个 skill 的 workflow 和 boundary 段
  - 这是执行差异真正存在的地方，不属于机械重复

## Result

结论：

- 还能安全删除的机械重复，已经基本删完
- 继续删减很可能会开始损伤路由可读性或任务边界
- 当前文档状态已经进入“薄但仍可执行”的平衡点

## Post-check

- 根 `AGENTS.md` 仍保持短协议
- 6 个 skills 仍然是一类任务一个 skill
- 没有发现必须继续合并的高价值重复句
