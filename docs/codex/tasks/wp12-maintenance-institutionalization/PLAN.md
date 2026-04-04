# WP12 Maintenance Institutionalization - PLAN

## Task summary

这是一个 `收口/治理` 层任务，不新增 `WP12` 能力，只把现有 maintenance baseline 变成可重复执行、可机器校验、可绑定发布口径的 institutionalized maintenance。

## Milestones

### Milestone 1: Runner And Gate

- scope:
  - 新增 canonical maintenance runner
  - 新增 non-mutating publish gate verifier
  - 新增 institutionalization 定向测试
- files / areas likely touched:
  - `scripts/codex/`
  - `OpenEmotion/tests/mvp17/`
- acceptance:
  - runner 能生成 `MAINTENANCE_VERIFICATION_CURRENT.md/.json`
  - gate verifier 能校验 baseline/report/ledger/claim ceiling
- validation:
  - `python3 -m py_compile scripts/codex/run_wp12_maintenance_verification.py scripts/codex/verify_wp12_maintenance_gate.py`
  - `PYTHONPATH=OpenEmotion pytest -q -s --noconftest OpenEmotion/tests/mvp17/test_wp12_maintenance_gate.py`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- rollback note:
  - 回退到没有 canonical runner/gate 的 `WP12` maintenance baseline 状态

### Milestone 2: First Institutionalized Maintenance Verification

- scope:
  - 真实执行 canonical runner
  - 刷新 `MAINTENANCE_VERIFICATION_CURRENT.*`
  - 在 ledger 记录第一次 baseline-driven maintenance verification
  - 更新 `WP12` maintenance docs 与 publish rule
- files / areas likely touched:
  - `Tasks/active/mvp17_social_self_other_modeling/*`
  - `AGENTS.md`
- acceptance:
  - gate verifier 返回 `publish_gate_ready = true`
  - docs 仍明确 `maintenance_mode` 与不可宣称项
- validation:
  - `PYTHONPATH=OpenEmotion python3 scripts/codex/run_wp12_maintenance_verification.py`
  - `python3 scripts/codex/verify_wp12_maintenance_gate.py --json`
  - `python3 scripts/codex/lint_repo.py`
  - `python3 scripts/codex/verify_repo.py --mode fast`
  - `python3 scripts/codex/verify_repo.py --mode full`
- rollback note:
  - 删除 institutionalized maintenance current report 与 ledger entry，恢复为 pre-institutionalization docs state

## Progress

- current_status: `completed`
- current_milestone: `Milestone 2: First Institutionalized Maintenance Verification`
- milestone_state: `completed`

## Decision log

- 2026-04-04: 当前主线先做 `WP12` institutionalization，不开 `WP13` authority package；避免在 `WP12` maintenance_mode 未制度化前继续扩 phase
- 2026-04-04: 不修改 repo evidence model；“`WP12 -> E6`”只作为治理里程碑，不新增 `V/E` 等级
- 2026-04-04: institutionalization 采用 `local + publish`，不新开 GitHub workflow

## Surprises / discoveries

- `WP12` 已有 QA baseline 和 maintenance ledger，但缺 canonical runner、machine-checkable gate 和 current maintenance verification report
- 仓库里最接近的样板是 `WP10` 的 maintenance verification report，而不是 repo-global publish gate

## Outcomes / retrospective

- 本轮已证明：
  - `WP12` maintenance baseline 已进入 canonical runner + local publish gate 约束
  - 第一份 baseline-driven maintenance verification 已落盘并写入 ledger
- 还没证明：
  - repo-global CI institutionalization
  - `WP13` 的 authority/package
- 观察性 residuals：
  - `python3 scripts/codex/verify_repo.py --mode full` 仍暴露既有非 `WP12` 失败面：
    - EgoCore pytest collection 中 `openemotion` / `EgoCore` import 相关错误
    - OpenEmotion Windows runtime 缺 `dotenv`
    - 旧 `mvp16_daily_check` 导入错误
    - EgoCore Telegram mainline regression 跟随同一类 import 问题失败
- 下一步最小闭环动作：
  - 后续 `WP12` maintenance intake 一律复用 canonical runner/gate；主线另起阶段前先单独规划 `WP13`
