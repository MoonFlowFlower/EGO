# WP9 Boundary Freeze For WP10

## Purpose

启动 `WP10` 不能重开 `WP9`。本文件冻结 `WP9/MVP14` 与 `WP10/MVP15` 之间的边界，防止阶段偷换。

## Frozen WP9 Facts

- `WP9/MVP14` 已在 controlled observation 轴上达到 `V5/E5`
- `WP9` 当前状态是 `maintenance_mode`
- `WP9` 的 formal owner 仍固定为：
  - `OpenEmotion/openemotion/endogenous_drives/*`
- `proto_self_v2` 当前 drive projection 仍只表示 runtime-bounded consumer surface

## Maintenance Rule

- `WP9` 后续新增样本只进入：
  - `Tasks/active/mvp14_endogenous_drives_self_maintenance/MAINTENANCE_LEDGER.md`
- 默认不会因为新增样本自动 reopen `WP9`
- 只有以下情况才允许考虑 reopen：
  - formal owner writeback regression
  - replay / invariant regression
  - authority boundary regression
  - evidence classification regression

## External Risk Classification Rule

- provider `429/401` 持续标注为外部预算层风险
- 只有当它们导致 formal owner writeback 主链失效时，才可升级为 `WP9` blocker
- 单纯预算波动、速率限制、认证波动，不构成 `WP9` reopen 条件

## Non-Regression Rules

- `WP10` 不得改写 `WP9` 的 formal read path / formal write path
- `WP10` 不得把 `WP9` 的 controlled `E5` 改写成 live maturity claim
- `WP10` 不得借 `WP9 pass` 放开 OpenEmotion direct reply authority
- `WP10` 不得借 `WP9 pass` 放开 broader transport claims
