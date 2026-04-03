# MVP15 Reflective Self / Counterfactual Self 执行包

```yaml
task_id: L3-20260403-MVP15-RSC
created_at: "2026-04-03T23:30:00Z"
owner: "Codex"
layer: 3
type: dual_repo
repos: [EgoCore, OpenEmotion]
status: authority_frozen
parent_authority: "Tasks/MVS_task_plan.md"
phase_authority: "Tasks/MVP15_task_plan.md"
predecessor: "WP9/MVP14"
same_subject_line: true
not_parallel_track: true
scope: "WP10 / MVP15 Reflective Self / Counterfactual Self"
```

---

## 真实目标

在不放开 authority 边界的前提下，把 `WP10/MVP15` 的 formal owner 冻结到 `OpenEmotion/openemotion/reflective_self/*`，并把 reflection / counterfactual capability 规划到当前正式 runtime 主线，而不是延续旧 `emotiond/*` bounded / shadow 线作为正式 owner。

## 当前正式 owner target

- `OpenEmotion/openemotion/reflective_self/*`

## 当前正式主链 target

`reflective owner -> bounded reflection projection / proposals -> proto_self_runtime / proto_self_adapter / proto_self_v2 -> governed downstream weighting and writeback candidate path`

## 当前锁定口径

- `MVP15` 是 `WP10`，接在 `WP9/MVP14` 后，不是新的主体线
- `emotiond/reflection_engine/*`、`reflection_adapter.py`、`reflection_shadow.py`、`self_counterfactual.py` 只作为 bounded compatibility / migration reference surfaces，不是 formal owner
- 旧 `/plan` 与 `/decision/target` bounded consumer 证明只作为历史参考，不是当前 runtime 主链 closeout 口径
- `WP9` 保持 `maintenance_mode`
- `WP9` 新增样本只进 [MAINTENANCE_LEDGER.md](/mnt/d/Project/AIProject/MyProject/Ego/Tasks/active/mvp14_endogenous_drives_self_maintenance/MAINTENANCE_LEDGER.md)，不回灌为 `WP9` scope reopen
- provider `429/401` 继续标注为外部预算层风险，不回灌为 `WP9` blocker

## 当前范围

- authority / contract freeze
- formal owner target freeze
- legacy reflection / counterfactual surfaces demotion plan
- current runtime mainline target freeze
- subagent-ready task decomposition

## 当前状态

- formal owner：`target frozen, not implemented`
- 主链接线：`not_started_on_current_runtime_mainline`
- 启用状态：`disabled`
- 已证实：legacy `MVP15` infra / tests / bounded consumer / paired relevance proof 存在
- 当前 blocker：`当前 formal owner 仍在 legacy emotiond surfaces；openemotion reflective owner package 尚不存在`

## 当前不做

- 直接开 `MVP15` 代码
- 放开 live autonomy
- 放开 OpenEmotion direct reply authority
- 放开 broader transport claims
- 把 `WP9` maintenance ledger 重新解释成 `WP10` readiness
- 把旧 `emotiond` bounded consumer 直接当成当前 `WP10` formal proof

## 执行入口

- authority：`Tasks/MVP15_task_plan.md`
- status：`STATUS.md`
- legacy register：`LEGACY_REFERENCE_REGISTER.md`
- contracts：`contracts/`
- task cards：`cards/`
