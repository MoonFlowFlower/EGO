# MVP17 Social Self / Other-Modeling 执行包

```yaml
task_id: L3-20260403-MVP17-SSOM
created_at: "2026-04-03T00:00:00Z"
owner: "Codex"
layer: 3
type: dual_repo
repos: [EgoCore, OpenEmotion]
status: authority_frozen
parent_authority: "Tasks/MVS_task_plan.md"
phase_authority: "Tasks/MVP17_task_plan.md"
predecessor: "WP11/MVP16"
same_subject_line: true
not_parallel_track: true
scope: "WP12 / MVP17 Social Self / Other-Modeling"
```

---

## 真实目标

在不放开 authority 边界的前提下，把 `WP12/MVP17` 的 formal owner 冻结到 `OpenEmotion/openemotion/social_self/*`，并为后续 `trust / commitment / repair` proposal-only 社会连续性能力定义正式 runtime 主线与任务分工。

## 当前正式 owner target

- `OpenEmotion/openemotion/social_self/*`

## 当前正式主链 target

`social owner -> bounded social projection / proposals -> proto_self_runtime / proto_self_adapter / proto_self_v2 -> governed downstream weighting and social writeback candidate path`

## 当前锁定口径

- `MVP17` 是 `WP12`，接在 `WP11/MVP16` 后，不是新的主体线
- phase 1 只做 `trust / commitment / repair`
- `other-modeling` 当前只允许 bounded state / role continuity 语义，不做泛化心智解读
- `EgoCore/app/response/relationship_context.py`、`EgoCore/app/handlers/social_chat_handler.py`、`EgoCore/app/runtime/repair_context_manager.py`、`EgoCore/app/bridges/openemotion_bridge.py`、`OpenEmotion/emotiond/db.py`、`OpenEmotion/emotiond/state.py`、`OpenEmotion/emotiond/api.py` 只作为 reference-only / input-only 历史 surfaces
- `WP11` 保持 `maintenance_mode`
- `WP11` 新增样本只进对应 maintenance ledger，不回灌为 `WP11` scope reopen
- provider `429/401` 继续标注为外部预算层风险，不回灌为 `WP11` blocker

## 当前范围

- authority / contract freeze
- formal owner package target
- bounded proto-self social contract target
- EgoCore runtime social bridge target
- historical social / relation materials demotion
- subagent-ready task decomposition

## 当前状态

- formal owner：`not_started`
- 主链接线：`not_started`
- 启用状态：`authority_frozen_only`
- 当前 blocker：`none on the authority surface`
- 当前最小动作：`T10_FORMAL_OWNER_PACKAGE`

## 当前不做

- 放开 live autonomy
- 放开 OpenEmotion direct reply authority
- 放开 broader transport claims
- autonomous social outreach
- unbounded other-model mind-reading
- 把 `WP11` maintenance ledger 重新解释成 `WP12` readiness
- 把 historical roadmap / archive social materials 直接当成当前 `WP12` formal proof

## 执行入口

- authority：`Tasks/MVP17_task_plan.md`
- status：`STATUS.md`
- legacy register：`LEGACY_REFERENCE_REGISTER.md`
- contracts：`contracts/`
- task cards：`cards/`
