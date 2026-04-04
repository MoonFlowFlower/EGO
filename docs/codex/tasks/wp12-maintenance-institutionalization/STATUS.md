# WP12 Maintenance Institutionalization - STATUS

## Current milestone

- name: `Milestone 2: First Institutionalized Maintenance Verification`
- owner: `Codex`
- state: completed

## Current state

- current_layer: `收口/治理`
- main_chain_status: `wp12_maintenance_gate_institutionalized`
- completion_class: `verify_passed`

## Completed work

- 新增 canonical runner `scripts/codex/run_wp12_maintenance_verification.py`
- 新增 non-mutating gate verifier `scripts/codex/verify_wp12_maintenance_gate.py`
- 新增定向 institutionalization tests
- 刷新 `MAINTENANCE_VERIFICATION_CURRENT.md/.json`
- 将第一次 baseline-driven maintenance verification 写入 `MAINTENANCE_LEDGER.md`

## Last validation results

- mode: `full closeout`
- result: `pass with unrelated full-verify residuals recorded`
- summary:
  - runner pass
  - gate pass
  - `lint_repo.py` pass
  - `verify_repo.py --mode fast` pass
  - `verify_repo.py --mode full` 存在非 `WP12` 既有问题，未宣称 full clean：
    - EgoCore pytest collection 的 `openemotion` / `EgoCore` import 错误
    - OpenEmotion Windows runtime 的 `dotenv` 缺失
    - 旧 `mvp16_daily_check` 导入错误
    - EgoCore Telegram mainline regression exit=2，跟随同类 import 问题

## Decisions made

- institutionalization 只覆盖 `WP12`
- 不把“`WP12 -> E6`”写成新的 evidence level
- `WP13` 保持 deferred-only，不占位、不建包

## Open risks

- `verify_repo.py --mode full` 仍可能暴露 repo 既有环境/collection 问题；当前已记录的 residuals 不构成 `WP12` blocker
- 后续若 `WP12` 维护态样本触发 authority/proposal/replay regression，仍需按 baseline reopen 规则处理

## Next step

- `WP12` 后续 maintenance intake 一律复用 canonical runner/gate；如果主线继续，下一步是单独规划 `WP13`

## Commands run / evidence

- `python3 -m py_compile scripts/codex/run_wp12_maintenance_verification.py scripts/codex/verify_wp12_maintenance_gate.py`
- `PYTHONPATH=OpenEmotion pytest -q -s --noconftest OpenEmotion/tests/mvp17/test_wp12_maintenance_gate.py`
- `PYTHONPATH=OpenEmotion python3 scripts/codex/run_wp12_maintenance_verification.py`
- `python3 scripts/codex/verify_wp12_maintenance_gate.py --json`
- `python3 scripts/codex/lint_repo.py`
- `python3 scripts/codex/verify_repo.py --mode fast`
- `python3 scripts/codex/verify_repo.py --mode full`
- `Tasks/active/mvp17_social_self_other_modeling/MAINTENANCE_VERIFICATION_CURRENT.md`
