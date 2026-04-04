# MVP18 Subagent Assignment

## 规则

- 所有 subagent 任务都以 `Tasks/MVS_task_plan.md` 为 parent authority
- 所有 subagent 任务都以 `Tasks/MVP18_task_plan.md` 为 phase-detail authority
- 不允许 subagent 自行扩 scope 到 `WP14+`
- 不允许 subagent 把 historical consequence / intervention materials 升格为 formal owner path
- `WP12` 当前已收口为 `maintenance_mode`；本文件只同步任务分派与 write scope，不 reopen `WP12`

## 推荐分派

| Task | Repo Owner | 可并行 | 写入范围 |
|------|------------|--------|----------|
| `T00_AUTHORITY_FREEZE` | Tasks/docs | 否 | `Tasks/MVS_task_plan.md`, `Tasks/MVP18_task_plan.md`, execution pack docs, `PROJECT_MEMORY.md` |
| `T10_FORMAL_OWNER_PACKAGE` | OpenEmotion | 否 | `OpenEmotion/openemotion/embodied_self/*`, `OpenEmotion/tests/mvp18/test_embodied_owner_infra.py` |
| `T20_PROTO_SELF_CONTRACT_INTEGRATION` | OpenEmotion | 否 | `OpenEmotion/openemotion/proto_self_v2/*`, `OpenEmotion/tests/mvp18/test_embodied_proto_self_integration.py` |
| `T30_EGOCORE_RUNTIME_BRIDGE` | EgoCore | 否 | `EgoCore/app/runtime_v2/*`, `EgoCore/app/openemotion_adapter/*`, EgoCore tests |
| `T40_LEGACY_DEMOTION_AND_COMPAT_MAP` | Dual-repo | 是 | historical consequence / intervention surfaces, reference docs, verifiers, demotion tests |
| `T50_CAUSAL_VALIDATION` | Dual-repo | 否 | `OpenEmotion/tests/mvp18/*`, proof tools/artifacts |
| `T60_CONTROLLED_OBSERVATION_SINGLE` | Dual-repo | 否 | `OpenEmotion/tools/*`, `OpenEmotion/artifacts/mvp18/*`, observation tests |
| `T70_BATCH_OBSERVATION_AND_AGGREGATE` | Dual-repo | 否 | `OpenEmotion/scenarios/mvp18_observation_bank/*`, batch tools, aggregate artifacts/tests |
| `T80_CLOSEOUT_AND_QA_BASELINE` | Tasks/docs | 否 | `Tasks/active/mvp18_embodied_loop_environment_coupling/*`, `Tasks/MVP18_task_plan.md`, `PROJECT_MEMORY.md`, `OpenEmotion/artifacts/mvp18/MVP18_COMPLETION_CURRENT.*` |
| `T90_SUBAGENT_ASSIGNMENT` | Tasks/docs | 否 | `SUBAGENT_ASSIGNMENT.md` |

## 固定依赖

- `T00 -> T10 -> T20 -> T30 -> T50 -> T60 -> T70 -> T80`
- `T40` 依赖 `T10`，可与 `T20/T30` 并行
- `T90` 依赖 `T00`，用于同步当前 authority package 的分派表；在 package 已收口时允许 no-op 验收

## 交付要求

每个 subagent 交付必须包含：

- 写入文件列表
- 验证命令
- 完成标准是否满足
- 未证明项
- 回退点
