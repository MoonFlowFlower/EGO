# MVP18 Embodied Loop / Environment Coupling 执行包

```yaml
task_id: L3-20260404-MVP18-ELEC
created_at: "2026-04-04T00:00:00Z"
owner: "Codex"
layer: 3
type: dual_repo
repos: [EgoCore, OpenEmotion]
status: authority_frozen
parent_authority: "Tasks/MVS_task_plan.md"
phase_authority: "Tasks/MVP18_task_plan.md"
predecessor: "WP12/MVP17"
same_subject_line: true
not_parallel_track: true
scope: "WP13 / MVP18 Embodied Loop / Environment Coupling"
```

---

## 真实目标

在不放开 authority 边界的前提下，把 `WP13/MVP18` 的 formal owner target 冻结到 `OpenEmotion/openemotion/embodied_self/*`，并把 `resource/slack pressure`、`action -> consequence` bounded writeback、`self/world boundary pressure` 的 proposal-only contract 正式接到当前主链规划里。

## 当前正式 owner target

- `OpenEmotion/openemotion/embodied_self/*`

## 当前正式主链 target

`embodied owner -> bounded embodied projection / proposals -> proto_self_runtime / proto_self_adapter / proto_self_v2 -> governed downstream weighting and embodied writeback candidate path`

## 当前锁定口径

- `MVP18` 是 `WP13`，接在 `WP12/MVP17` 后，不是新的主体线
- phase 1 只做 `resource/slack pressure`、`action -> consequence` bounded writeback、`self/world boundary pressure`
- `EgoCore` 继续保留 runtime / response / tool / transport / environment risk adjudication 的最终权威
- `OpenEmotion/emotiond/consequence.py`、`OpenEmotion/emotiond/science/interventions.py`、`OpenEmotion/roadmap/VersionRoadmap.md` 只作为 reference-only / input-only / technical reference 历史 surfaces
- `WP12` 保持 `maintenance_mode`
- `WP12` 新增样本只进对应 maintenance ledger，不回灌为 `WP12` scope reopen
- provider `429/401` 继续标注为外部预算层风险，不回灌为 `WP12` blocker

## 当前范围

- authority / contract freeze
- formal embodied owner package target
- bounded proto-self embodied contract
- EgoCore runtime embodied bridge target
- historical consequence / intervention materials demotion
- subagent-ready task decomposition

## 当前状态

- 执行包状态：`authority_frozen / task_package_ready`
- authority freeze：`completed`
- formal owner：`T10 pending`
- proto_self_v2 contract：`T20 pending`
- EgoCore runtime bridge：`T30 pending`
- legacy demotion / compat map：`T40 pending`
- causal validation：`T50 pending`
- single controlled observation：`T60 pending`
- batch controlled observation / aggregate：`T70 pending`
- 主链接线：`not_started`
- 启用状态：`not_started`
- 当前 blocker：`T10 formal owner package not started`
- 当前最小动作：`start T10_FORMAL_OWNER_PACKAGE; do not implement runtime code before T10`

## 当前不做

- 放开 live autonomy
- 放开 OpenEmotion direct reply authority
- 放开 broader transport claims
- embodied takeover
- 持续主动外发
- autonomous tool expansion
- 把 `WP12` maintenance institutionalization 重新解释成 `WP13` readiness
- 把 historical consequence / intervention materials 直接当成当前 `WP13` formal proof

## 执行入口

- authority：`Tasks/MVP18_task_plan.md`
- status：`STATUS.md`
- legacy register：`LEGACY_REFERENCE_REGISTER.md`
- contracts：`contracts/`
- task cards：`cards/`
- subagent assignment：`SUBAGENT_ASSIGNMENT.md`
