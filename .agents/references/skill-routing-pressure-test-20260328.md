# Skill Routing Pressure Test 2026-03-28

目标：用典型任务反向检查新的 repo `AGENTS.md` 与 `.agents/skills/` 是否会误路由，或把过多规则留在根协议常驻。

## Scope

- root `AGENTS.md`
- `.agents/skills/*/SKILL.md`
- `.agents/references/*`

## Findings Summary

结论：当前拆分方向正确，根 `AGENTS.md` 已足够薄，主要风险集中在 `ego-resume-context` 与其他具体任务 skill 的竞争。

本轮已修正：

- 根 `AGENTS.md` 增加优先级规则：
  - 若同一请求同时包含 `continue` 和明确 bug / milestone / review / handoff 目标，优先选择具体 task skill
- 收紧 5 个 skill 的 description，减少误触发：
  - `ego-plan-from-spec`
  - `ego-implement-milestone`
  - `ego-bugfix-root-cause`
  - `ego-review-against-acceptance`
  - `ego-resume-context`

## Reverse Pressure Cases

| Case | Example prompt | Expected route | Result |
|------|----------------|----------------|--------|
| 1 | `继续` | `ego-resume-context` | pass |
| 2 | `继续，把 SELF_AWARE_STEP_08A 的 Phase B 做完` | `ego-implement-milestone` | fixed |
| 3 | `继续，修复这个 failing test` | `ego-bugfix-root-cause` | fixed |
| 4 | `先规划 Proto-Self V3 迁移，别急着改代码` | `ego-plan-from-spec` | pass |
| 5 | `按这份 acceptance 把当前 milestone 实现掉` | `ego-implement-milestone` | pass |
| 6 | `review 当前未提交修改，看看能不能宣称完成` | `ego-review-against-acceptance` | fixed |
| 7 | `给我一份 subagent handoff brief` | `ego-handoff-brief` | pass |
| 8 | `把这个单文件 README typo 改掉` | no special skill; direct execution | pass |

## What Was Checked

### 1. Resume collision

问题：

- `continue` 类提示词很容易和 bugfix / implement / review 竞争

修正：

- 在 root `AGENTS.md` 明确了具体任务优先于 resume
- 在相关 skills 的 `description` 里补上了竞争边界

### 2. Planning vs implementing

问题：

- 原始 wording 对“已有 milestone 但用户想现在直接写代码”和“先做规划”之间的边界还不够尖锐

修正：

- `ego-plan-from-spec` 明确排除“已有明确 milestone 且用户要求现在编码”
- `ego-implement-milestone` 明确是 “implement that scoped slice now”

### 3. Review vs resume

问题：

- `看看现在算不算完成` 这类提示既像恢复上下文，又像验收 review

修正：

- `ego-review-against-acceptance` 明确在“resume-style + completion judgment”场景下优先于 `ego-resume-context`

### 4. Trivial edit over-trigger

检查：

- 小修小补、单文件简单修改，不应被强行套进 planning / milestone / bugfix / review 技能

结果：

- 当前 skill descriptions 都保留了足够窄的边界
- trivial edit 默认可直接执行，不需要 skill 常驻

## Root AGENTS Size Check

- current root `AGENTS.md`: `111` lines
- 内容只保留：
  - must-read
  - directory routing
  - real commands
  - acceptance / done
  - do-not rules
  - skill routing
  - short references

结论：

- 根协议没有再常驻旧版长流程
- 额外常驻内容目前不需要继续下压

## Remaining Risk

仍有一个可接受但未完全消除的灰区：

- 用户若同时写 `继续` + `先帮我规划` + `如果可以就顺手实现`

这类混合意图仍可能需要先做一次短澄清，或先按 `ego-plan-from-spec` 落最小 milestone，再进入实现。

## Recommended Rule

对混合提示，默认优先级：

1. explicit handoff
2. review against acceptance
3. bugfix root cause
4. implement milestone
5. plan from spec
6. resume context

只有当“恢复上下文”本身是主要工作时，才让 `ego-resume-context` 获胜。
