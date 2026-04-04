# WP12 Maintenance Institutionalization - IMPLEMENT

## Source of truth

- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- `Tasks/active/mvp17_social_self_other_modeling/WP12_QA_BASELINE.md`
- `Tasks/active/mvp17_social_self_other_modeling/STATUS.md`
- `Tasks/MVP17_task_plan.md`

## Execution rules

- 先读 `SPEC.md -> PLAN.md -> IMPLEMENT.md -> STATUS.md`
- 每次只推进 `STATUS.md` 当前 milestone
- `WP12` package docs 仍是 authority refs，不复制第二真相源

## Scope control

- 只做 institutionalized maintenance 所需的 runner、gate、tests、docs 和 current artifacts
- 不顺手推进 `WP13`
- 不改 `Tasks/MVS_task_plan.md` 去占位后续 phase

## Validation strategy

- Milestone 1 完成后运行：
  - `python3 -m py_compile scripts/codex/run_wp12_maintenance_verification.py scripts/codex/verify_wp12_maintenance_gate.py`
  - `PYTHONPATH=OpenEmotion pytest -q -s --noconftest OpenEmotion/tests/mvp17/test_wp12_maintenance_gate.py`
  - `python3 scripts/codex/verify_repo.py --mode fast`
- Milestone 2 / closeout 运行：
  - `PYTHONPATH=OpenEmotion python3 scripts/codex/run_wp12_maintenance_verification.py`
  - `python3 scripts/codex/verify_wp12_maintenance_gate.py --json`
  - `python3 scripts/codex/lint_repo.py`
  - `python3 scripts/codex/verify_repo.py --mode fast`
  - `python3 scripts/codex/verify_repo.py --mode full`

## Failure handling

- gate/runner/test 失败先在当前 milestone 内修复
- 若 `verify_repo.py --mode full` 只暴露与 `WP12` 无关的既有失败，记录但不伪报 full clean
- 若 full verify 暴露 `WP12` regression，则阻断 closeout

## Stopping rule

- canonical runner 未生成 current report，不进入 publish-gate closeout
- gate verifier 未返回 `publish_gate_ready = true`，不进入最终发布
- 命中 `WP12` authority regression 时停止并回到 reopen 讨论

## Final handoff checklist

- [x] `PLAN.md` 已更新进度与决策
- [x] `STATUS.md` 已更新验证结果与 next step
- [x] commands run / evidence 已记录
- [x] risks / rollback notes 已记录
