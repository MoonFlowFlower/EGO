# Active-Inference Mainline Activation - EXPLORE

> 仅在 research / verify / observation / proof / high-unknown 任务中强制使用。
> 每次实验后必须先更新本文件，再开始下一轮。

## Exploration mode

- enabled: `yes`
- why exploration mode is needed:
  - 当前不再缺 Stage 1/2 authority truth-sync；剩余未知是 Stage 3 最小 gate 怎样在不越过 claim ceiling 的前提下被冻结并进入后续验证
- current framing:
  - 当前 formal mainline、Stage 1、Stage 2、以及 comparative audit truth-sync 都已冻结；Stage 3 真正缺的是 dashboard-only / single-entry gate definition 与后续 fresh validation
- success looks like:
  - 能把“聊天更像主体”冻结成不越界的 conversational-stance/continuity gate
  - repo authority 与 task package 明确写清 gate definition 已冻结、Stage 3 仍 `pending_validation`
- disallowed premature claims:
  - 不把 gate definition 冻结说成 Stage 3 proof
  - 不把 tendency hints 或 dashboard-only evidence 说成 runtime efficacy、broad user benefit 或 consciousness

## Question reformulation

- original question:
  - Stage 3 的“聊天更像主体”应该怎样写成 truthful gate，且不越过当前 claim ceiling
- normalized question:
  - 如何把现有 dashboard-only Stage 1/2 evidence 收成一条可验证但未过证的 Stage 3 gate definition
- why this framing is better:
  - 它直接对应当前 program 的唯一剩余阶段，而不是回退到 Stage 1 排障或继续做 summary-only cleanup

## Hypotheses

### Hypothesis 1

- statement:
  - 现有 fresh same-session `dashboard_chat` 窗口已经足够支撑一条 Stage 3 最小 gate definition，不需要新增 runtime 机制或 scorer ontology
- why plausible:
  - 当前 comparative audit 已 truth-sync，且 fresh Stage 2 export 已同时满足 `mainline_candidate`、`host_only_count = 0`、`degraded_count = 0` 与 `non_ask/respond` tendency
- kill criteria:
  - 若定义 gate 必须依赖 cross-entry promotion、authority release、或更强 benefit wording，则当前 Stage 3 framing 失效
- smallest experiment:
  - 读取当前 authority files 与 latest fresh same-session dashboard evidence，检查是否能冻结最小成立/不成立条件

### Hypothesis 2

- statement:
  - 当前 task package 漂移仍主要在文档/执行规则，而不是证据面本身
- why plausible:
  - `IMPLEMENT.md` 仍锁在 Stage 1，`EXPLORE.md` 仍把核心问题表述成 Stage 1 排障
- kill criteria:
  - 若 authority/task package 已完全对齐 Stage 3 gate-definition-only 口径，则无需继续 truth-sync
- smallest experiment:
  - 读取 `PLAN.md / STATUS.md / IMPLEMENT.md / EXPLORE.md / OVERALL_PROGRESS.md / stage_scorecard.json`

## Experiment log

### Cycle 01

- question:
  - pre-runtime early return 是否真的在 subject ingress 之前截断了主链
- framing used:
  - 先查 formal runtime path，而不是先假设 pre-runtime 是根因
- experiment:
  - 读 `telegram_bot._handle_with_runtime_v2()`、`telegram_runtime_bridge.plan_pre_runtime()`、以及 `test_runtime_v2_pre_runtime_early_return_attempts_subject_ingress_first`
- command / script / artifact:
  - source read + existing regression inspection
- observed result:
  - current path 会先调用 `_ensure_runtime_v2_subject_ingress()`，随后才进入 `_maybe_handle_runtime_v2_pre_runtime()`
- what it proves:
  - Stage 1 不应把“推翻 pre-runtime”当主方案
- what it does not prove:
  - 不证明 fresh live Telegram ordinary chat 已稳定进入主体
- what path is ruled out:
  - “直接关闭 pre-runtime intercept 才能推进 Stage 1”
- decision for next step:
  - 保留高风险 intercept，转去补 Stage 1 metadata 与 audit accounting

### Cycle 02

- question:
  - 当前 `unexpected_subject_miss` 列表里是否混有 policy/control-plane 类 host-only 样本
- framing used:
  - 不改 baseline counts，先做 supplemental isolation
- experiment:
  - 抽查 `runs.jsonl` 中 ordinary-chat host-only 且 `response_plan_status in {pre_runtime, delivered_without_explicit_plan, chat, evidence_followup}` 的样本，再读对应 `raw_update.json / response_plan.json`
- command / script / artifact:
  - ad-hoc sample inspection against `artifacts/telegram_real_mainline_v1/real_telegram/*`
- observed result:
  - miss 列表中确有旧 `delivered_without_explicit_plan` 的 profile rule registration / enforcement 样本，以及 `pre_runtime` 的高风险 preflight 样本
- what it proves:
  - Stage 1 需要一个 supplemental lens 把 `policy-isolated ordinary-chat host-only` 与 `mainline-candidate unexpected miss` 分开
- what it does not prove:
  - 不证明 fresh audit 窗口已经改善
- what path is ruled out:
  - “沿用当前 miss 列表直接当 Stage 1 acceptance root”
- decision for next step:
  - 为 pre-runtime intercept 增加 metadata，并在审计里加 Stage 1 activation lens

## Framing changes

- 2026-04-12: `post-stronger frontier reframing` -> `active-inference mainline activation / Stage 1 subject-ingress stabilization` / 原因：用户已把真实目标切到真实通道闭环 program / 影响：停止继续 aggregate planning，开始主线接线与审计隔离
- 2026-04-12: `Stage 1/2 truth-sync` -> `Stage 3 gate definition freeze` / 原因：当前 cleaned dashboard-only authority surface 已足够定义最小 conversational-stance/continuity gate，而当前真正缺口已变成 fresh validation / 影响：不再回退到 Stage 1 排障，task package 全面切到 gate-definition-only 口径

## Candidate vs proof

- candidate_found:
  - `active-inference` 已是 durable build-first winner，且当前最小可执行切片是 Stage 3 gate definition freeze
- proof_pending:
  - fresh same-session `dashboard_chat` Stage 3 gate validation
- proof_passed:
  - `Stage 1 closeout`
  - `Stage 2 tendency closeout`
  - `Stage 2->3 admission-boundary truth-sync`
- remaining proof gap:
  - current repo edits 只能完成 gate-definition-only truth-sync，不能替代 fresh same-session `dashboard_chat` validation
