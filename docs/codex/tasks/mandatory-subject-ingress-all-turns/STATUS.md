# Mandatory Subject Ingress For All Authorized Turns - STATUS

## Current milestone

- name: `Milestone 4: Background / Proactive Closure`
- owner: `Codex`
- state: pending

## Current state

- current_layer: `repo_mainline_repair`
- main_chain_status: `command_document_legacy_closure_landed`
- completion_class: `verify_passed`

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
- 受影响测试已同步到新不变量：
  - command/session tests 默认不再假设“无 gate 也能成功回复”
  - context/profile continuity tests 已显式安装 allow gate，避免把旧 best-effort 预期误当成当前正确行为

## Open risks

- `telegram_bot.py` 里的 background/proactive user-visible send path 仍未 closure，`M4` 前仍可能存在 authorized bypass
- fresh real sample acceptance 依赖新采样窗口；历史红点不会自动消失
- 文档 closeout 时必须防止 wording drift，把“主体知晓”误写成“authority 已释放”

## Next step

- 进入 `M4 Background / Proactive Closure`
- 把 proactive/system user-visible send path 接到同一套 mandatory subject finalize / response-plan 规则
- 完成后再跑 fresh capture window，不能提前把历史红点当作已修复

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

## Claim ceiling

- 当前只能宣称：
  - `M1 Subject Gate Skeleton` 已完成
  - `M2 Telegram Runtime_V2 Early-Return Closure` 已完成
  - `M3 Command / Document / Legacy Closure` 已完成
  - 统一 gate abstraction 已建立
  - `_send_host_owned_reply()` 已成为第一条 enforced host-owned path
- 当前不能宣称：
  - 已修复所有 authorized bypass
  - 已实现包含 background/proactive 在内的全域 mandatory subject ingress
  - live 新窗口已变绿
