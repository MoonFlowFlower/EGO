# H1 Preflight Same-Surface Unblock - PLAN

## Task summary

这是一个 bounded implementation + proof slice。当前层级是 `实现 / 验证`，目标是在不恢复 sampling 的前提下，清除 H1 E4 formal sampling path 的 same-surface contamination，并把 clean-bind live process 重新绑到当前切片 `HEAD`。

## Execution mode

- mode: implementation
- why this mode: 主路径已经明确，当前主要工作是修 blocker、做 clean-bind automation、再跑 preflight proof
- proof required after discovery: 必须拿到 `native_path_surface pass + clean bind + preflight continue + causality-clear note`

## Milestones

### Milestone 1: Native blocker repair + clean-bind tooling

- type: implementation
- question: 当前 same-surface contamination 是否只来自 `test_native_loop` fixture drift，且能否用 temporary clean worktree 自动重建 clean-bind path
- current framing: 先修 scoped blocker，再做 clean-bind tooling；不碰 sampling
- hypotheses:
  - `FakeLLMClient` 缺 `generate_with_messages()` 是 `native_loop` 当前失败的最小根因
  - current repo root 太脏，必须使用 clean worktree + mirrored fileset 才能得到可信 preflight
- scope:
  - `EgoCore/tests/test_native_loop.py`
  - `scripts/codex/h1_e4_sampling_common.py`
  - `scripts/codex/run_h1_e4_sampling_preflight.py`
  - `scripts/codex/run_h1_clean_bind_cycle.py`
  - `scripts/start_egocore_telegram_windows.ps1`
  - `docs/codex/tasks/h1-preflight-same-surface-unblock/*`
- experiments planned:
  - rerun `native_loop` targeted pytest
  - py_compile + unit-test new clean-bind tooling
- kill criteria:
  - `native_loop` failure落到 production semantic bug，而不是 fixture drift
  - clean-bind 需要创建第二 authority source
- files / areas likely touched:
  - `EgoCore/tests/test_native_loop.py`
  - `EgoCore/tests/test_h1_e4_sampling_tools.py`
  - `scripts/codex/run_h1_clean_bind_cycle.py`
  - task docs
- acceptance:
  - `native_path_surface` tests pass
  - clean-bind script exists and can build causality-clear payload
- validation:
  - `python3 -m py_compile scripts/codex/run_h1_clean_bind_cycle.py scripts/codex/run_h1_e4_sampling_preflight.py scripts/codex/h1_e4_sampling_common.py EgoCore/tests/test_h1_e4_sampling_tools.py EgoCore/tests/test_native_loop.py`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_native_loop.py EgoCore/tests/test_telegram_bot_native_switch.py -q`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_live_process_version.py EgoCore/tests/test_h1_e4_sampling_tools.py -q`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note:
  - 若 clean-bind tooling 证明无法在 worktree 中维持 `git_dirty=false`，回退到 mirror-only trace integration proposal，不进入 live bind

### Milestone 2: Clean-bind execution + causality-clear proof

- type: implementation
- question: current H1 shadow slice 能否在 clean worktree 中真实启动 Telegram poller 并让 preflight 返回 `continue`
- current framing: live process 只用于 clean-bind provenance；不恢复任何 sample collection
- hypotheses:
  - mirrored fileset + ignored `.env` 足以在 clean worktree 上写出 `git_dirty=false` 的 live process report
  - 只要 `native_loop` same-surface blocker 消失，preflight 就会从 `close` 翻到 `continue`
- scope:
  - clean execution worktree lifecycle
  - live Telegram rebind
  - preflight rerun
  - causality-clear note
- experiments planned:
  - stop stale Telegram poller
  - start clean-bound Telegram poller from worktree
  - rerun preflight against worktree root
- kill criteria:
  - clean-bind cannot reach `git_dirty=false`
  - preflight still returns `close` due to same-surface contamination
- files / areas likely touched:
  - `artifacts/telegram_real_mainline_v1/reports/H1_E4_PREFLIGHT_CURRENT.*`
  - `artifacts/telegram_real_mainline_v1/reports/H1_E4_CAUSALITY_CLEAR_NOTE_CURRENT.*`
  - task docs
- acceptance:
  - preflight `decision=continue`
  - causality-clear note proves `native_loop` moved to `same_surface_cleared`
- validation:
  - `python3 scripts/codex/run_h1_clean_bind_cycle.py`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note:
  - 若 worktree poller 启动失败，杀掉 worktree PID，不恢复 sampling，不升级任何 repo-level 口径

## Progress

- current_status: Milestone 1 completed; Milestone 2 completed with refreshed clean-bind preflight `decision=continue` on current slice worktree `c256036`; task closeout reached
- current_milestone: Milestone 2 - Clean-bind execution + causality-clear proof
- milestone_state: closed
- candidate_vs_proof: proof_passed_for_preflight_clean

## Decision log

- 2026-04-09: 将 clean-bind authority 定位到 temporary clean execution worktree，而不是 dirty canonical root
- 2026-04-09: `native_loop` failure 被收敛为 test fixture drift，先修测试而不改 runtime semantics
- 2026-04-09: clean-bind script 采用 mirrored fileset + ignored `.env`，避免把 local-only slice 漏到 worktree 外
- 2026-04-09: `repo-root-guard` 增加显式 `EGO_REPO_ROOT + EGO_ALLOW_GIT_WORKTREE_ROOT` 授权路径；原因是 manual worktree startup 已证明旧 guard 会误杀合法 clean-bind root
- 2026-04-09: `live_process_version` 与 preflight dirty-path 分类同时引入 runtime-generated artifact allowlist；目标是把 tracked runtime side effects 从 code dirtiness 中剥离
- 2026-04-09: clean-bind runner 拉起 worktree Telegram 后，正式 preflight 直接对最新 worktree 重跑并收证；stop condition 是 `decision=continue`，不是 runner 自身必须优雅返回
- 2026-04-10: 发现旧 `H1_E4_PREFLIGHT_CURRENT.*` 仍绑定在旧 worktree `08d85c3`；因此按 authority 规则重跑 clean-bind 与 preflight，最新有效 worktree 切到 `ego_h1_clean_bind_20260410_002906` / `c256036`
- 2026-04-10: 最新 clean-bind 证据取回后，显式终止本轮 Telegram poller；Task A 只证明 preflight clean，不保留驻留进程

## Surprises / discoveries

- 新发现 1：`EgoCore/.env` 是 Telegram 启动所需 secret surface，但被 `.gitignore` 屏蔽，适合镜像进 clean worktree 而不污染 `git_dirty`
- 新发现 2：不少 H1/preflight 文件当前仍是 local-only；clean worktree 必须显式镜像并 local commit，不能只 trust `HEAD`
- 新发现 3：`egocore-telegram-poller.lock` 已经消失，clean-bind runner 现在能把 Telegram bot 启起来
- 新发现 4：最新 clean worktree `ego_h1_clean_bind_20260409_233520` 已写出可信 provenance：`repo_root`、`branch`、`git_commit_short` 都指向 worktree，且 `git_dirty=false`
- 新发现 5：`run_h1_clean_bind_cycle.py` 这轮拉起 Telegram 后，PowerShell start wrapper 没有及时返回；但这已不再影响 preflight 结论，属于后续 tooling hygiene
- 新发现 6：旧 preflight 报告虽然是 clean，但只覆盖到旧 worktree `08d85c3`；当前任务关闭前必须刷新到最新有效 worktree `c256036`
- 已排除路线 1：直接在 dirty canonical root 上追求 clean-bind
- 已排除路线 2：为了修 `native_loop` 去改 production contract runtime surface

## Outcomes / retrospective

- 本轮已证明：same-surface contamination 已被排除，外部 lock 不再是 blocker，clean worktree provenance 也已在最新切片 worktree 上成立
- 本轮已证明：`artifacts/telegram_real_mainline_v1/reports/H1_E4_PREFLIGHT_CURRENT.json` 已刷新为当前有效证据，报告 `decision=continue`、`clean_bind_ready=true`、`live_process_ok=true`，并绑定到 `ego_h1_clean_bind_20260410_002906` / `c256036`
- 本轮已证明：Task A stop condition 在当前有效 worktree 上再次满足；关闭 task 不再依赖旧 `08d85c3` 报告
- 本轮排除了什么：继续把 `git_dirty` runtime artifacts、old lock holder、canonical-root fallback，或旧 worktree 报告当成当前 blocker
- 下一步最小闭环动作：如果用户要继续，只重开 `e4-shadow-h1-formal-mainline-sampling`，在当前 clean preflight 前提上恢复正式 sample collection；本 task 到此关闭
