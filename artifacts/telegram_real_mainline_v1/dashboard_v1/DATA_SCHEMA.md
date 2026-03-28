# Dashboard Data Schema

所有 dashboard_v1 数据都来自只读派生索引，不是正式运行时状态源。

## files

- `runs.jsonl`: `RunIndexRecord`
- `continuity_observation.jsonl`: `ContinuityObservationRecord`
- `growth_signals.jsonl`: `GrowthSignalRecord`
- `failures.jsonl`: `FailureIndexRecord`
- `gap_summary.json`: gap 统计与 blocker 汇总
- `build_meta.json`: 索引生成元信息

## authority

- 主权威输入：`artifacts/telegram_real_mainline_v1/real_telegram/*/ledger.json`
- 兼容镜像：`sample.json` 只允许用于展示，不允许反向发明 OpenEmotion 语义
- continuity 观察口径：`artifacts/mvs_e5_observation/*.md`

## notes

- host-only 样本会进入 `runs.jsonl` 与 continuity 统计
- host-only 样本不会进入 `growth_signals.jsonl`
- `restore` 未拿到直接真实样本前，`continuity_observation.jsonl` 必须保持 `status=missing`
