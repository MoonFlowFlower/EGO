# WP12 Maintenance Institutionalization

## Goal

把 `WP12/MVP17` 从“已有 QA baseline 的 maintenance_mode”推进到“有 canonical maintenance runner、本地 publish gate 和第一次 baseline-driven maintenance verification”的制度化维护状态。

## Non-goals

- 不创建或冻结任何 `WP13/MVP18` authority / task package
- 不扩写 `WP12` authority、formal owner、runtime bridge 或 social capability scope
- 不把 institutionalization 说成新的 repo 级证据等级

## Constraints

- 边界约束：`WP12` 仍只覆盖 formal owner + proposal-only social writeback + controlled observation 轴
- 仓库/子仓约束：不改 `Tasks/MVS_task_plan.md` 去占位 `WP13`
- 环境约束：runner 必须使用 repo 内已存在的 `WP12` baseline entrypoints，不发明第二套验证体系
- 发布约束：若要给出 `WP12` maintenance 结论，必须先跑 canonical runner 和 gate verifier

## Acceptance criteria

- [ ] `docs/codex/tasks/wp12-maintenance-institutionalization/` 完整落地并锁定 milestone/claim ceiling
- [ ] `scripts/codex/run_wp12_maintenance_verification.py` 能刷新 `MAINTENANCE_VERIFICATION_CURRENT.md/.json` 并追加 ledger entry
- [ ] `scripts/codex/verify_wp12_maintenance_gate.py --json` 返回 `publish_gate_ready = true`
- [ ] `WP12` maintenance docs 已引用 canonical runner/gate，但 `WP12` authority 口径未扩张
- [ ] 未新增任何 `WP13` repo-tracked authority 文件

## Known risks / dependencies

- 风险：`python3 scripts/codex/verify_repo.py --mode full` 当前可能暴露与 `WP12` 无关的既有环境/collection 噪声
- 依赖：`WP12_QA_BASELINE.md`、既有 `mvp17` artifacts、既有 social mainline tests/runners
- 外部 blocker：无；若 full verify 暴露 `WP12` 真实 regression，则转为当前任务 blocker

## Authority refs

- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
- `docs/CODEX_CLOSED_LOOP_SELF_REVIEW_WORKFLOW.md`
- `AGENTS.md`
- `Tasks/active/mvp17_social_self_other_modeling/WP12_QA_BASELINE.md`
- `Tasks/active/mvp17_social_self_other_modeling/STATUS.md`
- `Tasks/MVP17_task_plan.md`
