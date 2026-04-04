# WP13 / MVP18 Legacy Reference Register

## Purpose

登记 `WP13` 启动前仓内已有的 `MVP18` / embodied / consequence 相关材料。它们可以作为参考输入、迁移线索或对照证据，但不能直接充当新的 `WP13` authority、formal owner 或 formal proof。

## Technical Reference, Not Authority

以下文件可作为技术参考，但与 `Tasks/MVS_task_plan.md + Tasks/MVP18_task_plan.md` 冲突时，不拥有裁决权：

- `OpenEmotion/roadmap/VersionRoadmap.md`

## Reference-only / Input-only Surfaces

以下代码与工具不属于 `WP13` formal owner path：

- `OpenEmotion/emotiond/consequence.py`
- `OpenEmotion/emotiond/science/interventions.py`

这些 surfaces 在 `WP13` 中最多只允许承担：

- migration reference
- replay / observation baseline
- action-consequence input-only helper
- historical comparison

它们不得承担：

- formal owner state
- final embodied/environment coupling semantics
- current-mainline closeout proof

## Current Authority Reminder

- `Tasks/MVS_task_plan.md` 是顶层裁决
- `Tasks/MVP18_task_plan.md` 是 `WP13` phase-detail authority
- `Tasks/active/mvp18_embodied_loop_environment_coupling/*` 是当前执行包

All listed legacy code and docs above are `reference-only` or `input-only` for `WP13`.

Current formal owner reminder:

- `OpenEmotion/openemotion/embodied_self/*` is the only formal owner target
- `runtime_v2 -> proto_self_runtime -> proto_self_adapter -> proto_self_v2` is the only current-mainline target
