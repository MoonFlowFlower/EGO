# MVP16 Subagent Assignment

## 规则

- 所有 subagent 任务都以 `Tasks/MVS_task_plan.md` 为 parent authority
- 所有 subagent 任务都以 `Tasks/MVP16_task_plan.md` 为 phase-detail authority
- 不允许 subagent 自行扩 scope 到 `WP12+`
- 不允许 subagent 把 legacy `emotiond` developmental 线或旧 `mvp16_*` tools 升格为 formal owner path

## 推荐分派

| Task | Repo Owner | 可并行 | 写入范围 |
|------|------------|--------|----------|
| `T00_AUTHORITY_FREEZE` | Tasks/docs | 否 | `Tasks/MVS_task_plan.md`, `Tasks/MVP16_task_plan.md`, execution pack docs, `PROJECT_MEMORY.md` |
| `T10_FORMAL_OWNER_PACKAGE` | OpenEmotion | 否 | `OpenEmotion/openemotion/developmental_self/*`, `OpenEmotion/tests/mvp16/test_developmental_owner_infra.py` |
| `T20_PROTO_SELF_CONTRACT_INTEGRATION` | OpenEmotion | 否 | `OpenEmotion/openemotion/proto_self_v2/*`, `OpenEmotion/tests/mvp16/test_developmental_proto_self_integration.py` |
| `T30_EGOCORE_RUNTIME_BRIDGE` | EgoCore | 否 | `EgoCore/app/runtime_v2/*`, `EgoCore/app/openemotion_adapter/*`, EgoCore tests |
| `T40_LEGACY_DEMOTION_AND_COMPAT_MAP` | OpenEmotion | 是 | `OpenEmotion/emotiond/*`, `OpenEmotion/tools/verify_mvp16_mainline_wiring.py`, migration docs/tests |
| `T50_CAUSAL_VALIDATION` | Dual-repo | 否 | `OpenEmotion/tests/mvp16/*`, proof tools/artifacts |
| `T60_CONTROLLED_OBSERVATION_SINGLE` | Dual-repo | 否 | `OpenEmotion/tools/*`, `OpenEmotion/artifacts/mvp16/*`, observation tests |
| `T70_BATCH_OBSERVATION_AND_AGGREGATE` | Dual-repo | 否 | `OpenEmotion/scenarios/mvp16_observation_bank/*`, batch tools, aggregate artifacts/tests |
| `T80_CLOSEOUT_AND_QA_BASELINE` | Tasks/docs | 否 | `STATUS.md`, `README.md`, `PROJECT_MEMORY.md`, `OpenEmotion/artifacts/mvp16/MVP16_COMPLETION_CURRENT.*`, `WP11_QA_BASELINE.md` |
| `T90_SUBAGENT_ASSIGNMENT` | Tasks/docs | 否 | `SUBAGENT_ASSIGNMENT.md` |

## 固定依赖

- `T00 -> T10 -> T20 -> T30 -> T50 -> T60 -> T70 -> T80`
- `T40` 依赖 `T10`，可与 `T20/T30` 并行
- `T90` 在文档阶段一次性完成

## 交付要求

每个 subagent 交付必须包含：

- 写入文件列表
- 验证命令
- 完成标准是否满足
- 未证明项
- 回退点
