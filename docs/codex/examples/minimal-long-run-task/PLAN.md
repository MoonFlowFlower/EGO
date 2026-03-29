# Minimal Long-Run Task Example - PLAN

## Task summary

用一个只改文档/脚本的最小例子，演示长任务如何按 milestone 推进、验证、记账。

## Milestones

### Milestone 1: Confirm task structure

- scope: 检查四个任务文档是否齐全、authority refs 是否明确
- files / areas likely touched: `docs/codex/examples/minimal-long-run-task/`
- acceptance: 四个文档可读，`STATUS.md` 已锁定当前 milestone
- validation:
  - `python3 scripts/codex/verify_repo.py --mode fast --dry-run`
- rollback note: 若结构不清，先回到模板修正

### Milestone 2: Run unified verification

- scope: 用统一验证脚本输出当前仓库的 fast summary
- files / areas likely touched: `scripts/codex/verify_repo.py`
- acceptance: fast summary 有 success/skipped/failure 和清晰原因
- validation:
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note: 若命令探测失真，先修脚本，不扩到业务代码

## Progress

- current_status: ready_for_demo
- current_milestone: Milestone 1
- milestone_state: pending

## Decision log

- 2026-03-28: 示例任务保持 docs/script-only，避免把流程演示和业务代码混写。

## Surprises / discoveries

- 当前仓库的 smoke/e2e 能力主要来自 Telegram regression 与 OpenEmotion smoke/testbot，不是前端 UI。

## Outcomes / retrospective

- 本轮已证明：模板足以承载一个最小长任务
- 还没证明：跨天、跨 milestone 的真实持续推进效果
- 下一步最小闭环动作：跑一次 fast verifier 并把结果写进 `STATUS.md`
