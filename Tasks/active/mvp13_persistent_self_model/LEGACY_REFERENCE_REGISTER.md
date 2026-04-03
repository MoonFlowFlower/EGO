# MVP13 Legacy Reference Register

## 目的

本文件登记旧 `MVP13 mirror / dual-write` 遗产的角色，防止它们被重新误报为 `WP8/MVP13` 的 formal owner / proof path。

## Reference-Only Items

| 路径 | 角色 | 新计划中的允许用途 | 禁止用途 |
|------|------|--------------------|----------|
| `OpenEmotion/artifacts/mvp13/TASK.md` | 历史任务单 | 对照旧阶段假设 | 作为当前 authority |
| `OpenEmotion/tools/mvp13_*` | 历史 mirror/readiness 脚本 | 参考旧观测方法与命名 | 作为当前 formal proof runner |
| `OpenEmotion/emotiond/self_model/*` | 旧 self-model 实现 | 迁移参考、字段对照 | 作为当前 formal owner |
| `OpenEmotion/emotiond/self_model_mirror.py` | 旧 mirror adapter | 参考镜像隔离方式 | 作为当前读写主链 |
| `EgoCore/egocore/runtime/self_model_manager.py` | 宿主侧旧 manager | 参考审计/校验接口 | 获得 self-model 解释权或 owner 身份 |

## Current Formal Owner

- `OpenEmotion/openemotion/self_model/*`
- `OpenEmotion/schemas/self_model.schema.json`

## Hard Rule

任何 `WP8/MVP13` 的 formal owner claim、behavioral influence proof、read/write gate、或 roadmap 状态，都不得依赖上表中的 reference-only 项。
