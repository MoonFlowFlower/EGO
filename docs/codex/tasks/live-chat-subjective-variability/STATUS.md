# Live Chat Subjective Variability - STATUS

## Current milestone

- name: `Milestone 4: Host-Governed Cadence`
- owner: `Codex`
- state: pending

## Current state

- current_layer: `repo_live_chat_corrective_slice`
- main_chain_status: `tendency_consumption_present`
- completion_class: `verify_passed`

## Completed work

- 新建 long-run task package：
  - `SPEC.md`
  - `PLAN.md`
  - `IMPLEMENT.md`
  - `STATUS.md`
- 冻结 baseline 会话：
  - `session = telegram:dm:8420019401`
  - time window = `2026-04-05 18:01:43 -> 18:11:55`
  - sample range = `sample_20260405_180143_60904195` -> `sample_20260405_181155_09ded249`
- 冻结 baseline 结论：
  - ordinary chat turn 已持续 ingress 到主体
  - 当前 live Telegram chat 仍由宿主同步聊天契约主导：
    - `reply_authority = model_chat`
    - `reply_origin = chat_mainline`
    - `delivery_kind = chat`
  - 13 个 ordinary chat turn 的 tendency 基本恒定：
    - `preferred_mode = ask`
    - `preferred_tone = cautious`
    - `suggested_next_step = prioritize_closure`
  - 当前 richer bounded fields 在 live sample 中缺失：
    - `social_policy_hints`
    - `embodied_policy_hints`
    - `integrated_policy_hints`
    - `initiative_policy_hints`
- 锁定 `M2` 只做 richer subject surface，不提前做 M3/M4
- `M2 Rich Subject Surface` 已完成：
  - `RuntimeV2ProtoSelfRuntime` 现在会在 ingress / external_result / finalized_result / idle_check / developmental_tick 路径上显式规范 richer bounded subject fields
  - richer result fields 在 capture 时即使上游未提供，也会显式保留为 `{}`：
    - `social_policy_hints`
    - `embodied_policy_hints`
    - `integrated_policy_hints`
    - `initiative_policy_hints`
  - richer trace fields 在 capture 时即使上游未提供，也会显式保留为 `{}`：
    - `social_context`
    - `environment_context`
    - `selfhood_integration_context`
    - `initiative_realization_context`
    - `host_proactive_context`
  - focused runtime/evidence tests 已补齐 explicit-empty-field 断言
- `M3 Tendency-to-Reply Consumption` 已完成：
  - `chat_reply_engine` 现在会把 richer bounded subject surface、`reflection_note.trigger`、最近 3 条 tendency 摘要、以及 bounded `chat_expression_hint` 显式带入 live chat payload
  - `chat_mainline` 现在会把 `chat_expression_hint` 和 `response_tendency_summary` 写入：
    - runtime reply metadata
    - assistant history
    - response plan metadata
  - `short / normal / expand` reply shaping 已在 current chat mainline 生效
  - `presence_check` 等 ordinary chat 已能通过结构化 hint 改变实际 reply 长度，而不只是把 tendency 留在日志里
  - repo-wide `verify_repo.py --mode full` 已重新跑通，没有引入新的 collection / mainline regression

## Open risks

- 当前 baseline 已说明“主体已 ingress”，但还没有 live 可感变化证据
- 当前 baseline 仍不能证明 chat-level downstream tendency change 强成立
- 当前 corrective slice 仍依赖 `mandatory-subject-ingress-all-turns` 的后续 background/proactive closure，不能把两条任务线混成同一 claim
- 当前还没有 host-governed cadence choice；那是 `M4` 的范围
- 当前还没有 fresh real Telegram window 证明同一 session 内已经出现稳定 tendency / cadence 差异；那是 `M5` 的范围

## Next step

- 进入 `M4 Host-Governed Cadence`
- 在 `response_contract` 和 current Telegram mainline 上引入 `chat_cadence_mode`
- 先保持 host-governed，不放开 direct reply / tool / transport authority
- `hold_for_followup` 只能在 ordinary chat + host policy allow 的条件下启用

## Last validation results

- mode: `Milestone 3 tendency-to-reply consumption`
- result: `pass`
- summary:
  - `chat_reply_engine` 的 richer payload / recent tendency summary / bounded `chat_expression_hint` 已接到 current chat mainline
  - `response_plan` 现在会保留 `chat_expression_hint` 和 `response_tendency_summary`
  - targeted M3 tests、repo lint、`verify_repo.py --mode fast`、`verify_repo.py --mode full` 全部通过
  - `M3` 证明的是 tendency 已开始改变 live reply shaping；还不证明 cadence autonomy 或 fresh real Telegram 可感变化已成立

## Commands run / evidence

- `sed -n '1,160p' PROJECT_MEMORY.md`
- `sed -n '1,200p' docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- `sed -n '1,200p' docs/CODEX_CLOSED_LOOP_SELF_REVIEW_WORKFLOW.md`
- `sed -n '1,220p' README.md`
- `sed -n '1,220p' EgoCore/README.md`
- `sed -n '1,220p' Tasks/MVS_task_plan.md`
- `sed -n '1,240p' docs/TELEGRAM_REAL_MAINLINE_VALIDATION_V1.md`
- `sed -n '1,260p' artifacts/telegram_real_mainline_v1/dashboard_v1/SUBJECT_MAINLINE_AUDIT_CURRENT.md`
- `sed -n '1,220p' docs/codex/tasks/mandatory-subject-ingress-all-turns/STATUS.md`
- `python3 - <<'PY' ...` against `artifacts/telegram_real_mainline_v1/real_telegram/sample_20260405_18*`
- `git diff --check -- docs/codex/tasks/live-chat-subjective-variability`
- `python3 -m py_compile EgoCore/app/runtime_v2/proto_self_runtime.py EgoCore/tests/test_runtime_v2_proto_self_runtime.py EgoCore/tests/test_telegram_proto_self_v2_evidence.py`
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_runtime_v2_proto_self_runtime.py EgoCore/tests/test_telegram_proto_self_v2_evidence.py -q -s`
- `python3 -m py_compile EgoCore/app/runtime_v2/chat_reply_engine.py EgoCore/app/response_contract/response_plan.py EgoCore/tests/test_runtime_v2_chat_mainline.py EgoCore/tests/test_response_contract.py`
- `PYTHONPATH=EgoCore:EgoCore/modules:OpenEmotion python3 -m pytest EgoCore/tests/test_runtime_v2_chat_mainline.py EgoCore/tests/test_response_contract.py -q -s`
- `python3 scripts/codex/lint_repo.py`
- `python3 scripts/codex/verify_repo.py --mode fast`
- `python3 scripts/codex/verify_repo.py --mode full`

## Claim ceiling

- 当前只能宣称：
  - `M1 Baseline Freeze` 已完成
  - `M2 Rich Subject Surface` 已完成
  - `M3 Tendency-to-Reply Consumption` 已完成
  - richer bounded subject fields 已进入 current live-artifact surface
  - tendency 已开始进入 current live reply shaping
  - full verify 当前为 green
- 当前不能宣称：
  - live Telegram chat 已具备稳定可感变化
  - host-governed cadence 已落地
  - `hold_for_followup` 已启用
  - unrestricted autonomy / direct reply authority release
