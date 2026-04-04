# MVP12 Developmental Sandbox 执行包

```yaml
task_id: L3-20260402-MVP12-DS
created_at: "2026-04-02T12:05:16Z"
owner: "Codex"
layer: 3
type: dual_repo
repos: [EgoCore, OpenEmotion]
status: maintenance_mode
parent_authority: "Tasks/MVS_task_plan.md"
phase_authority: "Tasks/MVP12_task_plan.md"
predecessor: "WP6"
same_subject_line: true
not_parallel_track: true
scope: "WP7 / MVP12 Developmental Sandbox"
```

---

## 真实目标

在不放开 authority 边界的前提下，把 `WP7/MVP12` 的 developmental sandbox 接入正式 runtime 主链，并验证 controlled observation、host-governed proactive draft / send chain 与 shadow-only writeback。

## 当前正式 owner / runtime target

- formal runtime path：
  - `runtime_v2 -> proto_self_runtime -> proto_self_adapter -> proto_self_v2`
- implementation library：
  - `OpenEmotion/emotiond/developmental_core/*`

## 当前锁定口径

- `MVP12` 是 `WP7`，是 `WP6` 之后的下一阶段，不是新的主体线
- `emotiond.developmental_core` 只作为实现库复用，不是 runtime owner
- `emotiond.daemon` 只作为 reference-only 历史表面
- primary evidence source 固定为正式 runtime ingress/egress 主链
- `Telegram` 只作为 transport-specific supplemental evidence
- developmental 产物只能 shadow-only writeback
- proactive 只能是 host-governed draft / send chain
- live 默认 `off`

## 当前范围

- formal runtime sandbox wiring
- developmental shadow writeback
- runtime mainline observation harness
- controlled observation aggregate
- host-governed proactive draft / scheduler / delivery / outbox / transport chain
- maintenance closeout

## 当前状态

- formal runtime sandbox：`implemented`
- 主链接线：`sandbox_mainline_stable`
- 启用状态：`controlled_mainline_observation`
- current aggregate：
  - `OpenEmotion/artifacts/mvp12/controlled_observation_aggregate_current.md = pass`
- supplemental Telegram proactive evidence：
  - single `E4` sample
- 当前 blocker：
  - controlled observation 范围内无主 blocker
  - supplemental transport evidence 仍是 single-sample `E4`，但不阻断 `WP7` controlled-axis maintenance

## 当前不做

- 放开 live autonomy
- 放开 OpenEmotion direct reply authority
- 放开 broader transport claims
- 把 `WP7` 的 controlled observation `pass` 冒充为 transport `E5`
- 重新启用 `emotiond.daemon` 作为正式 runtime owner

## 维护态规则

- `WP7` 当前已在 formal runtime sandbox + controlled observation 轴上收口进入 `maintenance_mode`
- 新增样本只进入 [MAINTENANCE_LEDGER.md](/mnt/d/Project/AIProject/MyProject/Ego/Tasks/active/mvp12_developmental_sandbox/MAINTENANCE_LEDGER.md)
- maintenance 样本不会自动 reopen `WP7`

## 执行入口

- authority：`Tasks/MVP12_task_plan.md`
- status：`STATUS.md`
- maintenance ledger：`MAINTENANCE_LEDGER.md`
- legacy register：`LEGACY_REFERENCE_REGISTER.md`
