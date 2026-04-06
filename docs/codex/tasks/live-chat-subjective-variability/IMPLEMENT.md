# Live Chat Subjective Variability - IMPLEMENT

## Source of truth

- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- `docs/TELEGRAM_REAL_MAINLINE_VALIDATION_V1.md`
- `artifacts/telegram_real_mainline_v1/dashboard_v1/SUBJECT_MAINLINE_AUDIT_CURRENT.md`
- `docs/codex/tasks/mandatory-subject-ingress-all-turns/STATUS.md`

## Execution rules

- 先读 `SPEC.md -> PLAN.md -> IMPLEMENT.md -> STATUS.md`
- 当前允许执行到 `M4 Host-Governed Cadence`
- 当前可写：
  - `docs/codex/tasks/live-chat-subjective-variability/*`
  - `EgoCore/app/runtime_v2/chat_reply_engine.py`
  - `EgoCore/app/response_contract/response_plan.py`
  - `EgoCore/tests/test_runtime_v2_chat_mainline.py`
  - `EgoCore/tests/test_response_contract.py`
  - `EgoCore/app/runtime_v2/*`
  - `EgoCore/app/telegram_*`
  - `EgoCore/tests/test_runtime_v2_cli_and_telegram.py`
- 不改 authority docs
- 不回写历史 real Telegram artifacts

## M1 baseline freeze rules

- baseline 会话固定为：
  - `telegram:dm:8420019401`
  - `2026-04-05 18:01:43 -> 18:11:55`
- baseline 结论必须同时满足：
  - live ordinary chat 已 subject ingress
  - tendency 近乎恒定，不足以构成强 downstream tendency proof
  - richer bounded fields 缺失
- baseline 必须显式写出当前宿主同步聊天契约：
  - `reply_authority = model_chat`
  - `reply_origin = chat_mainline`
  - `delivery_kind = chat`

## M2 completed target

- `M2` 只解决一件事：
  - 让 current Telegram mainline 在 live ordinary chat 中稳定暴露 richer bounded subject surface
- `M2` 实现目标固定为：
  - `policy_hint`
  - `response_tendency`
  - `reflection_note`
  - `social_policy_hints`
  - `embodied_policy_hints`
  - `integrated_policy_hints`
  - `initiative_policy_hints`
  都进入 current live subject surface，并在 sample artifacts / `state.proto_self_context` 中可见
- `M2` 不做：
  - prompt shaping overhaul
  - cadence autonomy
  - direct reply authority release

## M3 completed target

- `M3` 只解决一件事：
  - 让 richer bounded subject surface 真正改变 current `chat_mainline` 的 reply shaping
- `M3` 已完成的落点固定为：
  - `chat_reply_engine._build_messages()` 现在显式消费：
    - `response_tendency`
    - `reflection_note.trigger`
    - `social_policy_hints`
    - `embodied_policy_hints`
    - `integrated_policy_hints`
    - `initiative_policy_hints`
    - 最近 3 条 tendency 摘要
  - bounded `chat_expression_hint` 已进入：
    - runtime reply metadata
    - assistant history
    - response plan metadata
  - `short / normal / expand` shaping 已在 current chat mainline 生效
- `M3` 不做：
  - cadence autonomy
  - `hold_for_followup`
  - proactive substrate 改线

## Locked M4 implementation target

- `M4` 只解决一件事：
  - 在宿主治理下引入 `chat_cadence_mode`
- `M4` 实现目标固定为：
  - `reply_now_short`
  - `reply_now_normal`
  - `reply_now_expand`
  - `hold_for_followup`
- `M4` 必须满足：
  - 仍经过 mandatory subject ingress / finalized_result / response_plan
  - 对显式问题、presence check、clarification、repair feedback 禁止 `hold_for_followup`
  - `hold_for_followup` 只能进入现有 host-governed proactive substrate
- `M4` 不做：
  - direct reply authority release
  - tool authority release
  - unrestricted autonomy

## Claim ceiling

- 当前只能宣称：
  - `M1` 已完成
  - `M2` 已完成
  - `M3` 已完成
  - richer subject surface 已进入 current live artifacts
  - tendency 已开始改变 current live reply shaping
- 当前不能宣称：
  - fresh real Telegram 已证明稳定可感变化
  - host-governed cadence 已落地
  - `hold_for_followup` 已启用
  - direct reply / tool / transport authority 已放开

## Validation strategy

- `python3 -m py_compile` for touched EgoCore files
- focused pytest for current milestone
- `python3 scripts/codex/lint_repo.py`
- `python3 scripts/codex/verify_repo.py --mode fast`
- high-risk milestone closeout requires `python3 scripts/codex/verify_repo.py --mode full`

## Stopping rule

- 若当前 milestone 的定向测试不过，不推进下一 milestone
- 若 `verify_repo.py --mode fast` 不过，不推进下一 milestone
- 若高风险 milestone 需要 full verify 而 full 不过，只能在当前 milestone 内修复或降级口径
- 若需要 authority release 才能继续，直接停止；本任务不允许越过 host-governed 边界

## Final handoff checklist

- [x] long-run task package 已创建
- [x] baseline 会话已冻结
- [x] tendency 平坦结论已写明
- [x] richer fields 缺失已写明
- [x] `M2` richer subject surface 已落地
- [x] `M3` tendency-to-reply consumption 已落地并经 full verify
- [ ] `M4` host-governed cadence
- [ ] `M5` fresh real Telegram proof
- [ ] `M6` closeout
