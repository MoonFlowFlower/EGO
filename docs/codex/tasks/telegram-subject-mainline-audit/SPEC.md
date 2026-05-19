# Telegram Subject Mainline Audit

## Goal

审计 Telegram 当前真实主链里哪些 turn 在宿主层提前结束，哪些已经进入主体，以及当前 live 聊天到底能证明到哪一层。

## Non-goals

- 不修改 Telegram runtime、OpenEmotion hooks、dashboard 或 evidence collector
- 不修复 `unexpected_subject_miss`
- 不改 `Tasks/*` authority 口径
- 不把 controlled-axis 能力误写成 live Telegram 成熟能力

## Constraints

- 输入只读：`artifacts/telegram_real_mainline_v1/dashboard_v1/*` 与 `artifacts/telegram_real_mainline_v1/real_telegram/*`
- `host_only` 判定沿用现有 dashboard：`bool(response_plan) and not oe_available`
- 审计报告必须区分：
  - `control_plane_expected`
  - `policy_driven_host_interception`
  - `unexpected_subject_miss`
- “普通聊天 turn” 固定定义为：
  - `raw_update.message.text` 非空
  - 不以 `/` 开头
  - 不是 profile-rule 注册语句

## Acceptance criteria

- [ ] `docs/codex/tasks/telegram-subject-mainline-audit/` 完整落地
- [ ] `scripts/codex/audit_telegram_subject_mainline.py` 能生成 current md/json 审计产物
- [ ] 报告复现当前快照基线：
  - `runs = 1097`
  - `host_only = 484`
  - `oe_available = 580`
  - `control_plane_expected = 206`
  - `policy_driven_host_interception = 228`
  - `unexpected_subject_miss = 50`
  - `telegram_subject_rows = 104`
  - `telegram_subject_revision_gt_0 = 0`
  - `telegram_subject_non_ask_modes = 0`
- [ ] 报告明确写出：
  - 当前 live Telegram 不能宣称“大多数聊天都进入主体”
  - 当前 live Telegram 不能宣称“聊天里已稳定表现出 downstream tendency change”

## Authority refs

- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- `docs/CODEX_CLOSED_LOOP_SELF_REVIEW_WORKFLOW.md`
- `README.md`
- `EgoCore/README.md`
- `OpenEmotion/README.md`
- `artifacts/telegram_real_mainline_v1/dashboard_v1/DATA_SCHEMA.md`
