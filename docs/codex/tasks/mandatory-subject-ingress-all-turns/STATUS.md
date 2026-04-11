# Mandatory Subject Ingress For All Authorized Turns - STATUS

## Current milestone

- name: `Milestone 5: Verification + Fresh Real Sample Audit`
- owner: `Codex`
- state: blocked_on_publish_and_fresh_real_telegram_window

## Current state

- current_layer: `repo_mainline_repair`
- main_chain_status: `dashboard_preflight_passed`
- completion_class: `targeted_verify_passed`

## Completed work

- 锁定问题定义：当前缺口不是“Telegram 某些 turn 体验不佳”，而是 authorized event 还存在宿主绕开主体的主链漏洞
- 锁定唯一不变量：所有已授权事件都必须先 ingress 到 OpenEmotion，再允许宿主现实裁决
- 锁定三项硬决策：
  - 第一刀范围：`绝对所有事件`
  - gate 失败：`硬阻断`
  - 未授权 / pre-auth 安全拒绝：`宿主前置，不进入主体`
- 新建 long-run task package：`SPEC.md / PLAN.md / IMPLEMENT.md / STATUS.md`
- 新增 `EgoCore/app/openemotion_hooks/subject_gate.py`
- `TelegramBot._send_host_owned_reply()` 现在会通过统一 gate 执行 `finalized_result + response_plan`
- 新增 `EgoCore/tests/test_subject_gate.py`
- 新增/更新 Telegram 定向 tests，验证：
  - host-owned helper 成功路径会经过 gate
  - gate 失败会显式返回 `subject_gate_failed`
- `M2` 已完成：
  - `_handle_with_runtime_v2()` 中 authorized early-return cases 已先 subject ingress
  - `pending task conflict` 已通过 subject-gated finalize path
  - `evidence followup reply` 与 `read_only_preflight` / `force_waiting_input` / `direct_reply_text` 已补齐 subject-gated finalize / response-plan 强制路径
- `M3` 已完成：
  - `_capture_command_ingress()` 已升级为 mandatory subject ingress；authorized command ingress 不再是 silent best-effort
  - `_send_result()` 已统一走 subject-gated host-owned finalize / response-plan
  - `handle_document()` 的 unsupported / download failure / ingestion failure / non-runtime-v2 success reply 已 subject-gated
  - `_handle_with_new_runtime()` 已在 `run_agent()` 前执行 mandatory subject ingress；`success / timeout / crash` 均保持 subject-gated finalize
- `M4` 已完成本地代码闭环：
  - `drain_pending_proactive_outbox_to_telegram()` 不再直接 raw send；现在会先构造 host-owned response plan、跑 output check、执行 `finalized_result + response_plan` subject gate，再允许真正 transport send
  - proactive/background gate 失败时不再偷偷发送；会保留 outbox 事件并返回 `held`
  - proactive transport 现在发送的是统一 egress 文本，而不是绕过 output check 的原始 draft
  - 定向 proactive transport / cycle tests 与 focused host-owned Telegram tests 已通过，`verify_repo.py --mode fast` 已通过
- `M5a Dashboard Preflight` 已通过：
  - 新增 in-process dashboard preflight runner，直接驱动 `DashboardChatService`，不依赖浏览器或常驻 server
  - ordinary-chat dashboard backend 路径现在会保留 subject ingress、runtime finalized-result capture、runtime response-plan capture、response-plan / output-check、以及 bounded richer debug surface
  - current preflight artifact:
    - `artifacts/telegram_real_mainline_v1/dashboard_v1/LIVE_INGRESS_DASHBOARD_PREFLIGHT_CURRENT.md`
    - `artifacts/telegram_real_mainline_v1/dashboard_v1/LIVE_INGRESS_DASHBOARD_PREFLIGHT_CURRENT.json`
  - aggregate verdict:
    - `ordinary_chat_mainline = 5`
    - `ordinary_chat_with_richer_fields = 5`
    - `tendency_delta_present = true`
    - `cadence_delta_present = true`
    - `hold_for_followup_artifact = true`
    - `subject_gate_all_ingress_ok = true`
    - `response_contract_present = true`
    - `no_raw_send_without_finalize = true`
    - `acceptance_met = true`
  - claim ceiling 固定为：
    - `source = dashboard_local_preflight`
    - `claim_ceiling = preflight_only`
- 受影响测试已同步到新不变量：
  - command/session tests 默认不再假设“无 gate 也能成功回复”
  - context/profile continuity tests 已显式安装 allow gate，避免把旧 best-effort 预期误当成当前正确行为

## Open risks

- fresh real sample acceptance 依赖新采样窗口；历史红点不会自动消失
- 文档 closeout 时必须防止 wording drift，把“主体知晓”误写成“authority 已释放”
- 当前还没有 fresh real Telegram audit 证明：
  - 新窗口 `unexpected_subject_miss = 0`
  - `policy_driven_host_interception` 已统一成“进主体后由宿主拦截”
  - proactive/system user-visible send 的 fresh live 窗口已不再绕过 subject finalize
- dashboard preflight 只证明 bounded backend 预验证，不证明 live Telegram transport 结果
- clean-worktree 上的 `python3 scripts/codex/verify_repo.py --mode fast` 当前没有过：
  - 失败点在 `OpenEmotion test_smoke.py`
  - 直接报错是 `127.0.0.1:18080/health` connection refused
  - 当前更像 repo-local OpenEmotion smoke 环境阻塞，而不是本 tranche 的 targeted regression，但在 smoke 绿之前不能把 repo fast gate 记成 pass

## Next step

- 在发布当前 patch 后采一个 fresh real Telegram 窗口：
  - 先 `/new`
  - 再发 ordinary chat：
    - `你好`
    - `我现在有点卡住了，你先帮我理一下`
    - `继续`
    - `你刚才为什么那样回答`
- 然后重跑：
  - `python3 scripts/codex/prove_live_chat_subjective_variability.py --since-commit <publish_commit>`
  - 并刷新当前 `subject_mainline_audit_current` 的既有 audit artifact/workflow
- 只有 fresh 窗口同时证明 live audit 与 ordinary-chat proof 条件都过线，才进入 `M6 Closeout`

## Last validation results

- mode: `Milestone 1 closeout`
- result: `pass`
- summary:
  - 统一 subject gate abstraction 已落地
  - `_send_host_owned_reply()` 已接入 subject gate
  - `python3 -m py_compile` pass
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_subject_gate.py EgoCore/tests/test_runtime_v2_cli_and_telegram.py -q -s` pass
  - `python3 scripts/codex/lint_repo.py` pass
  - `python3 scripts/codex/verify_repo.py --mode fast` pass
  - scoped `git diff --check` 已通过
- mode: `Milestone 3 closeout`
- result: `pass`
- summary:
  - command/document/new_runtime paths 已接到同一套 mandatory subject ingress / finalize gate
  - `python3 -m py_compile EgoCore/app/telegram_bot.py EgoCore/tests/test_telegram_session_commands.py EgoCore/tests/test_runtime_v2_cli_and_telegram.py EgoCore/tests/test_telegram_context_command.py EgoCore/tests/test_profile_rule_continuity.py` pass
  - focused M3 node set pass (`16 passed`)
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_telegram_session_commands.py -q -s` pass
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_runtime_v2_cli_and_telegram.py -q -s` pass
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_telegram_context_command.py -q -s` pass
  - `python3 scripts/codex/lint_repo.py` pass
  - `python3 scripts/codex/verify_repo.py --mode fast` pass
  - scoped `git diff --check` 已通过
- mode: `Milestone 4 targeted closeout`
- result: `pass`
- summary:
  - proactive/background user-visible send path 现在先走 host-owned response plan + output check + `finalized_result + response_plan` subject gate，再允许真正 transport send
  - gate 失败时 outbox 事件会保留并返回 `held`，不再静默发送
  - `python3 -m py_compile EgoCore/app/telegram_bot.py EgoCore/tests/test_telegram_proactive_transport.py EgoCore/tests/test_host_governed_proactive_telegram_cycle.py` pass
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_telegram_proactive_transport.py EgoCore/tests/test_host_governed_proactive_telegram_cycle.py -q -s` pass (`8 passed`)
  - `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest --basetemp=/tmp/ego_tranche_pytest EgoCore/tests/test_runtime_v2_cli_and_telegram.py::test_telegram_bot_chat_hold_for_followup_queues_outbox_without_immediate_send EgoCore/tests/test_runtime_v2_cli_and_telegram.py::test_telegram_bot_chat_hold_for_followup_blocked_for_explicit_question EgoCore/tests/test_runtime_v2_cli_and_telegram.py::test_telegram_bot_host_owned_reply_captures_explicit_response_plan EgoCore/tests/test_runtime_v2_cli_and_telegram.py::test_telegram_bot_host_owned_reply_blocks_when_subject_gate_fails EgoCore/tests/test_runtime_v2_cli_and_telegram.py::test_telegram_bot_new_runtime_direct_reply_uses_runtime_authority_metadata -q -s` pass (`5 passed`)
  - `python3 scripts/codex/lint_repo.py` pass
  - `python3 scripts/codex/verify_repo.py --mode fast` pass
  - scoped `git diff --check` 已通过
- mode: `Milestone 5a dashboard preflight`
- result: `pass`
- summary:
  - dashboard-local preflight 现在能在 bounded backend 上证明 ordinary-chat path 经历了 subject ingress、runtime finalized-result capture、runtime response-plan capture、response-plan / output-check，以及 bounded richer fields / cadence debug surface
  - `python3 -m py_compile EgoCore/app/repo_paths.py EgoCore/app/dashboard/chat_service.py EgoCore/app/dashboard/preflight.py scripts/codex/run_dashboard_chat_preflight.py EgoCore/tests/test_dashboard_chat_service.py EgoCore/tests/test_dashboard_preflight.py` pass
  - `PYTHONPATH=/mnt/d/Project/AIProject/worktrees/ego-dashboard-preflight:/mnt/d/Project/AIProject/worktrees/ego-dashboard-preflight/EgoCore:/mnt/d/Project/AIProject/worktrees/ego-dashboard-preflight/EgoCore/modules:/mnt/d/Project/AIProject/worktrees/ego-dashboard-preflight/OpenEmotion python3 -m pytest --basetemp=/tmp/ego_dashboard_preflight_pytest EgoCore/tests/test_dashboard_chat_service.py EgoCore/tests/test_dashboard_preflight.py EgoCore/tests/test_telegram_proactive_transport.py EgoCore/tests/test_host_governed_proactive_telegram_cycle.py -q -s` pass (`15 passed`)
  - `python3 scripts/codex/run_dashboard_chat_preflight.py` pass
  - artifact verdict = `dashboard preflight passed`, `source = dashboard_local_preflight`, `claim_ceiling = preflight_only`
- mode: `repo-level fast verification after authority sync`
- result: `blocked`
- summary:
  - `python3 scripts/codex/generate_program_state_views.py` pass
  - `python3 scripts/codex/check_program_state_integrity.py --skip-diff-check` pass
  - `python3 scripts/codex/lint_repo.py` pass
  - `git diff --check` pass
  - `python3 scripts/codex/verify_repo.py --mode fast` failed on `OpenEmotion/test_smoke.py`
  - direct error: `HTTPConnectionPool(host='127.0.0.1', port=18080): Max retries exceeded with url: /health`
  - 当前按 repo-local OpenEmotion smoke blocker 记录，不能把 repo fast gate 记成 green

## Commands run / evidence

- `sed -n '1,220p' PROJECT_MEMORY.md`
- `sed -n '1,220p' docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- `sed -n '1,220p' docs/CODEX_CLOSED_LOOP_SELF_REVIEW_WORKFLOW.md`
- `sed -n '1,220p' README.md`
- `sed -n '1,220p' EgoCore/README.md`
- `sed -n '1,220p' docs/codex/tasks/telegram-subject-mainline-audit/SPEC.md`
- `sed -n '1,220p' docs/codex/tasks/telegram-subject-mainline-audit/PLAN.md`
- `sed -n '1,220p' docs/codex/tasks/telegram-subject-mainline-audit/IMPLEMENT.md`
- `sed -n '1,220p' docs/codex/tasks/telegram-subject-mainline-audit/STATUS.md`
- `rg -n "def _handle_with_runtime_v2|def _handle_with_new_runtime|def handle_command|def _send_result|run_host_governed_proactive_telegram_cycle|def _maybe_handle_runtime_v2_pre_runtime|def _capture_command_ingress|def process_ingress|def process_finalized_result|def capture_response_plan|def process_idle_check" EgoCore/app EgoCore/tests -S`
- `python3 -m py_compile EgoCore/app/openemotion_hooks/subject_gate.py EgoCore/app/openemotion_hooks/__init__.py EgoCore/app/telegram_bot.py EgoCore/tests/test_subject_gate.py EgoCore/tests/test_runtime_v2_cli_and_telegram.py`
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_subject_gate.py EgoCore/tests/test_runtime_v2_cli_and_telegram.py -q -s`
- `python3 scripts/codex/lint_repo.py`
- `python3 scripts/codex/verify_repo.py --mode fast`
- `git diff --check -- EgoCore/app/openemotion_hooks/subject_gate.py EgoCore/app/openemotion_hooks/__init__.py EgoCore/app/telegram_bot.py EgoCore/tests/test_subject_gate.py EgoCore/tests/test_runtime_v2_cli_and_telegram.py`
- `python3 -m py_compile EgoCore/app/telegram_bot.py EgoCore/tests/test_telegram_session_commands.py EgoCore/tests/test_runtime_v2_cli_and_telegram.py EgoCore/tests/test_telegram_context_command.py EgoCore/tests/test_profile_rule_continuity.py`
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest -q -s EgoCore/tests/test_telegram_session_commands.py::test_new_command_captures_real_command_ingress EgoCore/tests/test_telegram_session_commands.py::test_command_results_use_subject_gate EgoCore/tests/test_telegram_session_commands.py::test_command_ingress_failure_blocks_reply EgoCore/tests/test_telegram_session_commands.py::test_task_conflict_command_results_use_subject_gate EgoCore/tests/test_telegram_session_commands.py::test_replace_command_subject_gates_command_ingress_before_runtime EgoCore/tests/test_runtime_v2_cli_and_telegram.py::test_telegram_bot_new_runtime_direct_reply_uses_runtime_authority_metadata EgoCore/tests/test_runtime_v2_cli_and_telegram.py::test_telegram_bot_new_runtime_blocks_when_subject_ingress_fails EgoCore/tests/test_runtime_v2_cli_and_telegram.py::test_handle_document_failure_paths_use_subject_gate EgoCore/tests/test_runtime_v2_cli_and_telegram.py::test_handle_document_non_runtime_v2_success_uses_subject_gate`
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_telegram_session_commands.py -q -s`
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_runtime_v2_cli_and_telegram.py -q -s`
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_telegram_context_command.py -q -s`
- `python3 scripts/codex/lint_repo.py`
- `python3 scripts/codex/verify_repo.py --mode fast`
- `git diff --check -- EgoCore/app/telegram_bot.py EgoCore/tests/test_telegram_session_commands.py EgoCore/tests/test_runtime_v2_cli_and_telegram.py EgoCore/tests/test_telegram_context_command.py EgoCore/tests/test_profile_rule_continuity.py`
- `python3 -m py_compile EgoCore/app/telegram_bot.py EgoCore/tests/test_telegram_proactive_transport.py EgoCore/tests/test_host_governed_proactive_telegram_cycle.py`
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_telegram_proactive_transport.py EgoCore/tests/test_host_governed_proactive_telegram_cycle.py -q -s`
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest --basetemp=/tmp/ego_tranche_pytest EgoCore/tests/test_runtime_v2_cli_and_telegram.py::test_telegram_bot_chat_hold_for_followup_queues_outbox_without_immediate_send EgoCore/tests/test_runtime_v2_cli_and_telegram.py::test_telegram_bot_chat_hold_for_followup_blocked_for_explicit_question EgoCore/tests/test_runtime_v2_cli_and_telegram.py::test_telegram_bot_host_owned_reply_captures_explicit_response_plan EgoCore/tests/test_runtime_v2_cli_and_telegram.py::test_telegram_bot_host_owned_reply_blocks_when_subject_gate_fails EgoCore/tests/test_runtime_v2_cli_and_telegram.py::test_telegram_bot_new_runtime_direct_reply_uses_runtime_authority_metadata -q -s`
- `PYTHONPATH=/mnt/d/Project/AIProject/worktrees/ego-dashboard-preflight:/mnt/d/Project/AIProject/worktrees/ego-dashboard-preflight/EgoCore:/mnt/d/Project/AIProject/worktrees/ego-dashboard-preflight/EgoCore/modules:/mnt/d/Project/AIProject/worktrees/ego-dashboard-preflight/OpenEmotion python3 -m pytest --basetemp=/tmp/ego_dashboard_preflight_pytest EgoCore/tests/test_dashboard_chat_service.py EgoCore/tests/test_dashboard_preflight.py EgoCore/tests/test_telegram_proactive_transport.py EgoCore/tests/test_host_governed_proactive_telegram_cycle.py -q -s`
- `python3 scripts/codex/run_dashboard_chat_preflight.py`
- `python3 scripts/codex/generate_program_state_views.py`
- `python3 scripts/codex/check_program_state_integrity.py --skip-diff-check`
- `python3 scripts/codex/lint_repo.py`
- `python3 scripts/codex/verify_repo.py --mode fast`
- `git diff --check`

## Claim ceiling

- 当前只能宣称：
  - `M1 Subject Gate Skeleton` 已完成
  - `M2 Telegram Runtime_V2 Early-Return Closure` 已完成
  - `M3 Command / Document / Legacy Closure` 已完成
  - `M4 Background / Proactive Closure` 已完成本地代码与定向验证
  - `M5a Dashboard Preflight` 已通过，且明确属于 `dashboard_local_preflight / preflight_only`
  - 统一 gate abstraction 已建立
  - `_send_host_owned_reply()` 已成为第一条 enforced host-owned path
- 当前不能宣称：
  - 已修复所有 authorized bypass
  - live 新窗口已变绿
  - dashboard preflight 已替代 fresh real Telegram audit
  - repo-level `verify_repo.py --mode fast` 当前为 green
