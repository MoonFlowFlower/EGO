# Dashboard Data Schema

所有 dashboard_v1 数据都来自只读派生索引，不是正式运行时状态源。

## files

- `runs.jsonl`: `RunIndexRecord`
- `continuity_observation.jsonl`: `ContinuityObservationRecord`
- `growth_signals.jsonl`: `GrowthSignalRecord`
- `failures.jsonl`: `FailureIndexRecord`
- `agency_runs.jsonl`: `AgencyRunRecord`
- `runs_rollup.json`: `RunsRollup`
- `growth_rollup.json`: `GrowthRollup`
- `failures_rollup.json`: `FailuresRollup`
- `agency_rollup.json`: `AgencyRollup`
- `gap_summary.json`: gap 统计与 blocker 汇总
- `build_meta.json`: 索引生成元信息

## authority

- 主权威输入：`artifacts/telegram_real_mainline_v1/real_telegram/*/ledger.json`
- 兼容镜像：`sample.json` 只允许用于展示，不允许反向发明 OpenEmotion 语义
- Agency causal 链：优先读 `ledger.json.openemotion.events[*].payload`，仅在缺字段时回退 `sample.json`
- continuity 观察口径：`artifacts/mvs_e5_observation/*.md`

## notes

- host-only 样本会进入 `runs.jsonl` 与 continuity 统计
- host-only 样本不会进入 `growth_signals.jsonl`
- `restore` 一旦拿到“显式 restore + 首条 post-restore 完整 bundle + continuity probe 命中”的真实链，就应升级为 `status=direct_real`
