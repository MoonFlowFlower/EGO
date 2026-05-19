# E4 Shadow H1 Formal Mainline Sampling

## Goal

在不做 live decision promotion 的前提下，为 canonical `shadow_h1` 采集和审核 **formal Telegram mainline E4 shadow samples**，并且先用 clean-bind / contamination preflight 决定是否允许进入真实采样。

## Non-goals

- 不把 `shadow_h1` 直接接到 live `ask_preferred` / `ask_needed`
- 不改 scorer ontology
- 不比较 challenger
- 不升级 repo-level program state
- 不宣称 runtime efficacy、样本级生效以上的结论
- 不扩 replay suite、不新建 parallel runner 或 second authority source

## Constraints

- 边界约束：`Trial-1` / `Trial-2` 保持 closed, read-only evidence；当前 authority 只能是 canonical `proto_self` + formal Telegram mainline + `real_telegram/*/ledger.json`
- 仓库/子仓约束：EgoCore 只负责 host-owned feature flag、actual send、ledger/tape/replay；OpenEmotion 只负责 canonical `shadow_h1` telemetry
- 环境约束：live binding 模式固定为 `require clean commit`；若当前 Telegram poller 未绑定到 clean current commit，不允许开始采样
- 发布约束：本任务最多拿到 `E4 sample-level observation`；repo-level state 不变，不能写“已启用 / 已生效 / verified”

## Problem framing

- 当前问题表述：收集 real mainline `shadow_h1` 样本
- 归一化后的问题表述：先判断 formal sampling path 是否干净，再只对 canonical `shadow_h1 telemetry` 做 bounded E4 sample collection 和 evidence review
- 为什么这个 framing 更适合当前任务：当前最脆弱前提不是“有没有采样脚本”，而是 sampling path 是否被 `native_loop / runtime observation` 同表面问题污染，以及 live Telegram process 是否真的绑定到当前 H1 patch 版本

## Unknowns to eliminate

- 当前 live Telegram process 是否绑定到 clean current commit，并显式记录 H1 shadow rollout env
- H1-positive sample rows 是否必然经过当前仍不可信的 same-surface failure path
- 现有 `TelegramEvidenceCollector` + `real_telegram/*/ledger.json` 是否足以支撑 sample manifest / appearance / failures / final report，不需要新 harness

## Acceptance criteria

- [ ] 新建并填完 `docs/codex/tasks/e4-shadow-h1-formal-mainline-sampling/` 五件套与 frozen sample matrix
- [ ] 交付 clean-bind / contamination preflight tooling，并能输出 `continue` 或 `close`
- [ ] 若 preflight `close`，生成 `H1_E4_CAUSALITY_EXCLUSION_CURRENT.*` 或 `H1_E4_PREFLIGHT_CURRENT.*`，明确 blocker
- [ ] 交付 sample manifest / appearance / failures / final sample-level report 生成器，基于现有 `real_telegram/*/ledger.json` 读 authority 数据
- [ ] scoped tests、`py_compile`、`git diff --check`、`python3 scripts/codex/verify_repo.py --mode fast` 通过

## Disallowed premature claims

- `shadow_h1 runtime efficacy passed`
- `repo-level state should upgrade`
- `live decision promotion is enabled`
- `sample-level observation already proves stability`

## Known risks / dependencies

- 风险：当前 positive sample rows 使用显式路径 file-read prompts，天然贴近 `native_loop` surface；若该 surface 不干净，任务必须先停在 causality exclusion
- 依赖：`EgoCore/app/live_process_version.py`、`scripts/start_egocore_telegram_windows.ps1`、`TelegramEvidenceCollector`、`scripts/run_telegram_real_channel_capture.py`
- 外部 blocker：真实采样需要用户发送 Telegram 消息；当前工作树和 live process binding 若不 clean，也必须先停

## Authority refs

- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- `docs/CODEX_CLOSED_LOOP_SELF_REVIEW_WORKFLOW.md`
- `docs/codex/tasks/h1-canonical-promotion-prep/E4_SAMPLE_COLLECTION_PLAN.md`
- `docs/codex/tasks/h1-canonical-shadow-patch/STATUS.md`
- `docs/codex/tasks/e4-shadow-h1-formal-mainline-sampling/FROZEN_SAMPLE_MATRIX.json`
- `docs/TELEGRAM_REAL_MAINLINE_VALIDATION_V1.md`
