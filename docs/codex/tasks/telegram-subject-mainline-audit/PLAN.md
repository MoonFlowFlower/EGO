# Telegram Subject Mainline Audit - PLAN

## Task summary

这是一个只读审计任务。目标不是证明仓里有没有能力，而是把 live Telegram 聊天为什么大量停在宿主层、哪些样本确实进了主体、以及 live 证据到底缺什么，固化成可复跑 current report。

## Milestones

### Milestone 1: Audit Harness

- scope:
  - 新增只读审计脚本
  - 固定 host-only 三分法
  - 固定 ordinary chat 定义
- files / areas likely touched:
  - `scripts/codex/`
- acceptance:
  - 能从 dashboard / real_telegram 样本重建统计
  - 能输出 md/json current report
- validation:
  - `python3 -m py_compile scripts/codex/audit_telegram_subject_mainline.py`
  - `python3 scripts/codex/audit_telegram_subject_mainline.py`

### Milestone 2: Current Audit Report

- scope:
  - 生成 current md/json 报告
  - 固定 wording drift 检查
  - 固定 representative sample 提取
- files / areas likely touched:
  - `artifacts/telegram_real_mainline_v1/dashboard_v1/`
  - `docs/codex/tasks/telegram-subject-mainline-audit/STATUS.md`
- acceptance:
  - current report 复现快照基线
  - 报告明确区分 ingress proved 与 downstream tendency proved
- validation:
  - `python3 scripts/codex/lint_repo.py`
  - `python3 scripts/codex/verify_repo.py --mode fast`

## Progress

- current_status: `completed`
- current_milestone: `Milestone 2: Current Audit Report`
- milestone_state: `completed`

## Decision log

- `host_only` 不重定义，直接沿用 dashboard 现有口径
- `profile_rule_enforced` 不归入 control-plane；单列成 `policy_driven_host_interception`
- live Telegram tendency 证明只认 `session_id` 为 `telegram:*` 的 growth/tendency 样本

## Expected outcome

- 给出一份当前可引用的审计结论
- 说明 live Telegram 真实断层在宿主 pre-runtime / policy interception，而不是简单归咎于“用户感觉不敏感”

## Outcome

- current report 已生成：
  - `artifacts/telegram_real_mainline_v1/dashboard_v1/SUBJECT_MAINLINE_AUDIT_CURRENT.md`
  - `artifacts/telegram_real_mainline_v1/dashboard_v1/SUBJECT_MAINLINE_AUDIT_CURRENT.json`
- 当前结论已冻结：
  - `host_only = 484` 且不只是控制面噪声
  - ordinary chat 中存在 `unexpected_subject_miss`
  - live Telegram chat 有 subject ingress 证据，但 downstream tendency change 只有弱结构信号，没有强证明
