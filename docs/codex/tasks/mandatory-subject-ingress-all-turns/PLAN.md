# Mandatory Subject Ingress For All Authorized Turns - PLAN

## Task summary

这是一个 repo-level 主链修复任务。目标不是提升某一条 `WP` 能力，而是把“主体知晓”从当前分散、部分路径有效的 best-effort 状态，收紧为所有已授权事件的强制 gate。

本任务只修接线与强制顺序，不改 authority source：

- `OpenEmotion` 负责知晓、写回、主体语义
- `EgoCore` 仍负责 reply/tool/transport/runtime 的最终现实裁决

## Milestones

### Milestone 1: Subject Gate Skeleton

- scope:
  - 建立统一 host-side subject gate abstraction
  - 固定 `ingress / finalized_result / response_plan` 三段强制顺序
  - 固定 `subject_gate_failed` blocking policy
- files / areas likely touched:
  - `EgoCore/app/openemotion_hooks/`
  - `EgoCore/tests/`
- acceptance:
  - 存在唯一 gate abstraction
  - 低层发送 helper 不再被业务路径直接绕过
  - hooks failure 的 blocking policy 有定向测试
- validation:
  - `python3 -m py_compile ...`
  - 定向 gate/unit tests
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note:
  - 回退到现有 best-effort hooks 使用方式，不保留半接线 gate

### Milestone 2: Telegram Runtime_V2 Early-Return Closure

- scope:
  - 修 `_handle_with_runtime_v2()`
  - 修 `plan_pre_runtime()` 产生的所有 host reply 早退分支
  - 确保 authorized turn 先 ingress，再 host branch，再 finalize
- files / areas likely touched:
  - `EgoCore/app/telegram_bot.py`
  - `EgoCore/app/telegram_runtime_bridge.py`
  - `EgoCore/tests/test_runtime_v2_cli_and_telegram.py`
- acceptance:
  - `profile_rule_registered`
  - `profile_rule_enforced`
  - `return_runtime_status`
  - `waiting_input`
  - `evidence_followup`
  - `task_conflict`
  - 以上路径都不再出现 authorized host-only success reply
- validation:
  - 定向 Telegram/runtime_v2 tests
  - `python3 scripts/codex/lint_repo.py`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note:
  - 如 runtime_v2 主线出现 regressions，先保持 existing behavior，不提交半闭合 early-return patch

### Milestone 3: Command / Document / Legacy Closure

- scope:
  - 修 `handle_command()` 与 `_send_result()` finalize 缺口
  - 修 document/ingestion wrapper 中的 host failure 直返路径
  - 修 `_handle_with_new_runtime()` 的 ingress/finalize 缺口
- files / areas likely touched:
  - `EgoCore/app/telegram_bot.py`
  - `EgoCore/tests/test_telegram_session_commands.py`
  - `EgoCore/tests/` 下相关 document/runtime tests
- acceptance:
  - `/new /status /context /prompt /proto /replace /append /cancel` 和普通 command result 都 subject-gated
  - unsupported type / download failure / ingestion failure 也不再跳过 finalize
  - `new_runtime success/timeout/crash` 都 subject-gated
- validation:
  - 定向 command/document/new_runtime tests
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note:
  - 保持 command ingress 现状，不接受只补一半 finalize 的 partial patch

### Milestone 4: Background / Proactive Closure

- scope:
  - 修 proactive/system user-visible send path
  - 明确 idle/developmental tick 与 final delivery 的主体 finalize 关系
- files / areas likely touched:
  - `EgoCore/app/telegram_bot.py`
  - `EgoCore/app/runtime_v2/proactive_telegram_cycle.py`
  - 相关 proactive tests
- acceptance:
  - proactive delivery 前存在 subject finalized-result + response-plan
  - 仍不放开 unsolicited authority；只是 delivery 前必须 subject-gated
- validation:
  - 定向 proactive tests
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note:
  - 若 proactive send 变得不稳定，宁可保留 host hold，不接受绕过 subject finalize 的 send

### Milestone 5a: Dashboard Preflight

- scope:
  - 用 `DashboardChatService` 后端直驱做发布前最便宜主链预验证
  - 只证明 ordinary-chat dashboard backend 路径里，subject ingress / runtime finalized-result / runtime response-plan / response-plan / output-check 能闭环
  - 不把 dashboard chat 写成 real Telegram 替代
- files / areas likely touched:
  - `EgoCore/app/dashboard/*`
  - `scripts/codex/run_dashboard_chat_preflight.py`
  - `EgoCore/tests/test_dashboard_*`
- acceptance:
  - ordinary-chat dashboard preflight report 通过
  - 每轮 `subject_gate.ingress.ok = true`
  - 每轮 `runtime_subject_finalize_ok = true`
  - 每轮 `runtime_subject_response_plan_ok = true`
  - report 明确 `source = dashboard_local_preflight`、`claim_ceiling = preflight_only`
- validation:
  - 定向 dashboard/preflight tests
  - `python3 scripts/codex/run_dashboard_chat_preflight.py`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note:
  - 若 preflight 需要 candidate-private host API 或绕开 subject finalize 才能过，维持任务 open，不发布

### Milestone 5: Verification + Fresh Real Sample Audit

- scope:
  - 跑定向测试、fast/full verify
  - 采 fresh real Telegram 样本
  - 刷新现有 `subject_mainline_audit_current` audit artifact/workflow
- files / areas likely touched:
  - `artifacts/telegram_real_mainline_v1/`
  - `docs/codex/tasks/telegram-subject-mainline-audit/` 只作为引用，不改 authority
- acceptance:
  - 新窗口 `unexpected_subject_miss = 0`
  - `policy_driven_host_interception` 变成“进主体后由宿主拦截”
  - 已授权 user-visible send 前都能看到 subject finalized-result / response-plan 证据
- validation:
  - `python3 scripts/codex/lint_repo.py`
  - `python3 scripts/codex/verify_repo.py --mode fast`
  - `python3 scripts/codex/verify_repo.py --mode full`
  - fresh capture + current audit artifact refresh
- rollback note:
  - 若新窗口仍存在 authorized bypass，维持任务 open，不对外宣称修复完成

### Milestone 6: Closeout

- scope:
  - 产出 current report
  - 收平 claim ceiling
  - 记录历史红点 vs 新窗口结果
- files / areas likely touched:
  - `docs/codex/tasks/mandatory-subject-ingress-all-turns/STATUS.md`
  - 相关 current report / handoff docs
- acceptance:
  - 明确区分“历史红点”与“修复后新窗口”
  - 不把本任务写成 authority release
- validation:
  - scoped `git diff --check`
  - `python3 scripts/codex/verify_repo.py --mode full`
- rollback note:
  - closeout 文档不接受超前 claim；若 evidence 不足，保持任务 open

## Progress

- current_status: `in_progress`
- current_milestone: `Milestone 5: Verification + Fresh Real Sample Audit`
- milestone_state: `blocked_on_publish_and_fresh_real_telegram_window`

## Decision log

- 当前修复目标从“减少 Telegram 红点”收紧为 repo-level 不变量：所有已授权事件都必须 subject-aware
- 第一刀范围固定为“绝对所有事件”，不只修普通聊天
- gate 失败策略固定为硬阻断，不允许 host success fallback
- 未授权 / pre-auth 安全拒绝保留宿主前置，不进入主体
- `M1` 先只把统一 gate abstraction 落到 `openemotion_hooks`，并把 `_send_host_owned_reply()` 接进去，作为第一个 enforced host-owned path；不提前推进 `M2+` 的 pre-runtime/document/proactive closure

## Outcomes / retrospective

- `M1` 已完成：
  - 新增统一 `MandatorySubjectGate`
  - 固定 `SubjectGateVerdict`
  - `_send_host_owned_reply()` 现在必须先过 `finalized_result + response_plan`
  - hooks unavailable/disabled/failure 时，会显式送出 `subject_gate_failed`，而不是继续正常成功回复
- `M2` 当前在收口：
  - `_handle_with_runtime_v2()` 中 authorized early-return cases 已先 subject ingress
  - `pending task conflict` 已通过 subject-gated finalize path
  - `evidence followup reply` 与 `read_only_preflight` / `force_waiting_input` / `direct_reply_text` 已补齐 subject-gated finalize / response-plan 强制路径
- `M3` 已完成：
  - `handle_command()` / `_capture_command_ingress()` 已改为 mandatory subject ingress；authorized command ingress 不再是 silent best-effort
  - `_send_result()` 已改为 subject-gated host-owned finalize path，authorized command result 不再 raw send
  - `handle_document()` 的 unsupported / download failure / ingestion failure / non-runtime-v2 success reply 已统一走 subject ingress + host-owned finalize
  - `_handle_with_new_runtime()` 已在 `run_agent()` 前执行 mandatory subject ingress；`success / timeout / crash` 均走 subject-gated finalize path
- `M4` 已完成本地代码闭环：
  - `drain_pending_proactive_outbox_to_telegram()` 不再直接 raw send；现在会先构造 host-owned response plan、跑 output check、执行 `finalized_result + response_plan` subject gate，再允许真正 transport send
  - proactive/background gate 失败时不再偷偷发送；会保留 outbox 事件并返回 `held`
  - proactive transport 现在发送的是统一 egress 文本，而不是绕过 output check 的原始 draft
  - 定向 proactive transport / cycle tests 与 focused host-owned Telegram tests 已通过，`verify_repo.py --mode fast` 已通过
- `M5a` 已完成：
  - 已新增 dashboard-local preflight runner / report
  - ordinary-chat dashboard backend 路径现在可在 preflight artifact 中显式证明：
    - subject ingress
    - runtime finalized-result capture
    - runtime response-plan capture
    - response-plan / output-check presence
    - no raw send without finalize
  - 当前 preflight aggregate 已通过，但 claim ceiling 固定为 `preflight_only`
- 当前仍未证明：
  - fresh real window 已消除 authorized bypass

## Expected outcome

- authorized turn/event 不再存在“宿主先回了，主体完全不知晓”的主链漏洞
- live Telegram 新窗口中，authorized host-only success reply 应清零
- dashboard preflight 只作为发布前低成本预验证；真正 acceptance 仍由 fresh real Telegram proof 决定
