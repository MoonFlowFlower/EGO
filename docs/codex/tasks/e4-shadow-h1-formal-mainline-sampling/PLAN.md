# E4 Shadow H1 Formal Mainline Sampling - PLAN

## Task summary

当前任务是一个 `verification / observation` 型长任务：先做 `M0 clean-bind + contamination preflight`，只有 preflight 明确 `continue` 才允许进入 bounded live sampling；与此同时把 sample manifest / appearance / failures / final report 的工具链先落地，但不越过 stop rule。

## Execution mode

- mode: exploration
- why this mode: 当前关键未知是 sampling path 是否干净、正样本是否需要命中 same-surface residual failure；这比“把脚本写出来”更先决
- proof required after discovery: 需要 current live binding 证明、same-surface targeted checks、以及 real_telegram ledger-based report outputs

## Milestones

### Milestone 0: Clean-Bind And Contamination Gate

- type: exploration
- question: 当前 formal Telegram sampling path 是否干净到足以开始 H1 E4 shadow sampling
- current framing: 先把 live binding 和 same-surface contamination 变成 repo-tracked preflight report，再决定是否允许采样
- hypotheses:
  - 当前 positive H1 sample rows 依赖 `native_loop` / runtime observation surface
  - 只要 same-surface targeted checks 通过，历史 full-gate residual 可以降级成 monitored residual，而不是 stop reason
- scope:
  - 新建 task docs
  - 冻结 `FROZEN_SAMPLE_MATRIX.json`
  - 实现 `run_h1_e4_sampling_preflight.py`
  - 如需，输出 causality exclusion report
- experiments planned:
  - current HEAD vs `LIVE_TELEGRAM_PROCESS_VERSION.json`
  - tracked dirty-path inspection
  - targeted pytest slice
  - `python3 scripts/codex/verify_repo.py --mode fast`
- kill criteria:
  - live binding 不是 clean current commit
  - positive sample rows 仍依赖 failing `native_loop` / runtime observation surface
- files / areas likely touched:
  - `docs/codex/tasks/e4-shadow-h1-formal-mainline-sampling/*`
  - `scripts/codex/h1_e4_sampling_common.py`
  - `scripts/codex/run_h1_e4_sampling_preflight.py`
  - `EgoCore/app/live_process_version.py`
  - `scripts/start_egocore_telegram_windows.ps1`
- acceptance:
  - preflight report 明确给出 `continue` / `close`
  - 若 `close`，给出 blocker category 和 causality exclusion 口径
- validation:
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note:
  - 只回退 preflight/report tooling，不碰 canonical runtime behavior

### Milestone 1: Sample Manifest And Report Chain

- type: implementation
- question: 在不扩 sampling suite 的前提下，现有 `real_telegram/*/ledger.json` 能否支撑 H1-specific manifest / appearance / failures / final report
- current framing: 复用 `TelegramEvidenceCollector` 产生的权威 bundle；不把 dashboard_v1 当 authority
- hypotheses:
  - exact prompt-text + post-bind window 足以把 frozen sample rows 和 real samples 对齐
  - `openemotion_result.trace_payload.shadow_h1` 与 `confidence_meta.shadow_h1_*` 足以做 appearance report
- scope:
  - 实现 `build_h1_e4_sample_reports.py`
  - 交付 sample manifest / appearance / failures / final sample-level report
  - 新增 slice-local tests
- experiments planned:
  - fake sample bundle matching
  - positive vs negative control appearance extraction
- kill criteria:
  - 必须改 scorer ontology 才能产出 report
  - 必须新建第二 authority source 才能做 sample manifest
- files / areas likely touched:
  - `scripts/codex/h1_e4_sampling_common.py`
  - `scripts/codex/build_h1_e4_sample_reports.py`
  - `EgoCore/tests/test_h1_e4_sampling_tools.py`
- acceptance:
  - 4 份 report 工具链能从权威 sample bundle 生成结构化输出
  - negative control 与 positive row 的 appearance extraction 有最小测试覆盖
- validation:
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note:
  - 删除 H1-specific reporting scripts；real_telegram ledger 本体不受影响

## Progress

- current_status: sampling_admitted_but_external_operator_blocked
- current_milestone: Milestone 1: Sample Manifest And Report Chain
- milestone_state: blocked
- candidate_vs_proof: proof_pending

## Decision log

- 2026-04-09: live binding 模式冻结为 `require clean commit`；原因是 user 已选 clean-bind rule；影响是 dirty-tree live sampling 一律不准开始
- 2026-04-09: positive sample rows 固定用显式路径 file-read prompts；原因是要最大化 `tool:file` 家族上 `shadow_h1` 的可见性；影响是 preflight 必须显式审查 `native_loop` surface
- 2026-04-09: `real_telegram/*/ledger.json` 是样本 authority，dashboard_v1 只作 derived diagnostics；影响是 report chain 直接读 sample bundles，不读 dashboard flow detail
- 2026-04-09: `run_h1_e4_sampling_preflight.py` 首轮结论为 `close / causality_exclusion`；原因是 `native_path_surface` same-surface blocker 仍存在，且 live Telegram process 也未 clean-bind 到当前 `HEAD`
- 2026-04-09: `h1-preflight-same-surface-unblock` 已把 same-surface blocker 与 clean-bind provenance 清到 `decision=continue`；影响是本任务恢复 admission，可以进入 bounded sample matching / live sampling 准备
- 2026-04-09: `build_h1_e4_sample_reports.py` 现在跟随 preflight 的 `evaluated_repo_root` 读取 authority bundles；原因是 clean-bind live sampling 真实发生在 temporary worktree，不在 canonical root

## Surprises / discoveries

- 新发现 1：当前 `LIVE_TELEGRAM_PROCESS_VERSION.json` 记录的是 `2b56ee6` 且 `git_dirty=true`，并不等于当前 repo `HEAD`
- 新发现 2：当前 repo tracked worktree 本身并不 clean，clean-bind preflight 会先卡在 provenance，而不是先卡在 sample tooling
- 新发现 3：same-surface blocker 已定位到 `EgoCore/tests/test_native_loop.py::test_native_loop_runs_tool_call_and_returns_reply`，失败原因为 `FakeLLMClient` 缺少 `generate_with_messages`
- 已排除路线 1：直接在 dirty live process 上采样，再事后口头补 provenance
- 已排除路线 2：复用 dashboard_v1 作为 sample authority source
- 新发现 4：admitted preflight 之后，current authority 里仍然 `0/4` 命中 frozen prompts；因此当前 blocker 已收敛为 external operator ingress 缺失，而不是 report chain 或 same-surface 污染
- 新发现 5：browser-side operator probe 不可用，当前内建工具里也没有可替代真实 `user -> bot` ingress 的 operator harness

## Outcomes / retrospective

- 本轮已证明：preflight gate 已恢复，same-surface contamination 已排除，clean-bind Telegram live process 能绑定到 current clean worktree `HEAD`
- 本轮已证明：H1 sample report chain 已能直接跟随 admitted clean worktree source root 读取 authority bundles，不需要复制 artifacts
- 还没证明：任何 `shadow_h1` formal mainline E4 sample-level observation，更没有 runtime efficacy
- 本轮排除了什么：dirty-tree blind sampling、dashboard-derived authority、在 unresolved native-loop blocker 上继续采样
- 下一步最小闭环动作：由真实 Telegram operator 从授权 DM 发送 frozen sample matrix 的 prompts，再重跑 report builder
