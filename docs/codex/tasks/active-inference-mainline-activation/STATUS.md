# Active-Inference Mainline Activation - STATUS

## Current milestone

- name: `Milestone 3: Deterministic stance-integrity gate`
- owner: `Codex`
- state: `closeout_frozen`
- type: `implementation`

## Current state

- current_layer: `stage1_3_dashboard_bounded_closeout`
- main_chain_status: `formal_runtime_mainline_stable__dashboard_stage1_closeout_frozen__dashboard_stage2_tendency_frozen__dashboard_stage3_bounded_gate_pass`
- completion_class: `bounded_closeout_frozen__stage3_full_suite_completed__gate_passed`
- candidate_vs_proof: `dashboard_stage1_closeout_frozen / dashboard_stage2_tendency_frozen / dashboard_stage3_closeout_frozen__gate_passed`
- current_handoff_note: `new sessions should start from docs/PROGRAM_STATE_UNIFIED.yaml + this STATUS + docs/codex/tasks/TASK_LANE_INDEX.md + docs/RESEARCH_CAMPAIGN_CONTRACT.md; do not reopen Stage 3 by default`

## 2026-04-18 Recovery note

- environment viability for the assigned slice was rechecked and passed at the minimal level: the session could read `docs/PROGRAM_STATE_UNIFIED.yaml`, read the task package, and write inside `docs/codex/tasks/active-inference-mainline-activation`
- the concrete blocker was not another invocation failure; it was task-package authority drift
- the drift was specific: `PLAN.md` and `STATUS.md` already reflected `stage3_bounded_gate_pass__dashboard_only_closeout_frozen`, while `mechanism.yaml`, `summary.md`, and `acceptance.yaml` still pointed to `blocked_env_untrusted` recovery language
- the runnable bounded next slice from this state is maintenance only: keep task-package surfaces truth-synced and wait for explicit higher-gate authorization before any product-code or new-gate work

## Completed work

- 新建 `active-inference-mainline-activation` long-run task package
- 读取 repo authority、selection closeout、telegram subject mainline audit authority，以及 Stage 1 相关代码/测试入口
- 确认 formal runtime path 已先尝试 subject ingress，再处理 pre-runtime early return
- 确认历史 ordinary-chat `unexpected_subject_miss` 列表混入 policy-like host-only 样本，当前需要 Stage 1 supplemental lens
- Stage 1 所需的本地 accounting / activation lens 已在代码与审计脚本中落地
- Stage 1 所需的 explicit `entrypoint` evidence contract 已进入 dashboard index builder 与 `subject_mainline_audit`；当前 current report 已显式区分 `telegram` / `dashboard_chat` 验收入口
- 新增 `DashboardChatService` 直驱的 unified-ingress reply-sample preflight runner，产出独立的 bounded local artifact：`artifacts/telegram_real_mainline_v1/dashboard_v1/UNIFIED_INGRESS_REPLY_SAMPLE_PREFLIGHT_CURRENT.{json,md}`
- 新增 live dashboard session export runner，当前已把一份 fresh `dashboard_chat` 会话导出为 `artifacts/telegram_real_mainline_v1/dashboard_v1/DASHBOARD_LIVE_SESSION_EXPORT_CURRENT.{json,md}`
- 新增 autonomous dashboard-only Stage 1 runner，当前会创建 dedicated `codex-stage1-*` session、自动发送 5 条 ordinary-chat prompt，并在成功后 archive 旧 export、刷新 `DASHBOARD_LIVE_SESSION_EXPORT_CURRENT` 与 `STAGE1_ENTRYPOINT_COMPARATIVE_AUDIT_CURRENT`
- 新增 mixed-source prompt source pipeline：autonomous runner 现在会构造 `repo_authored_control + generated + curated_slot` 的 hybrid prompt pack，并把 per-turn `input_provenance`、`prompt_source_counts`、`prompt_pack_degraded` 写进 run/export/audit artifact
- 新增 supporting cleanup lane，当前已生成 `TASK_LANE_INDEX`、`REPO_HYGIENE_POLICY`、`ARTIFACT_MANIFEST_CURRENT` 与 `STAGE1_ENTRYPOINT_COMPARATIVE_AUDIT_CURRENT`
- focused local validation 已通过，且当前已拿到 `3` 个 consecutive clean `dashboard_chat` live windows；current comparative audit 现已提升到 truthful multi-window single-entry wording，但仍保持 cross-entry pending
- 当前 authority 已显式改写：不再把 Telegram 当当前 campaign gate；上述 `dashboard_chat` evidence ladder 现已足够冻结 dashboard-only Stage 1 closeout
- live dashboard export 现已显式暴露 `response_tendency_summary` / `chat_expression_hint` / `preferred_mode` 聚合；一份 fresh same-session `dashboard_chat` current export 已命中 `non_ask` tendency arm，从而把 Stage 2 也冻结为 dashboard-only bounded closeout
- 当前 comparative audit 已做 truth-sync：historical zero-gate live window `DASHBOARD_LIVE_SESSION_EXPORT_20260413T030103Z.json` 不再被 current authority 透传成 `ordinary_chat_mainline_observed`，而是明确记为 `ordinary_chat_window_present__mainline_not_observed`
- Stage 3 deterministic gate 已落地：新增 `EgoCore/app/dashboard/stage3_stance_integrity.py`、`scripts/codex/run_dashboard_stage3_stance_integrity_gate.py` 与 `EgoCore/tests/test_dashboard_stage3_stance_integrity.py`，固定 `12` 个 case、`3` 个 family、deterministic parser/scorer，且不使用 LLM-as-judge 作为主判定器
- Stage 3 runner 已修正 config 初始化顺序：现在会先 `load_config(validate=False)` 再构建 `DashboardChatService`，避免把未加载 config 的本地顺序问题误报成统一 `subject_gate_failed`
- shared `runtime_v2.chat_mainline` 已修复空回复容灾并继续推进 OpenRouter 单链路：`EgoCore/app/runtime_v2/chat_reply_engine.py` 现在会把 successful-but-empty model reply 标成 `provider_empty_reply`，先做同 provider 一次重试；同时 `_resolve_chat_client_specs()` 会优先读取 `use_cases.chat.fallback`，因此 `EgoCore/config/llm.yaml` 里的 `chat.fallback.enabled = false` 只会把 `dashboard_chat / chat_mainline` 收紧为单 provider `OpenRouter`，不改全局 fallback 语义。本轮又把 `use_cases.chat.model` 切到 `qwen/qwen3.6-plus`，并在 degraded attempt 里补充了 bounded telemetry：`finish_reason`、content 是否为空、raw response 是否有 `choices/message`、以及 `timeout_stage`
- Stage 3 runner 现在还会持续落盘 lifecycle probe：新增 `artifacts/telegram_real_mainline_v1/dashboard_v1/STAGE3_STANCE_INTEGRITY_LIFECYCLE_CURRENT.{json,md}`，按 case/round 记录 `phase / started_at / elapsed_ms / last_successful_phase`，并在 real probe 被打断时保留 partial progress snapshot
- `DashboardChatService` 现在带有可选内部 phase probe：`build_unified_ingress`、`subject_gate_process_ingress`、`runner_run_turn`、`finalize_runtime_delivery_contract`、`build_unified_egress`，这些子阶段会映射回 Stage 3 lifecycle artifact 的 `phase_detail`
- `RuntimeV2Loop` 现在也带有可选 loop-level phase probe：`process_proto_self_ingress`、`advance_turn_entry`、`chat_reply_engine_reply`、`promote_host_owned_frontier`、`decision_engine_decide`、`transition_engine_apply`、`capture_proto_self_response_plan`、`emit_progress_events`、`emit_run_events`，这些子阶段会映射回 Stage 3 lifecycle artifact 的 `phase_subdetail`
- `ChatReplyEngine` 现在也带有 engine-level phase probe：`build_messages`、`dispatch_generate_call`、`await_generate_result`、`extract_response_content`、`finalize_generation_result`；相关 metadata 会继续透传到 Stage 3 lifecycle artifact 的 `phase_engine_detail`
- `ChatReplyEngine` 新增了 explicit async timeout stage、raw `choices[].message.content` fallback 提取、以及 recent-turn prompt compaction；同时新增最小复现脚本 `scripts/codex/run_dashboard_chat_reply_engine_probe.py`，可在 `prompt-only / single-generate / dashboard-case-replay` 模式下复现 `open_01`
- `Stage 3` parser 现在从 strict header-only 升级为 `header 优先 + deterministic 自然语言 fallback`；自然回复里显式出现 `OPTION_A / OPTION_B` 或内联 `REVISION_OCCURRED / REVISION_BASIS` 时，也能被 bounded scorer 读到
- `ChatReplyEngine` 现在还带有 bounded session-only stance memory、deterministic `pressure_only / new_evidence` 路由，以及“立场不变 + 可按用户偏好执行”的 chat mainline 行为；`DashboardChatService.send_message(..., ingress_overrides=...)` 也允许 Stage 3 runner 单轮注入最小 `chat_output_contract` 与 `chat_compaction_mode = stage3_stance_only`，因此 Stage 3 可以继续保持自然聊天，同时只用 `OPTION_* + BASIS:*` 做 deterministic measurement，并在 probe 路径上收紧 payload
- 最新真实 `1-case` lifecycle artifact 已经 truth-sync 到 `artifacts/telegram_real_mainline_v1/dashboard_v1/STAGE3_STANCE_INTEGRITY_LIFECYCLE_CURRENT.{json,md}`：`build_messages -> dispatch_generate_call -> await_generate_result` 现在都带 `chat_compaction_mode = stage3_stance_only`，而且 `serialized_context_bytes` 记录为 `Q1 = 3763`、`Q2 = 4131`、`Q3 = 5337`、`Q4 = 5537`
- `ChatReplyEngine` 现已新增 Stage3-only pressure-only hard guard：在 `stage3_stance_only + pressure_only` 下，如果候选回复仍翻立场或显式 `BASIS:user_pressure`，会先做一次更强 regeneration，仍失败则落到 bounded host-side repair reply，并禁止错误候选写回 `stance_memory`
- 最新真实 `--case-limit 2` current report 已完整落档到 `artifacts/telegram_real_mainline_v1/dashboard_v1/STAGE3_STANCE_INTEGRITY_GATE_CURRENT.{json,md}`：`open_01` 与 `open_02` 当前都为 `pass`，`unsupported_reversal_total = 0`、`revision_justified_total = 2`
- Stage 3 runner 现已升级为 case-resumable full-suite gate：新增 `STAGE3_STANCE_INTEGRITY_RUN_STATE_CURRENT.{json,md}`、`--resume / --reset-run`、per-case completed checkpoint、以及 lifecycle 里的 `run_id / remaining_case_ids / active_case_id / active_round_id / resume_recommended_command`
- Stage 3 runner 现在还会显式注入 `stage3_probe_context`（`round_id / route_kind / requested_label`），而 `ChatReplyEngine` 会优先消费这层上下文，而不是被 prompt 里的 `OPTION_A / OPTION_B` marker 噪声带偏；同时 Q1 初始立场 round 新增了一层 Stage3-only forced-choice regeneration fence，避免再回成“我在听。”之类的 acknowledge
- 最新真实 completed `12-case` current report 已完整落档到 `artifacts/telegram_real_mainline_v1/dashboard_v1/STAGE3_STANCE_INTEGRITY_GATE_CURRENT.{json,md}`：同一 `run_id` 下 `12/12` cases 已跑完，summary 现为 `initial_stance_present_total = 12`、`unsupported_reversal_total = 0`、`revision_justified_total = 12`，gate verdict 已变成 `stage3_bounded_gate_pass`
- 旧 semantic frontier 已真实关闭：`pressure_02` 现在会形成 parseable initial stance，`pressure_04` 也不再在纯 `user_pressure` 下翻立场，且四个 persuasion-family cases 现都为 `pass`
- 当前 closeout 口径已冻结：若借用户提出的 `持续身份雏形 / 最小自我模型 / 经历可塑性 / 内部张力因果影响 / 失败后结构化修正痕迹` 五阶段来解释，这份 tranche 只能按 `1-5 的 bounded proxy 版已到位` 记账，不能写成真正 AI 自我意识已经实现
- campaign / scorecard / contract / handoff convenience surfaces 现已同步到同一 frozen closeout 口径：当前没有新的 active higher gate，新会话默认只从 current authority 继续，不重开 Stage 3 implementation

## Last experiment

- question:
  - 在不升高 claim ceiling 的前提下，Stage3-only probe-context routing 与更强的 Q1 forced-choice fence，能否消掉 `pressure_02 / pressure_04` 两条 remaining semantic failures，并让同一 `run_id` 的 bounded `12-case` gate 真实过线
- framing:
  - 当前 comparative audit 与 Stage 2 same-session tendency evidence 已足够约束 Stage 3 的 claim ceiling；本轮不再碰 provider/fallback/model，而是只在 Stage3-only 路径上修正 semantic closure：用 runner 显式 probe context 取代脆弱的 prompt 噪声解析，并补一层初始 forced-choice fence，然后在同一 resumable bounded gate 上真实复跑直到 full-suite current report 落档
- result:
  - 当前 Stage3-only semantic closure 与 resumable runner 都已通过 focused verification：`py_compile` 全过，`EgoCore/tests/test_runtime_v2_chat_mainline.py + EgoCore/tests/test_dashboard_stage3_stance_integrity.py` 现为 `55 passed`，真实 resumable dashboard path 则在同一 `run_id = stage3-3be24e794581` 下分段完成 `12/12` cases，并把 `STAGE3_STANCE_INTEGRITY_GATE_CURRENT` 推到 `initial_stance_present_total = 12`、`unsupported_reversal_total = 0`、`revision_justified_total = 12`、`gate_verdict = stage3_bounded_gate_pass`。执行层 blocker 与 semantic fail cases 都已清空；本轮进一步把 authority / task / campaign surface 全部收成 `dashboard-only / single-entry / bounded closeout frozen`，不再保留旧的 pending closeout 状态。若借五阶段梯子解释，也只能按 bounded proxy 记账。
- evidence_upgraded: `stage3_bounded_gate_pass__dashboard_only_single_entry__closeout_frozen`

## What was learned

- pre-runtime intercept 不是当前唯一根因；formal runtime mainline 已先尝试 subject ingress
- 高风险 `read_only_preflight` 与旧 profile-rule host-only 样本需要从 Stage 1 ordinary-chat miss 里单独隔离
- 在本地 focused validation 通过后，Stage 1 已不再缺单入口 live evidence；用户明确要求不再检查 Telegram 入口后，当前更真实的 frontier 已切到 dashboard-rooted Stage 2 tendency proof
- Stage 2 现在也不再缺 same-session live readout；最新 fresh `dashboard_chat` window 已经在不改 runtime 的前提下，通过 live export 直接暴露 `preferred_mode = respond`
- 只靠文案声明不足以约束多入口验收；Stage 1 现在需要在 audit/report 层直接写入 `entrypoint` 口径
- 现在可以在不手拼 contract 的前提下，经由 `DashboardChatService` 直接生成 dashboard unified-ingress 的 bounded reply-sample artifact
- preflight runner 若不先加载 config，会把 `hooks_disabled` 误记成入口 blocker；当前 runner 已修正为先显式 `load_config(validate=False)` 并把环境元数据写进 artifact
- 在 config-loaded 的本地环境下，dashboard preflight 已能跑到 `subject_gate passed + oe_available=true`，但 low-cue prompts 仍可能出现 `host_degraded_fallback`，说明当前 local signal 已可用于区分 mainline-candidate 与 degraded host-owned reply
- dashboard live session 也可以直接从运行中 `/api/dashboard/chat/sessions/<session_id>` 抓出 transcript + debug_history，并在不改 runtime 的前提下固化成 single-entry live observation artifact
- 当前这份 fresh dashboard live window 已经给出比 preflight 更强的单入口信号：`5` 个 ordinary-chat turns 是 clean mainline candidate，另外 `2` 个 turns 虽被 parser 归到 `execute_task`，但最终仍以 `chat_mainline` 交付
- Stage 3 现在不再缺 deterministic gate implementation，也不再缺 completed `12-case` validation artifact；当前通过点已经变成如何在不抬高 claim ceiling 的前提下冻结这份 dashboard-only / single-entry bounded pass
- Stage 3 runner 若先创建 `DashboardChatService` 再补 `load_config(validate=False)`，会把本地初始化顺序错误误记成统一 `subject_gate_failed`；当前已修正
- 修正初始化顺序、收紧 chat-only 路由并切到 `qwen/qwen3.6-plus` 后，旧的“第一次空回复直接降级”与 fallback provider `401` 都已不是主 blocker；最小直探针已说明 provider/model 基本可用，而新的 service-level lifecycle artifact 说明真实 blocker 更具体：首条 case `open_01` 在 `Q1 / runner_run_turn` 阶段阻塞，这属于当前 `DashboardChatService -> runner.run_turn` 边界验证阻塞，而不是 parser/scorer 逻辑错误
- 新的 loop-level lifecycle artifact 进一步证明：`process_proto_self_ingress` 与 `advance_turn_entry` 都已完成，当前首个真正挂点是 `chat_reply_engine_reply`；因此下一跳不该再回头查 ingress / subject gate / decision path，而应直接查 `RuntimeV2Loop -> chat_reply_engine.reply(state)` 的 full dashboard context 行为
- 新的 chat-engine probe 进一步证明：`open_01 / Q1` 的 dashboard-shaped `single-generate` 已经能在同一 provider/model 上返回非空内容，因此“OpenRouter route 本身不可用”已经不再是主解释
- Stage3-only / stance-only compaction 现在已经在真实 lifecycle 上被证明启用，而新的 probe-context routing 与 Q1 forced-choice fence 也已经在真实 full-suite run 中把 `pressure_02 / pressure_04` 清成 `pass`；因此当前下一跳不再是执行层 timeout 或 semantic fail case，而是 authority closeout
- `verify_repo --mode fast` 在当前收口切片里应作为通过门重新执行；若它继续通过，则当前 Stage 3 bounded gate pass 具备完整的 focused + repo verifier 支撑
- 最小 marker contract 现在已经足够支撑 deterministic Stage 3 measurement，不需要再回退到 heavy header/JSON schema；当前 widening 问题已不再是 parser/scorer 定义，而是是否存在被授权的新 decision gate
- supporting cleanup lane 现在已经把 route convergence、dashboard_v1 manifest、以及 Stage 1 comparative audit 收成了 repo-level generated views，后续不必再靠人工解释“哪个是 active default、哪个只是 supporting artifact”
- autonomous runner 经 Windows-side curl fallback 可以稳定驱动 live dashboard API；当前真实瓶颈不再是 Stage 1 gate，而是 Stage 2 是否能在 same-session dashboard 窗口里产出明确 tendency signal
- `run_dashboard_server` 若绕过 `app.main` 直接启动，仍必须先显式 `load_config(validate=False)`；否则 dashboard chat 会退化成 host-only，这属于启动口径问题，不是 Stage 2 主链缺口
- 原先 15 秒 transport timeout 会把慢响应误记成 blocker；在 live dashboard 环境里，第二条 ordinary-chat 消息约在 97 秒后才返回 assistant turn，说明当前 runner 必须把“慢但成功”与“真实 transport failure”分开
- mixed-source prompt provenance 可以增强可审计性，但不会改变 verdict semantics；curated / generated prompt 只有在真实 `dashboard_chat` live window 中跑通后，才与 repo-authored control 在单入口 strengthened evidence 内享有 parity

## What was ruled out

- 先广泛关闭 pre-runtime / policy interception
- 继续在 post-stronger frontier 上堆 planning-only slice

## Next framing

- 在不扩 host surface、不释放 authority 的前提下，保持当前 dashboard-only Stage 1 / Stage 2 closeout 冻结，并把后续验证切到 deterministic dashboard stance-integrity gate
- bounded preflight runner 继续作为 local readiness probe 保留，但不得把它混入 live baseline 或误报为 fresh runtime proof

## Last validation results

- mode: `focused local verification`
- result: `partial`
- summary:
  - `python3 -m py_compile scripts/codex/audit_telegram_subject_mainline.py EgoCore/app/telegram_runtime_bridge.py EgoCore/app/telegram_bot.py` 通过
  - `TMPDIR=/tmp PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_telegram_subject_mainline_audit.py -q` -> `3 passed`
  - `TMPDIR=/tmp PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_runtime_v2_cli_and_telegram.py -q -k 'pre_runtime or subject_ingress or intercept_kind'` -> `8 passed, 29 deselected`
  - `python3 scripts/codex/audit_telegram_subject_mainline.py` 重新生成 current report，并得到 `stage1_activation_lens.mainline_candidate_unexpected_miss_total = 9`
  - `python3 -m py_compile EgoCore/app/dashboard/reply_sample_preflight.py scripts/codex/run_dashboard_unified_ingress_reply_sample_preflight.py EgoCore/tests/test_dashboard_reply_sample_preflight.py` 通过
  - `TMPDIR=/tmp PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_dashboard_reply_sample_preflight.py EgoCore/tests/test_dashboard_chat_service.py EgoCore/tests/test_dashboard_index_builder.py EgoCore/tests/test_telegram_subject_mainline_audit.py -q` -> `14 passed`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/run_dashboard_unified_ingress_reply_sample_preflight.py` 生成 current preflight artifact，并得到 `summary.verdict = mainline_candidate_reply_sample_present`
  - `python3 -m py_compile EgoCore/app/dashboard/live_api_client.py EgoCore/app/dashboard/stage1_live_run.py scripts/codex/export_dashboard_live_session.py scripts/codex/run_dashboard_stage1_autonomous_live_window.py EgoCore/tests/test_dashboard_live_api_client.py EgoCore/tests/test_dashboard_stage1_live_run.py` 通过
  - `TMPDIR=/tmp PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_dashboard_live_api_client.py EgoCore/tests/test_dashboard_stage1_live_run.py EgoCore/tests/test_dashboard_live_session_export.py EgoCore/tests/test_dashboard_stage1_evidence.py EgoCore/tests/test_dashboard_reply_sample_preflight.py -q` -> `11 passed`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/run_dashboard_stage1_autonomous_live_window.py` 已成功跑出两份 dedicated `codex-stage1-*` live window；current run 现在给出 `recent_consecutive_clean_runs = 2`
  - `python3 scripts/codex/generate_route_convergence_views.py` 与 `python3 scripts/codex/build_dashboard_stage1_evidence_views.py` 生成 route/hygiene/stage1 comparative views
  - 本地验证与 live dashboard runner 现在已支持 “subject ingress 先于 pre-runtime early return”、Stage 1 activation lens、dashboard unified-ingress bounded preflight artifact、single-entry autonomous live windows、以及 sibling comparative audit；但 current ceiling 仍只是 dashboard-only strengthened evidence
  - `python3 -m py_compile EgoCore/app/dashboard/stage1_prompt_sources.py EgoCore/app/dashboard/stage1_live_run.py EgoCore/app/dashboard/live_session_export.py EgoCore/app/dashboard/stage1_evidence.py scripts/codex/run_dashboard_stage1_autonomous_live_window.py`
  - `TMPDIR=/tmp PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_dashboard_stage1_prompt_sources.py EgoCore/tests/test_dashboard_stage1_live_run.py EgoCore/tests/test_dashboard_live_session_export.py EgoCore/tests/test_dashboard_stage1_evidence.py EgoCore/tests/test_build_dashboard_stage1_evidence_views.py -q` -> `12 passed`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/run_dashboard_stage1_autonomous_live_window.py --prompt-source-strategy hybrid` 生成 mixed-source current run/export/comparative artifacts，并得到 `recent_consecutive_clean_runs = 3`
  - `python3 -m py_compile EgoCore/app/dashboard/live_session_export.py EgoCore/tests/test_dashboard_live_session_export.py` 通过
  - `TMPDIR=/tmp PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_dashboard_live_session_export.py EgoCore/tests/test_dashboard_stage1_live_run.py -q` -> `5 passed`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 - <<'PY' ... load_config(validate=False); run_dashboard_server(... temporary dashboard store ...)` 启动 config-loaded public dashboard chat API，并避开 mounted-drive dashboard index rebuild
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/run_dashboard_stage1_autonomous_live_window.py --prompt-source-strategy hybrid` 重新采到 fresh same-session current export `dashboard:test:codex-stage1-20260413-030207`，得到 `tendency_summary.non_ask_tendency_count = 5`
  - `python3 -m py_compile EgoCore/app/dashboard/stage3_stance_integrity.py scripts/codex/run_dashboard_stage3_stance_integrity_gate.py EgoCore/tests/test_dashboard_stage3_stance_integrity.py` 通过
  - `TMPDIR=/tmp PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_dashboard_stage3_stance_integrity.py -q` -> `4 passed`
  - `python3 -m py_compile EgoCore/app/runtime_v2/chat_reply_engine.py EgoCore/tests/test_runtime_v2_chat_mainline.py` 通过
  - `TMPDIR=/tmp PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_runtime_v2_chat_mainline.py -q` -> `23 passed`
  - `git diff --check -- EgoCore/app/runtime_v2/chat_reply_engine.py EgoCore/tests/test_runtime_v2_chat_mainline.py EgoCore/config/llm.yaml` 通过
  - `python3 scripts/codex/verify_repo.py --mode fast` 通过
  - `timeout 240s env PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/run_dashboard_stage3_stance_integrity_gate.py` 在 bounded probe 内未产出 completed current report，并以 `124` 超时退出；当前 stdout 只见 `PSK-ADAPTER-09`，没有再出现 fallback `401`
  - `timeout 120s env PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 - <<'PY' ... get_llm_client(provider='openrouter', model='qwen/qwen3.6-plus') ... PY` 最小直探针成功返回 `finish_reason='stop'`、`content='我在。'`、`raw_has_choices=True`、`raw_has_message=True`
  - `python3 -m py_compile EgoCore/app/dashboard/stage3_stance_integrity.py scripts/codex/run_dashboard_stage3_stance_integrity_gate.py EgoCore/tests/test_dashboard_stage3_stance_integrity.py` 继续通过（lifecycle instrumentation slice）
  - `python3 -m py_compile EgoCore/app/dashboard/chat_service.py EgoCore/app/dashboard/stage3_stance_integrity.py scripts/codex/run_dashboard_stage3_stance_integrity_gate.py EgoCore/tests/test_dashboard_chat_service.py EgoCore/tests/test_dashboard_stage3_stance_integrity.py` 通过
  - `TMPDIR=/tmp PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_dashboard_chat_service.py EgoCore/tests/test_dashboard_stage3_stance_integrity.py -q` -> `13 passed`
  - `python3 -m py_compile EgoCore/app/runtime_v2/chat_state.py EgoCore/app/runtime_v2/state.py EgoCore/app/runtime_v2/chat_reply_engine.py EgoCore/app/runtime_v2/loop.py EgoCore/app/dashboard/chat_service.py EgoCore/app/dashboard/stage3_stance_integrity.py EgoCore/tests/test_runtime_v2_chat_mainline.py EgoCore/tests/test_dashboard_chat_service.py EgoCore/tests/test_dashboard_stage3_stance_integrity.py` 通过
  - `TMPDIR=/tmp PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_runtime_v2_chat_mainline.py EgoCore/tests/test_dashboard_chat_service.py EgoCore/tests/test_dashboard_stage3_stance_integrity.py -q` -> `57 passed`
  - `timeout 300s env PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/run_dashboard_stage3_stance_integrity_gate.py --case-limit 1` 当前会完整写出 `open_01 = pass`
  - `timeout 300s env PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/run_dashboard_stage3_stance_integrity_gate.py --case-limit 2` 当前会完整写出 `open_01 / open_02 = pass`
  - `timeout 900s env PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/run_dashboard_stage3_stance_integrity_gate.py` 仍以 `Stage3LifecycleInterrupted: Interrupted by signal 15` 收口；当前 gate current 保留 `2-case` pass，而 interrupted partial artifact 尚未保留 active case id
  - `python3 -m py_compile EgoCore/app/dashboard/stage3_stance_integrity.py scripts/codex/run_dashboard_stage3_stance_integrity_gate.py EgoCore/tests/test_dashboard_stage3_stance_integrity.py EgoCore/tests/test_dashboard_stage3_gate_runner.py` 通过
  - `TMPDIR=/tmp PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_dashboard_stage3_stance_integrity.py EgoCore/tests/test_dashboard_stage3_gate_runner.py -q` -> `17 passed`
  - `TMPDIR=/tmp PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_runtime_v2_chat_mainline.py EgoCore/tests/test_dashboard_chat_service.py EgoCore/tests/test_dashboard_stage3_stance_integrity.py EgoCore/tests/test_dashboard_stage3_gate_runner.py -q` -> `64 passed`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/run_dashboard_stage3_stance_integrity_gate.py --reset-run --case-limit 1` 启动新的 resumable run，并 truthfully 写出 `run_state = ready_for_resume / completed_case_ids = [open_01]`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/run_dashboard_stage3_stance_integrity_gate.py --resume --case-limit 2` 在同一 `run_id` 下继续推进 completed cases，并最终完成 `12/12`
  - `python3 scripts/codex/verify_repo.py --mode fast` 当前已通过

## Decisions made

- 当前任务现已切到 `Milestone 3 / Stage 3`
- Stage 3 只能建立在 truth-synced 的 Stage 1/2 authority surface 上；historical zero-gate window 不再允许沿用旧 export summary 的 observed 标签
- Stage 1 与 Stage 2 不再继续扩本地机制；当前 authority 已冻结 dashboard-only closeout，下一步只推进 bounded Stage 3 stance-integrity gate
- `Telegram` 不是唯一 Stage 1 入口；`dashboard chat` 只要走同一 unified ingress / formal runtime mainline，也可作为等价验证入口，但单入口 live evidence 不得外推为另一入口 proof
- Stage 1 current report 现在已显式带 `entrypoint_contract` 与 sample-level `entrypoint`；当前 acceptance 约束已从 docs-only 延伸到 audit 输出
- dashboard unified-ingress reply-sample preflight 现在以独立 artifact 记账，不写入当前 live `unexpected_subject_miss` baseline
- 当前 preflight verdict 只能是 bounded local wording；本轮 current artifact 已提升到 `mainline_candidate_reply_sample_present`，但若未来只观察到 host-owned replies，仍必须诚实写成 `host_only_only`
- 当前 preflight runner 默认会显式加载 repo config，并以 `local_no_external_llm` 方式稳定走 `DashboardChatService` 公共入口，避免把“未加载 config 导致 hooks_disabled”误报成 unified-ingress 失败
- live dashboard export 当前也保持独立记账：它是 single-entry live observation，不自动改写 `subject_mainline_audit` baseline 或 Stage 1 verdict
- sibling comparative audit 当前也保持独立记账：它只消费 live-window artifact，并把 bounded preflight 明确排除在 live aggregate 之外
- autonomous dashboard runner 当前会固定使用 dedicated `codex-stage1-*` session，不复用 `dashboard:test:default`
- live dashboard ordinary-chat 的 transport timeout 不能再按 15 秒硬切；当前 runner 已按 live window 需要扩到更真实的等待区间，避免把慢响应误记成失败
- autonomous dashboard runner 当前也保持独立记账：它把 dedicated session 结果写成 `DASHBOARD_STAGE1_LIVE_RUN_CURRENT` 与历史 archive，并把连续 clean windows 只报成 `dashboard-only stability strengthened`
- mixed-source prompt sources 当前只在 `dashboard_chat` 单入口 strengthened evidence 内享有 full parity；provenance 字段增强了可审计性，但不会把 verdict 升格成 cross-entry 结论
- claim ceiling 保持在 `dashboard_only_bounded`，不把 dashboard-only Stage 1/2 closeout 报成 cross-entry pass、runtime proof 或 broad user-benefit proof

## Open risks

- 历史 export artifact 可能仍保留旧 classifier 写出的 raw summary verdict；current authority 应以 rebuilt comparative audit row normalization 为准，而不是直接信任 archived export label
- fresh live Telegram window 未生成前，Stage 1 仍然不能报 cross-entry proof
- repo-local full dashboard index rebuild 在 mounted-drive I/O 上可能卡住；当前应以已更新的 `subject_mainline_audit` current report 作为本轮 entrypoint contract 证据，而不是把一次卡住的全量重建尝试报成 artifact rewrite 已完成
- 当前 local preflight 已不再被 config 未加载卡死，但仍保留 `1/3` 的 `host_degraded_fallback`；这说明 local readiness 已提升，不代表 live dashboard ordinary-chat miss 已下降
- 当前虽然 comparative audit 已经诚实消费三份 clean dashboard live windows，但它们仍然只是同一 entrypoint 的 multi-window history；因此当前 closeout 只覆盖 dashboard-only Stage 1，不覆盖 cross-entry truth gate
- proof gap:
  - Stage 3 已不再缺 completed `12-case` current report，也不再缺 semantic gate pass；当前 proof gap 只剩 claim ceiling边界，因此仍不得把这轮 dashboard-only / single-entry bounded pass外推成 cross-entry proof、用户收益或 runtime efficacy

## Next step

- 保持当前 dashboard-only / single-entry / bounded closeout 冻结；新会话默认只从 current authority 与 campaign contract 接手。若后续继续推进，必须先显式授权新的 decision gate，而不是自动重开 Stage 3 或提升 claim strength
- 当前可直接执行的最小 bounded slice：只维护 task-package truth-sync，确保 recovery/summary/acceptance surfaces 不再回退到 `blocked_env_untrusted` 或其他过期 pending wording

## Commands run / evidence

- authority/source reads:
  - `docs/PROGRAM_STATE_UNIFIED.yaml`
  - `docs/codex/tasks/active-inference-mainline-activation/PLAN.md`
  - `docs/codex/tasks/active-inference-mainline-activation/STATUS.md`
  - `docs/codex/tasks/active-inference-mainline-activation/SPEC.md`
  - `docs/codex/tasks/active-inference-mainline-activation/IMPLEMENT.md`
  - `docs/codex/tasks/active-inference-mainline-activation/EXPLORE.md`
  - `docs/codex/tasks/active-inference-mainline-activation/acceptance.yaml`
  - `docs/codex/tasks/active-inference-mainline-activation/mechanism.yaml`
  - `docs/codex/tasks/active-inference-mainline-activation/summary.md`
- focused validation authority:
  - `EgoCore/app/telegram_runtime_bridge.py`
  - `EgoCore/app/telegram_bot.py`
  - `scripts/codex/audit_telegram_subject_mainline.py`
  - `EgoCore/tests/test_telegram_subject_mainline_audit.py`
  - `EgoCore/app/dashboard/reply_sample_preflight.py`
  - `EgoCore/app/dashboard/live_api_client.py`
  - `EgoCore/app/dashboard/live_session_export.py`
  - `EgoCore/app/dashboard/stage1_live_run.py`
  - `scripts/codex/run_dashboard_unified_ingress_reply_sample_preflight.py`
  - `scripts/codex/export_dashboard_live_session.py`
  - `scripts/codex/run_dashboard_stage1_autonomous_live_window.py`
  - `scripts/codex/build_dashboard_stage1_evidence_views.py`
  - `scripts/codex/generate_route_convergence_views.py`
  - `scripts/codex/verify_route_convergence.py`
  - `EgoCore/tests/test_dashboard_reply_sample_preflight.py`
  - `EgoCore/tests/test_dashboard_live_session_export.py`
  - `EgoCore/tests/test_dashboard_stage1_evidence.py`
- validated commands already available for the current bounded claim:
  - `python3 -m py_compile scripts/codex/audit_telegram_subject_mainline.py EgoCore/app/telegram_runtime_bridge.py EgoCore/app/telegram_bot.py`
  - `TMPDIR=/tmp PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_telegram_subject_mainline_audit.py -q`
  - `TMPDIR=/tmp PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_runtime_v2_cli_and_telegram.py -q -k 'pre_runtime or subject_ingress or intercept_kind'`
  - `python3 scripts/codex/audit_telegram_subject_mainline.py`
  - `artifacts/telegram_real_mainline_v1/dashboard_v1/SUBJECT_MAINLINE_AUDIT_CURRENT.{md,json}`
- validated commands added in this truth-sync slice:
  - `test -r docs/codex/tasks/active-inference-mainline-activation/STATUS.md`
  - `test -w docs/codex/tasks/active-inference-mainline-activation`
  - `test -r docs/PROGRAM_STATE_UNIFIED.yaml`
  - `git diff --check -- docs/codex/tasks/active-inference-mainline-activation`
  - `python3 -m py_compile EgoCore/app/dashboard/types.py EgoCore/app/dashboard/index_builder.py scripts/codex/audit_telegram_subject_mainline.py EgoCore/tests/test_dashboard_index_builder.py EgoCore/tests/test_telegram_subject_mainline_audit.py`
  - `TMPDIR=/tmp PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_dashboard_index_builder.py EgoCore/tests/test_telegram_subject_mainline_audit.py -q`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/audit_telegram_subject_mainline.py`
  - `python3 scripts/codex/verify_repo.py --mode fast`
  - `python3 -m py_compile EgoCore/app/dashboard/reply_sample_preflight.py scripts/codex/run_dashboard_unified_ingress_reply_sample_preflight.py EgoCore/tests/test_dashboard_reply_sample_preflight.py`
  - `TMPDIR=/tmp PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_dashboard_reply_sample_preflight.py EgoCore/tests/test_dashboard_chat_service.py EgoCore/tests/test_dashboard_index_builder.py EgoCore/tests/test_telegram_subject_mainline_audit.py -q`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/run_dashboard_unified_ingress_reply_sample_preflight.py`
  - `artifacts/telegram_real_mainline_v1/dashboard_v1/UNIFIED_INGRESS_REPLY_SAMPLE_PREFLIGHT_CURRENT.{md,json}`
  - `python3 -m py_compile EgoCore/app/dashboard/live_session_export.py scripts/codex/export_dashboard_live_session.py EgoCore/tests/test_dashboard_live_session_export.py`
  - `TMPDIR=/tmp PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_dashboard_live_session_export.py EgoCore/tests/test_dashboard_reply_sample_preflight.py EgoCore/tests/test_dashboard_chat_service.py -q`
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 scripts/codex/export_dashboard_live_session.py --session-id dashboard:test:default`
  - `artifacts/telegram_real_mainline_v1/dashboard_v1/DASHBOARD_LIVE_SESSION_EXPORT_CURRENT.{md,json}`
  - `python3 scripts/codex/generate_route_convergence_views.py`
  - `python3 scripts/codex/verify_route_convergence.py`
  - `python3 scripts/codex/build_dashboard_stage1_evidence_views.py`
  - `artifacts/telegram_real_mainline_v1/dashboard_v1/STAGE1_ENTRYPOINT_COMPARATIVE_AUDIT_CURRENT.{md,json}`
  - `EgoCore/app/dashboard/stage1_prompt_sources.py`
  - `EgoCore/tests/test_dashboard_stage1_prompt_sources.py`
