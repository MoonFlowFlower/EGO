# MVP12 Maintenance Ledger

## Purpose

`WP7/MVP12` 已进入维护态。后续新增样本、补充 observation、transport 补证和非 scope 变动统一记在这里，不自动触发 `WP7` scope reopen。

## Frozen Completion Context

- completion artifact:
  - `OpenEmotion/artifacts/mvp12/MVP12_COMPLETION_CURRENT.md`
- current aggregate:
  - `OpenEmotion/artifacts/mvp12/controlled_observation_aggregate_current.md`
- current status:
  - `Tasks/active/mvp12_developmental_sandbox/STATUS.md`

## Reopen Policy

默认不 reopen `WP7`。仅当出现以下任一项时，才允许升级为 reopen 讨论：

- sandbox runtime owner regression
- shadow-only writeback regression
- controlled observation aggregate regression
- replay consistency regression
- authority boundary regression
- evidence classification regression

## External Budget / Transport Note

- `WP7` 的 Telegram proactive transport 当前只有 supplemental single-sample `E4`
- 这不是 `WP7` controlled-axis blocker
- 只有在 formal runtime sandbox / controlled observation 主链被破坏时，才升级为 `WP7` reopen 讨论

## Sample Intake Rule

- `WP7` 新增 controlled observation 或 supplemental transport 样本只在本 ledger 追加记录
- 这些样本不会自动改变 `WP7 maintenance_mode`
- 若样本触发 reopen policy，再单独开裁决，不直接在阶段文档中偷改结论
