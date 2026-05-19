# E4 Shadow H1 Formal Mainline Sampling - EXPLORE

> 仅在 research / verify / observation / proof / high-unknown 任务中强制使用。
> 每次实验后必须先更新本文件，再开始下一轮。

## Exploration mode

- enabled: yes
- why exploration mode is needed: 当前未知不是功能实现，而是 formal sampling path 是否干净、live provenance 是否可证明
- current framing: 先做 preflight + same-surface contamination diagnosis，再决定是否允许 bounded real sampling
- success looks like: preflight 明确给出 `continue` 或 `close`，且样本 report 工具链已经可用
- disallowed premature claims:
  - `shadow_h1 runtime efficacy passed`
  - `E4 sample collection completed`（在 preflight 未放行前）
  - `repo-level state should upgrade`

## Question reformulation

- original question: 收集 E4 shadow_h1 formal mainline 样本
- normalized question: 当前 formal Telegram mainline 是否已经具备可信 provenance 和可信 surface，足以让 E4 shadow_h1 样本进入账本
- why this framing is better: 它先处理 stop condition，而不是在坏路径上机械采样

## Hypotheses

### Hypothesis 1

- statement: 当前 positive sample rows 的关键 surface 是 `native_loop + runtime_v2/proto_self_runtime + telegram_evidence_collector`；如果这个表面通过 targeted checks，就不必因为历史 full-gate residual 自动停机
- why plausible: 当前 explicit-path execute turn 会选择 `native_loop`，但同表面的 targeted tests 可以直接证明它是不是 blocker
- kill criteria: `native_path_surface` 或 `runtime_mainline_observation` scoped check 失败
- smallest experiment: 跑 `run_h1_e4_sampling_preflight.py`

### Hypothesis 2

- statement: `real_telegram/*/ledger.json` 已足够做 H1-specific manifest / appearance / failures / final report，不需要改 dashboard scorer ontology
- why plausible: ledger 已保存 raw/update/result/plan/outbox/timeline/tape/replay，`shadow_h1` 位于 canonical result trace payload 内
- kill criteria: report chain 需要读取 dashboard-only 字段或需要改 scorer ontology 才能成立
- smallest experiment: 用 fake sample bundles 跑 `build_h1_e4_sample_reports.py` 的纯工具链测试

## Experiment log

### Cycle 01

- question: 当前任务应该先采样，还是先做 live bind / contamination gate
- framing used: preflight-first
- experiment: inspection of current `LIVE_TELEGRAM_PROCESS_VERSION.json` + tracked dirty paths + existing same-surface task history
- command / script / artifact:
  - `git rev-parse --short HEAD`
  - `git status --short --untracked-files=no`
  - `EgoCore/artifacts/proto_self_v2/LIVE_TELEGRAM_PROCESS_VERSION.json`
  - `docs/codex/tasks/h1-canonical-shadow-patch/STATUS.md`
- observed result: live process commit 与当前 repo HEAD 不一致，且 `git_dirty=true`；当前正样本又依赖 `native_loop` surface，因此直接采样不成立
- what it proves: 当前 first action 必须是 clean-bind / contamination preflight
- what it does not prove: 当前 `native_loop` surface 一定仍坏；还需要 targeted checks
- what path is ruled out: 直接在 dirty live process 上做 E4 sample capture
- decision for next step: 实现 preflight script、report chain 和 frozen sample matrix

### Cycle 02

- question: 当前 sampling path 在 actual targeted checks 下是否已经干净到足以进入 bounded E4 sample collection
- framing used: preflight gate with same-surface blocker classification
- experiment: `python3 scripts/codex/run_h1_e4_sampling_preflight.py`，并单独复跑 `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_native_loop.py EgoCore/tests/test_telegram_bot_native_switch.py -q -vv`
- command / script / artifact:
  - `artifacts/telegram_real_mainline_v1/reports/H1_E4_CAUSALITY_EXCLUSION_CURRENT.json`
  - `artifacts/telegram_real_mainline_v1/reports/H1_E4_CAUSALITY_EXCLUSION_CURRENT.md`
- observed result: preflight 给出 `decision=close`、`report_kind=causality_exclusion`；`runtime_mainline_observation` 已通过，但 `native_path_surface` 失败，且 positive H1 sample rows 需要 `native_loop` surface；live process 仍记录为旧 commit 且 `git_dirty=true`
- what it proves: 当前 formal sampling path 受 same-surface `native_loop` blocker 污染，任务必须停在 causality exclusion；`shadow_h1` 还不能进入 E4 sample ledger
- what it does not prove: canonical `shadow_h1` telemetry patch 无效；也不证明 runtime efficacy
- what path is ruled out: 在 unresolved `native_loop` blocker 和 dirty live binding 上继续收集 Telegram E4 样本
- decision for next step: close current task at preflight；把 `native_loop` same-surface failure 作为独立 bugfix authority source

## Framing changes

- 2026-04-09: `collect E4 samples now` -> `preflight gate first` / 原因是 live bind mismatch + same-surface risk / 影响是当前任务先实现 preflight/report tooling

## Candidate vs proof

- candidate_found: canonical `shadow_h1` 已经具备进入 formal Telegram sample bundle 的最小 surface
- proof_pending: none in this task; current task closed before sample admission
- proof_passed: none
- remaining proof gap: clean-bound live Telegram process、cleared `native_loop` same-surface path、actual E4 sample presence
