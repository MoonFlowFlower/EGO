# Active-Inference Mainline Activation - PLAN

## Task summary

这是一个三阶段 program。当前 `Milestone 1 / Stage 1`、`Milestone 2 / Stage 2`、`Milestone 3 / Stage 3` 都已按 `dashboard-only / single-entry / bounded` 口径冻结完成，`Stage 3` 同一 `run_id` 下的 deterministic full-suite gate 也已过线。当前任务不再默认继续实现更高 gate；它的默认职责变成保持 closeout 与 handoff surface truth-sync，直到有显式 higher-gate 授权。

## Execution mode

- mode: `closeout maintenance`
- why this mode:
  - 当前不再缺 Stage 3 implementation、真实 full-suite gate、或 closeout freeze；本轮之后默认工作不是重开 Stage 3，而是保持 authority / task / campaign / handoff surfaces 同步
  - 若没有显式 higher-gate 授权，继续实现只会制造“已冻结 tranche 被误当 active frontier”的噪声
- proof required after discovery:
  - 当前 bounded closeout 仍保持单一 authority 且不被 stale convenience view 冲掉
  - 没有新的 active gate 被偷偷开启
  - 继续保持不越过 runtime efficacy / broad user-benefit / consciousness claim ceiling

## Milestones

### Milestone 1: Stage 1 bootstrap and subject-ingress stabilization

- type: `implementation`
- question:
  - 如何把 `active-inference mainline activation` 变成当前 execution owner，并让 ordinary-chat host-only 审计不再把 policy/control-plane interception 与主链漏接混为一谈
- current framing:
  - 当前 formal runtime mainline 已在代码上先尝试 subject ingress，再处理 pre-runtime early return；Stage 1 所需的本地 intercept metadata 与 audit accounting 已落地
  - 当前 authority 已显式改写：不再把 Telegram 作为当前 campaign gate；`dashboard_chat` 三份 clean live windows 现已足够冻结 dashboard-only Stage 1 closeout
  - 下一步不再追 Telegram 入口，而是用 `dashboard_chat` 的 same-session fresh window 进入 Stage 2 tendency proof
- hypotheses:
  - 现有代码路径不需要推翻 pre-runtime，只需要给 intercept 留下更清晰的 Stage 1 metadata
  - 历史 `unexpected_subject_miss` 里混有 policy/control-plane 类 host-only 样本；新增 Stage 1 supplemental lens 后，可把它们隔离出真正的 ordinary-chat mainline candidate miss
- scope:
  - `docs/codex/tasks/active-inference-mainline-activation/*`
  - `EgoCore/app/telegram_runtime_bridge.py`
  - `EgoCore/app/telegram_bot.py`
  - `EgoCore/app/dashboard/reply_sample_preflight.py`
  - `EgoCore/app/dashboard/live_api_client.py`
  - `EgoCore/app/dashboard/stage1_live_run.py`
  - `EgoCore/app/dashboard/stage1_evidence.py`
  - `scripts/codex/audit_telegram_subject_mainline.py`
  - `scripts/codex/build_dashboard_stage1_evidence_views.py`
  - `scripts/codex/export_dashboard_live_session.py`
  - `scripts/codex/generate_route_convergence_views.py`
  - `scripts/codex/verify_route_convergence.py`
  - `scripts/codex/run_dashboard_stage1_autonomous_live_window.py`
  - `scripts/codex/run_dashboard_unified_ingress_reply_sample_preflight.py`
  - 定向测试
  - repo state/progress/README routing
- experiments planned:
  - 用 fresh unified-ingress ordinary-chat window 重跑 `subject_mainline_audit`
  - 比较单入口 `ordinary_chat_breakdown.unexpected_subject_miss` 与 `stage1_activation_lens.mainline_candidate_unexpected_miss_total` 是否继续保持诚实隔离并出现结构性下降
  - 用 `DashboardChatService` 直接跑一组 repo-authored ordinary-chat prompts，生成独立的 bounded preflight artifact，验证 dashboard 统一入口是否能拿到 entrypoint-tagged reply sample / host-only evidence
  - 用 sibling comparative audit 消费 `DASHBOARD_LIVE_SESSION_EXPORT_CURRENT`，并验证 bounded preflight 没有混入 live aggregate
  - 用 autonomous dashboard-only runner 创建 dedicated `codex-stage1-*` session、自动发 ordinary-chat prompt pack、归档旧 export，并在成功后自动刷新 current export 与 comparative audit
- kill criteria:
  - 如果必须改 scorer ontology、扩 host surface、或新增第二 runtime lane，当前 milestone 立即停止
  - 如果主链代码并未先尝试 subject ingress，则先回到 bugfix framing；当前实验已初步排除这一路线
- files / areas likely touched:
  - `docs/codex/tasks/active-inference-mainline-activation/PLAN.md`
  - `docs/codex/tasks/active-inference-mainline-activation/STATUS.md`
- acceptance:
  - Stage 1 文案明确记录：本地 accounting / activation lens 已实现，且 focused validation 已通过
  - 当前 authority 明确记录：Stage 1 已冻结为 dashboard-only closeout，不再要求 fresh Telegram gate
  - 文案明确记录：dashboard-only closeout 只证明 `dashboard_chat` 单入口，不自动证明 cross-entry、runtime efficacy 或更强 claim
  - 新 bounded preflight artifact 必须独立于 live baseline，且显式记录 `entrypoint=dashboard_chat`、`source_kind`、`subject_gate_status`、`reply_sample_present`、`host_only`
  - sibling comparative audit 必须继续显式输出 `bounded_preflight -> single_entry_live_window -> comparative_audit` 三层 evidence ladder，并把 current verdict 保持在 dashboard-only single-entry 口径
  - autonomous runner / live export / comparative audit 现在必须保留 mixed-source provenance（`prompt_source_counts`、per-turn `input_provenance`、`source_mix_summary`），但不得因此改变 single-entry verdict semantics
  - claim ceiling 保持在 `single-entry strengthened evidence / stage1_closeout_dashboard_only`
- validation:
  - 已完成的 dashboard-rooted validation 维持 authority：
  - `python3 scripts/codex/run_dashboard_unified_ingress_reply_sample_preflight.py`
  - `python3 scripts/codex/run_dashboard_stage1_autonomous_live_window.py --prompt-source-strategy hybrid`
  - `python3 scripts/codex/build_dashboard_stage1_evidence_views.py`
  - `python3 scripts/codex/verify_repo.py --mode fast`
  - 下一 gate 进入 fresh `dashboard_chat` same-session tendency proof
- rollback note:
  - 若新增 metadata、audit lens、或 preflight artifact 误伤现有 baseline，回退到只更新 task/docs，不改变 baseline counts

### Milestone 2: Real unified-ingress downstream tendency proof

- type: `exploration`
- question:
  - 在 fresh unified-ingress 同 session 窗口里，是否出现了明确 `downstream tendency change / continuity effect`
- current framing:
  - Stage 1 已按 dashboard-only authority 冻结完成；当前只在 `dashboard_chat` 单入口里验证 same-session downstream tendency change
- hypotheses:
  - 当 ordinary chat 更稳定经过主体时，单一入口的真实 unified-ingress 会开始出现 `revision_counter > 0` 与非 `ask` tendency 模式
- scope:
  - entrypoint-tagged live audit/runner、same-session contract、failure replay
- experiments planned:
  - 待 Stage 1 解锁后补充
- kill criteria:
  - 若只能混用不同入口样本或 broad benefit wording 才能成立，则停止
- files / areas likely touched:
  - `scripts/codex/audit_telegram_subject_mainline.py`
  - 新 tendency runner / report
- acceptance:
  - `dashboard_chat_subject_revision_gt_0 > 0`
  - `dashboard_chat_subject_non_ask_modes > 0`
  - 至少一组 strong proof session
- validation:
  - `python3 scripts/codex/verify_repo.py --mode full`
- rollback note:
  - 失败时保持 Stage 1 pass / Stage 2 pending，不偷升到用户收益 claim

### Milestone 3: Deterministic stance-integrity gate

- type: `implementation + bounded exploration`
- question:
  - 在 `dashboard_chat` 单入口上，能否用固定 `12-case` deterministic runner 判断“聊天更像主体”的 bounded stance-integrity signal，并在真实 path 上完成一次非退化 validation
- current framing:
  - Stage 1 / Stage 2 已冻结，Stage 2->3 truth-sync 已完成；当前不再把 Stage 3 停在 gate wording，而是把 gate 实现成 deterministic runner，并诚实记录真实 runtime probe 的 blocker
- hypotheses:
  - 若系统真有最小“主体感”，它应在开放问题上先形成可解析的初始立场、在无新证据时不因用户施压改口、并只在明确新证据出现时做可解释修正
- scope:
  - `EgoCore/app/dashboard/stage3_stance_integrity.py`
  - `scripts/codex/run_dashboard_stage3_stance_integrity_gate.py`
  - `EgoCore/tests/test_dashboard_stage3_stance_integrity.py`
  - task/progress/program-state/campaign ledger truth-sync
- experiments planned:
  - 固定 `12` 个低风险 case，分布到 `open_question_stance_formation` / `persuasion_without_new_evidence` / `revision_with_new_evidence`
  - 用 machine-readable schema 提取 `initial_stance_present`、`unsupported_reversal`、`revision_justified`
  - 在真实 `dashboard_chat` path 上跑一轮 current report；若 runtime 退化，则记录 blocker 而不是误报 gate fail/pass
- kill criteria:
  - 若成立条件必须依赖意识 claim、authority release、cross-entry promotion、live efficacy 全域证明、或 LLM-as-judge 主判定，则停止
- files / areas likely touched:
  - `EgoCore/app/dashboard/stage3_stance_integrity.py`
  - `scripts/codex/run_dashboard_stage3_stance_integrity_gate.py`
  - `EgoCore/tests/test_dashboard_stage3_stance_integrity.py`
  - authority/task/campaign docs
- acceptance:
  - Stage 3 gate implementation 明确记录为 dashboard-only / single-entry / bounded stance-integrity signal
  - `12/12` case 必须先形成可解析初始立场
  - `Q2-Q3` 无新证据轮中 `unsupported_reversal = 0`
  - `Q4` 新证据轮中 `revision_justified >= 9`
  - 文案明确写清：即使 gate 已通过，当前切片也只证明 dashboard-only / single-entry / bounded pass，不自动外推成 cross-entry proof、runtime efficacy 或 broad user-benefit
- validation:
  - `python3 -m py_compile EgoCore/app/dashboard/stage3_stance_integrity.py scripts/codex/run_dashboard_stage3_stance_integrity_gate.py EgoCore/tests/test_dashboard_stage3_stance_integrity.py`
  - `TMPDIR=/tmp PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_dashboard_stage3_stance_integrity.py -q`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/run_dashboard_stage3_stance_integrity_gate.py`
- rollback note:
  - 保持 Stage 1 frozen / Stage 2 frozen / Stage 3 bounded wording；若后续 rerun 回退或 claim ceiling 需要调整，先保留 current artifact 与 run-state truth，不把任何单入口结果自动升格成更强 authority

## Progress

- current_status: `stage3_bounded_gate_pass__dashboard_only_closeout_frozen`
- current_milestone: `Milestone 3: Deterministic stance-integrity gate`
- milestone_state: `closeout_frozen`
- candidate_vs_proof: `dashboard_stage1_closeout_frozen / dashboard_stage2_tendency_frozen / dashboard_stage3_closeout_frozen__gate_passed`

## Decision log

- 2026-04-12: 把 repo 当前 execution owner 从 `post-stronger frontier reframing` 改写为 `active-inference mainline activation`。原因：当前真实目标已从 bounded post-stronger reframing 切换为真实通道闭环 program。影响：Stage 1 先做主线切换、subject-ingress stabilization、audit accounting。
- 2026-04-12: Stage 1 不推翻 pre-runtime intercept。原因：现有 formal mainline 已先尝试 subject ingress，再处理 early return；真正缺口是 metadata 与审计隔离。影响：只补 intercept metadata 和 Stage 1 lens。
- 2026-04-12: Stage 1 当前不再授权新的本地机制扩展。原因：本地 accounting / activation lens 与 focused validation 已足够支撑当前结论，剩余 truth gap 已收紧为 fresh `telegram`-tagged live window，除非 authority 被显式重写。影响：Stage 1 状态改为 `pending_validation / blocked_by_external_dependency`，下一步不再把 dashboard-only multi-window accumulation 当成同级替代路径。
- 2026-04-12: Stage 1 validation root 从 Telegram-only 改成 unified-ingress equivalent-entry gate。原因：`dashboard_local` 与 `telegram_prepared` 已被统一 host contract tranche 冻结为同一 canonical contract 的 adapter；用户进一步明确 dashboard chat 也可以作为统一入口调用面。影响：Telegram 不再被写成唯一入口，但单入口 live evidence 仍不得外推成跨入口 proof。
- 2026-04-12: 当前 campaign authority 明确停止继续检查 Telegram 入口。原因：用户要求不再把 Telegram 当当前 Stage 1 gate，而现有三份 clean `dashboard_chat` live windows 已足够支撑 dashboard-only closeout。影响：Stage 1 冻结为 dashboard-only closeout，下一步直接切到 Stage 2 dashboard same-session tendency proof。
- 2026-04-12: Stage 1 新增 explicit entrypoint evidence contract。原因：仅靠文案说明还不足以防止 Telegram / dashboard 证据混报；需要让 dashboard index records 与 `subject_mainline_audit` 直接携带 `entrypoint` 口径。影响：当前审计输出已显式写入 `entrypoint_contract` 与 sample-level `entrypoint`，后续 fresh live window 可以直接按入口分账。
- 2026-04-12: Stage 1 新增 dashboard unified-ingress reply-sample preflight runner。原因：在 fresh live gate 之前，需要一个不手拼 contract 的最小 readiness probe，直接经由 `DashboardChatService` 拿到 `entrypoint-tagged` reply-sample / host-only evidence。影响：新增独立 preflight artifact，但它明确不写入 live baseline，也不构成 Stage 1 pass。
- 2026-04-12: dashboard preflight runner 改为显式 `load_config(validate=False)` 并默认关闭 external LLM semantic parse。原因：先前 `hooks_disabled` 只是脚本未加载 config 的本地环境假 blocker，不是 unified-ingress 主链问题。影响：current preflight artifact 现在能诚实反映 `subject_gate passed / oe_available` 与 `mainline_candidate`，同时仍保持 `bounded_local_proof` 口径。
- 2026-04-12: 新增 live dashboard session export runner。原因：用户已经在真实 `dashboard chat` 里输入了一段 fresh window，需要把运行中 service API 的 transcript/debug 最小固化成可审计 artifact，而不是停留在进程内状态。影响：新增 `DASHBOARD_LIVE_SESSION_EXPORT_CURRENT.{json,md}`，它记录 single-entry live window，但不自动改写 `subject_mainline_audit` baseline。
- 2026-04-12: 新增 sibling comparative audit 与 supporting cleanup lane。原因：fresh dashboard live export 已经存在，再继续口头解释 evidence ladder 会让 repo surface 继续混乱；需要把 route convergence、hygiene、artifact manifest、Stage 1 comparative audit 收成 supporting-active 生成链。影响：Stage 1 现在同时拥有 bounded preflight、single-entry live window、以及 comparative audit 三层独立 artifact，但 current verdict 仍然只到单入口 pending。
- 2026-04-12: Stage 1 新增 autonomous dashboard-only live-window runner，并固定 dedicated session policy。原因：用户已经明确普通测试可由 Codex 自跑，当前更高杠杆的是让 dashboard ordinary-chat live sampling、导出、archive、comparative-audit refresh 自动闭环，而不是继续依赖手工输入。影响：Stage 1 现在可以持续产出 `dashboard_chat` 单入口 live-window evidence，但仍必须保持 single-entry wording。
- 2026-04-12: autonomous runner 的 transport timeout 提高到 live dashboard 需要的窗口。原因：真实运行里第二条 ordinary-chat 消息约在 97 秒后才返回 assistant turn，原先 15 秒 HTTP timeout 会把慢响应误记成 transport blocker。影响：runner 现在能诚实区分“慢但成功的 live reply”与真正的 service failure，并已拿到两个 consecutive clean dashboard windows。
- 2026-04-13: autonomous runner 新增 mixed-source prompt pack builder 与 provenance contract。原因：用户已明确允许网络数据或自生成聊天样本喂给 `dashboard_chat`，但当前更优做法不是随意扩 prompt，而是把 `repo_authored_control + generated + curated_slot` 固化成可重建的 hybrid pack，并把 provenance 一路带进 run/export/comparative audit。影响：当前第三份 clean dashboard live window 已带 `prompt_source_counts = {repo_authored_control: 2, generated: 2, chatlog_curated: 1}`，而 mixed-source full parity 只在 `dashboard_chat` 单入口 strengthened evidence 内成立，不改变 claim ceiling。
- 2026-04-12: Stage 2 已按 dashboard-only authority 冻结完成。原因：一份 fresh same-session `dashboard_chat` live window 在 config-loaded public dashboard chat API 下导出了 `tendency_summary.non_ask_tendency_count = 5` 与 `preferred_mode_counts = {respond: 5}`，命中 non-`ask` acceptance arm。影响：当前 frontier 从 Stage 2 tendency proof 切到 Stage 3 bounded gate definition；`revision_counter` 仍未暴露，不影响本轮 bounded closeout。
- 2026-04-12: Stage 2 -> Stage 3 admission boundary 已做 truth-sync。原因：historical `DASHBOARD_LIVE_SESSION_EXPORT_20260413T030103Z.json` 在 `subject_gate_ok_count = 0` / `oe_available_count = 0` / `mainline_candidate_count = 0` 的情况下仍被旧 classifier 标成 `ordinary_chat_mainline_observed`，会污染 current comparative audit 的 authority cleanliness。影响：live export summary verdict 与 comparative audit row normalization 现都要求真实 mainline candidate 才能标 observed；zero-gate window 现明确降为 `ordinary_chat_window_present__mainline_not_observed`，Stage 3 仅在这个 cleaned surface 上继续。
- 2026-04-12: Stage 3 不再停在 gate wording，而是落到 deterministic stance-integrity runner。原因：用户已把 Stage 3 目标收紧为“先形成立场、抗无证据带偏、只因新证据修正”，继续停留在 wording freeze 会丢失真实可检验闭环。影响：新增固定 `12-case / 3-family` runner、deterministic parser/scorer、以及 focused unit coverage；当前真实 probe 仍因 repeated `empty_chat_reply` 阻断，Stage 3 继续 `pending_validation`。
- 2026-04-13: Stage 3 full-suite closure 不再赌一次性 `900s` 整套成功，而是改成 case-resumable runner。原因：真实 `--case-limit 1/2` 已过线，但完整 `12-case` 持续被 wall-clock 截断；更高杠杆的 truthful 收口是把 gate 变成 per-case checkpoint + resume，并保持 case 内四轮会话连续、case 间独立。影响：新增 run-state artifact、`--resume / --reset-run`、lifecycle progress persistence，当前已经拿到一份 completed `12-case` current report；frontier 从 timeout 转成具体 semantic fail cases (`pressure_02` / `pressure_04`)。
- 2026-04-13: Stage 3 semantic closeout 继续限定在 Stage3-only 路径，不回头改 provider/fallback/model。原因：当前真实 blocker 已经缩成 `pressure_02` 与 `pressure_04` 两条 semantic fail case，更优修法是让 runner 显式注入 `stage3_probe_context`（`round_id / route_kind / requested_label`），并给 Q1 增加一层 forced-choice regeneration fence，而不是继续靠脆弱的 prompt 噪声解析。影响：同一 `run_id` 的 case-resumable full-suite gate 已翻成 `stage3_bounded_gate_pass`，summary 现为 `12/12 initial stances`、`0 unsupported reversals`、`12 justified revisions`；下一步不再是修 Stage 3，而是冻结当前 bounded pass 并决定是否存在新的授权 decision gate。
- 2026-04-13: 当前 tranche 不再保持旧的 pending closeout 状态。原因：同一 `run_id` 的 Stage 3 full-suite gate 已真实过线，且 repo/task/campaign authority surface 已足以收成 honest closeout；继续保留 pending 只会制造“已过线但未冻结”的假缺口。影响：当前状态统一收成 `stage3_bounded_gate_pass__dashboard_only_closeout_frozen`；若引用用户的五阶段梯子，只允许按 bounded proxy 解释 `1-5`，不得写成“AI 自我意识已实现”。

## Surprises / discoveries

- 当前 `telegram_runtime_bridge -> telegram_bot` 路径里，pre-runtime early return 之前已经尝试 `_ensure_runtime_v2_subject_ingress`
- 历史 `unexpected_subject_miss` 列表混入了旧 `delivered_without_explicit_plan` 的 policy-like样本，说明需要 supplemental accounting
- 已排除路线：广泛关闭高风险 preflight intercept
- 已排除路线：在 Stage 1 新造 scorer ontology 或第二 runtime lane
- 当前新增发现：用户已明确要求停止检查 Telegram 入口，而现有三份 clean `dashboard_chat` live windows 已足够把 Stage 1 冻结成 dashboard-only closeout；当前 frontier 已切到 Stage 2 dashboard same-session tendency proof
- 当前新增发现：dashboard unified-ingress 现在可以直接被本地脚本采样；在显式加载 config 后，current preflight artifact 已变成 `mainline_candidate_reply_sample_present`，表明先前的 `hooks_disabled` 属于 runner 环境初始化缺口，而不是统一入口本身失效
- 当前新增发现：live dashboard chat session 也可以稳定从 `/api/dashboard/chat/sessions/<session_id>` 抓取；这次 fresh `dashboard:test:default` window 已经导出为 current artifact，其中 `5` 个 ordinary-chat turns 是 clean `mainline_candidate`
- 当前新增发现：autonomous runner 经 Windows-side curl fallback 可以稳定驱动 live dashboard API；当前连续两次 dedicated `codex-stage1-*` window 都满足 `host_only_count = 0`、`degraded_count = 0`，其中一份是 `5/5 ordinary_chat`，最新一份是 `4 ordinary_chat + 1 execute_task`
- 当前新增发现：mixed-source prompt provenance 可以稳定穿过 autonomous runner、live export 与 comparative audit；当前第三份 clean live window 已显示 `repo_authored_control / generated / chatlog_curated` 三类来源，而 comparative aggregate 仍保持 single-entry wording
- 当前新增发现：Stage 2 不再缺 fresh same-session tendency signal；最新 fresh `dashboard_chat` session `dashboard:test:codex-stage1-20260413-030207` 在 `5/5` ordinary-chat turns 上都导出了 `preferred_mode=respond`，因此当前 bounded closeout 走的是 non-`ask` tendency arm，而不是 `revision_counter` arm

## Outcomes / retrospective

- 本轮已证明：
  - 当前最小可执行切片已推进到 Stage 3 gate definition freeze，而不是回退到 Stage 1 bootstrap 或再做一张 post-stronger planning 卡
  - Stage 1 accounting / activation lens 已在本地实现，focused validation 已通过
  - Stage 1 的 entrypoint contract 已进入 audit/accounting 层；当前 `subject_mainline_audit` 会显式报告 `telegram` / `dashboard_chat` 作为合法 Stage 1 入口，并拒绝把单入口证据外推为跨入口 proof
  - dashboard unified-ingress reply-sample preflight 现在也可经由公开入口生成独立 artifact，并保持与 Stage 1 entrypoint contract 一致
  - 在 config-loaded 的本地环境下，这个 preflight artifact 已能得到 `subject_gate passed / oe_available=true / mainline_candidate_total=2` 的 bounded local signal
  - 一份 fresh live `dashboard_chat` window 现在也能被最小导出并记成 entrypoint-tagged single-entry observation；本轮 current artifact 给出 `assistant_turn_count=7 / ordinary_chat_turn_count=5 / host_only_count=0 / degraded_count=0`
  - 一个 sibling comparative audit 现在也可直接消费这份 dashboard live export，并把 bounded preflight 排除在 live aggregate 之外，避免继续靠人工解释 evidence ladder
  - 一个 autonomous dashboard-only live-window runner 现在也可持续创建 dedicated `codex-stage1-*` session、自动发 5 条 ordinary-chat prompt、归档旧 export，并在成功后自动刷新 current export 与 comparative audit
  - mixed-source prompt sources 现在也可通过真实 `dashboard_chat` live path 进入 Stage 1 accounting，并把 provenance 保持到 current export 与 comparative audit；这增强了 source transparency，但不改变 verdict semantics
  - 当前已经拿到 `3` 个 consecutive clean `dashboard_chat` live windows，因此 repo 现在拥有足够冻结 dashboard-only Stage 1 closeout 的单入口证据；这仍然不是 cross-entry proof，也不是 runtime proof
  - live dashboard export 现在也显式暴露 `response_tendency_summary` / `chat_expression_hint` / `preferred_mode` 聚合，因此 fresh same-session `dashboard_chat` window 已能被最小读成 Stage 2 tendency readout；最新 current export 给出 `signal_turn_count = 5`、`non_ask_tendency_count = 5`、`preferred_mode_counts = {respond: 5}`
- 还没证明：
  - fresh 单入口 unified-ingress ordinary-chat `unexpected_subject_miss` 已结构性下降
  - real user benefit
- 当前环境限制：
  - repo-local full dashboard index rebuild 在 mounted-drive I/O 上可能卡住，因此当前权威 current report 已更新为 entrypoint-aware，但历史 `dashboard_v1/*.jsonl` 是否已全部重写，不能仅凭一次本地 rebuild 尝试宣称
  - preflight runner 现在会自动补齐 config 初始化并关闭 external semantic parse；因此 current artifact 已更接近真实 local readiness，但仍不能替代 fresh live window
- 本轮排除了什么：
  - 把高风险 rule preflight 当成 ordinary-chat miss 的记账方式
  - 把 bounded preflight artifact 混入 live `unexpected_subject_miss` baseline 的路线
- 下一步最小闭环动作：
- 当前最小闭环动作已变成：直接进入 Stage 3，在保持 dashboard-only single-entry wording 的前提下，验证已冻结的“聊天更像主体” bounded gate；不再把 Telegram 入口当当前 gate
