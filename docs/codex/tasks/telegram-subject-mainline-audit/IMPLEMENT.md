# Telegram Subject Mainline Audit - IMPLEMENT

## Source of truth

- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- `artifacts/telegram_real_mainline_v1/dashboard_v1/DATA_SCHEMA.md`
- `README.md`
- `EgoCore/app/dashboard/index_builder.py`
- `EgoCore/app/telegram_runtime_bridge.py`
- `EgoCore/app/telegram_bot.py`
- `EgoCore/app/openemotion_hooks/native_hooks.py`

## Execution rules

- 先读 `SPEC.md -> PLAN.md -> IMPLEMENT.md -> STATUS.md`
- 只做只读审计，不修改 runtime 行为
- 不新增第二套 authority source；report 只引用 ledger / dashboard derived index / current code path

## Audit rules

- `control_plane_expected`:
  - `response_plan_status in {profile_rule_registered, command_result, profile_rule_unsupported, return_runtime_status}`
- `policy_driven_host_interception`:
  - `response_plan_status == profile_rule_enforced`
- `unexpected_subject_miss`:
  - `response_plan_status in {pre_runtime, delivered_without_explicit_plan, chat, evidence_followup}`
  - 或任何未映射状态
- ordinary chat:
  - text 非空
  - 不以 `/` 开头
  - 不属于 profile-rule 注册语句

## Validation strategy

- `python3 -m py_compile scripts/codex/audit_telegram_subject_mainline.py`
- `python3 scripts/codex/audit_telegram_subject_mainline.py`
- `python3 scripts/codex/lint_repo.py`
- `python3 scripts/codex/verify_repo.py --mode fast`

## Stopping rule

- 如果 current report 无法复现快照统计，先修脚本，不下结论
- 如果审计发现 authority source 与 live path 表述冲突，只记录 drift，不在本轮修文档

## Final handoff checklist

- [x] current md/json 报告已生成
- [x] host-only 三分法统计已落盘
- [x] ordinary chat unexpected misses 已列样本
- [x] subject ingress 与 downstream tendency claim ceiling 已收平
