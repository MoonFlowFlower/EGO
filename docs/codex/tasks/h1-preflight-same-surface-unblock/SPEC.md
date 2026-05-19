# H1 Preflight Same-Surface Unblock

## Goal

修复 `native_loop` 同面 blocker，恢复一个绑定到当前切片 `HEAD` 的 clean-bind Telegram live process，并产出 causality-clear note，证明 `shadow_h1` 的 E4 formal sampling path 不再被同面失败污染。

## Non-goals

- 不恢复任何 live/E4 shadow sampling
- 不升级 repo-level program state / evidence ledger
- 不改 scorer ontology
- 不做 H1 live decision promotion
- 不顺手修与本路径无关的 full-gate 残余失败

## Constraints

- 边界约束：`shadow_h1` 仍是 canonical proto_self 内的 shadow-only telemetry；EgoCore 只能记录，不能消费成 live decision input
- 仓库/子仓约束：不创建 parallel proto_self engine；Task A 只修 same-surface blocker 与 clean-bind path
- 环境约束：当前 canonical repo root 很脏，clean-bind 不能直接依赖原工作树；必须走 temporary clean execution worktree
- 发布约束：本任务只更新 task-doc 状态与 scoped tooling，不升级 repo-level state，不宣称 runtime efficacy

## Problem framing

- 当前问题表述：H1 E4 sampling preflight 被 `native_loop` 同面失败和 stale live bind 一起挡住
- 归一化后的问题表述：在不恢复采样的前提下，证明 frozen sampling path 的 same-surface blocker 已清，且 live Telegram process 可 clean-bind 到当前切片 `HEAD`
- 为什么这个 framing 更适合当前任务：目标不是证明 `shadow_h1` 有效，而是恢复可采样前提；因此最小闭环是 `native_path_surface -> clean bind -> preflight continue`

## Unknowns to eliminate

- `test_native_loop_runs_tool_call_and_returns_reply` 是 fixture drift 还是 runtime semantic regression
- clean worktree 是否能携带当前 local-only H1/preflight slice 而不污染 `git_dirty`
- clean-bind Telegram process 是否能在 current HEAD 上写出 `git_dirty=false` 的 live version report

## Acceptance criteria

- [x] `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_native_loop.py EgoCore/tests/test_telegram_bot_native_switch.py -q` 通过
- [x] temporary clean execution worktree 已创建，必要 H1/preflight slice 已镜像并提交到 worktree `HEAD`
- [x] worktree 内 `LIVE_TELEGRAM_PROCESS_VERSION.json` 记录 `git_commit_short == worktree HEAD` 且 `git_dirty == false`
- [x] `python3 scripts/codex/run_h1_e4_sampling_preflight.py --repo-root <worktree>` 返回 `decision=continue`
- [x] 产出 `H1_E4_CAUSALITY_CLEAR_NOTE_CURRENT.{json,md}`，明确 `native_loop: same_surface_blocking -> same_surface_cleared`

## Disallowed premature claims

- 不得宣称已恢复 E4 sampling
- 不得宣称 H1 runtime efficacy 或 repo-level enablement
- 不得把 clean-bind preflight clean 写成 live decision promotion

## Known risks / dependencies

- 风险：Windows Python / Telegram live bind 依赖本地 `.env` 与现有 Windows runtime
- 依赖：`EgoCore/.env`、`scripts/start_egocore_telegram_windows.ps1`、`EgoCore/app/live_process_version.py`
- 外部 blocker：若 clean worktree 启动仍受 `native_loop` / runtime observation 同面失败或 live bind mismatch 影响，本任务必须停在 causality-exclusion/clear note 层

## Authority refs

- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- `docs/CODEX_CLOSED_LOOP_SELF_REVIEW_WORKFLOW.md`
- `docs/codex/README.md`
- `docs/codex/tasks/e4-shadow-h1-formal-mainline-sampling/SPEC.md`
- `docs/codex/tasks/e4-shadow-h1-formal-mainline-sampling/PLAN.md`
- `docs/codex/tasks/e4-shadow-h1-formal-mainline-sampling/STATUS.md`
- `artifacts/telegram_real_mainline_v1/reports/H1_E4_CAUSALITY_EXCLUSION_CURRENT.json`
