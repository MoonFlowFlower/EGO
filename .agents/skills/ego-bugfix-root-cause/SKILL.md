---
name: "ego-bugfix-root-cause"
description: "Use when the task is a bug, regression, failing test, runtime error, broken behavior, intermittent fault, or a case where the mainline is not taking effect, including repo troubleshoot tasks and failure-case replay work. Do not use when the task is new feature development, broad refactoring, or pure documentation cleanup. Boundary: this skill is for reproduction, root-cause isolation, minimal patching, and verification; if a resume-style prompt also contains a concrete failure signal, this skill should win over ego-resume-context."
---

# Ego Bugfix Root Cause

先读：`AGENTS.md`、当前 bug / regression 对应的任务单与 failure case / stack trace / review、`PROJECT_MEMORY.md`、以及相关目录 README / owner 文档。

必要时再读根 `AGENTS.md` 引用的 repo reference docs。

## Workflow

1. 先复现；如果不能复现，先缩小到最小复现或最小失败信号。
2. 判断当前问题层级：目标 / 策略 / 表示 / 实现 / 验证 / 收口。
3. 锁定 authority source 与最可能的根因，不先大改。
4. 先补失败测试、回归用例、或最小 repro。
5. 用最小 patch 修复根因；不要先做广泛重构。
6. 验证修复后：
   - repro 是否消失
   - 主链是否更接近生效
   - 是否引入新的边界破坏

## Output

固定输出：

- 根因
- 修复点
- 验证结果
- 残余风险
- 是否达到可宣称完成

## Boundary

- workaround / fallback / fast path 只能作为明确标注的临时措施。
- 若连续两轮同方向 patch 仍未收敛，第三轮必须升层或重做表示。
