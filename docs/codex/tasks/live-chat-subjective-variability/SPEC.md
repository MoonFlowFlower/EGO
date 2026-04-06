# Live Chat Subjective Variability

## Goal

把当前 live Telegram chat 的“主体已 ingress 但用户几乎感受不到结构变化”问题收成一个 repo-level corrective slice，并先冻结可复跑的 `M1 Baseline Freeze`。

## Non-goals

- 不修改 `EgoCore/`、`OpenEmotion/`、`Tasks/*` 或任何运行时代码
- 不在本轮实现 richer subject surface、tendency consumption、cadence contract
- 不把 controlled-axis 能力误写成 live Telegram 已成熟能力
- 不把 host-governed chat corrective slice 升格成新的 `WP`

## Constraints

- 当前任务只允许写：`docs/codex/tasks/live-chat-subjective-variability/*`
- baseline 会话固定为：
  - `session = telegram:dm:8420019401`
  - 时间窗：`2026-04-05 18:01:43 -> 2026-04-05 18:11:55`
- baseline 事实必须同时写明：
  - 该会话普通聊天 turn 已进入主体
  - tendency 几乎恒定
  - live sample 缺少 richer bounded fields
- 必须锁定 `M2` 的实现目标和 claim ceiling，但不得开始实现 `M2+`

## Baseline facts to freeze

- 会话样本范围：
  - `/new`: `sample_20260405_180138_fd6b4b0f`
  - ordinary chat turn: `sample_20260405_180143_60904195` -> `sample_20260405_181155_09ded249`
- 已成立：
  - 这段真实会话在 ordinary chat turn 上持续产出 `openemotion_result.json`、`openemotion_trace.json`、`response_plan.json`
  - ordinary chat turn 当前都显示 `oe_available = true`
  - `response_plan.status = chat`
  - live chat 仍由宿主同步聊天契约主导：
    - `reply_authority = model_chat`
    - `reply_origin = chat_mainline`
    - `delivery_kind = chat`
- tendency 基线：
  - 13 个 ordinary chat turn 基本都保持：
    - `preferred_mode = ask`
    - `preferred_tone = cautious`
    - `suggested_next_step = prioritize_closure`
  - 当前 live baseline 不构成“可感的 downstream tendency change 强证明”
- richer fields 缺失基线：
  - `social_policy_hints = null`
  - `embodied_policy_hints = null`
  - `integrated_policy_hints = null`
  - `initiative_policy_hints = null`

## Acceptance criteria

- [ ] `docs/codex/tasks/live-chat-subjective-variability/` 已完整落地
- [ ] `SPEC.md / PLAN.md / IMPLEMENT.md / STATUS.md` 只收 `M1 Baseline Freeze`
- [ ] 已把 `telegram:dm:8420019401` 的 `2026-04-05 18:01:43 -> 18:11:55` 会话冻结成 baseline
- [ ] 文档明确写出：
  - ordinary chat 已 ingress
  - tendency 几乎恒定
  - richer fields 缺失
- [ ] 文档已锁定 `M2 Rich Subject Surface` 的实现目标
- [ ] 文档已锁定当前 claim ceiling：
  - 不能宣称 live Telegram chat 已稳定体现 subject-driven variability
  - 不能宣称 cadence autonomy 已实现
  - 不能宣称 direct reply / tool / transport authority release

## Authority refs

- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- `docs/CODEX_CLOSED_LOOP_SELF_REVIEW_WORKFLOW.md`
- `README.md`
- `EgoCore/README.md`
- `Tasks/MVS_task_plan.md`
- `docs/TELEGRAM_REAL_MAINLINE_VALIDATION_V1.md`
- `artifacts/telegram_real_mainline_v1/dashboard_v1/SUBJECT_MAINLINE_AUDIT_CURRENT.md`
- `docs/codex/tasks/mandatory-subject-ingress-all-turns/STATUS.md`
