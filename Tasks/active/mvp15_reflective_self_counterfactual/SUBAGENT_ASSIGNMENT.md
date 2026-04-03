# MVP15 Subagent Assignment

## 规则

- 所有 subagent 任务都以 `Tasks/MVS_task_plan.md` 为 parent authority
- 所有 subagent 任务都以 `Tasks/MVP15_task_plan.md` 为 phase-detail authority
- 不允许 subagent 自行扩 scope 到 `MVP16+`
- 不允许 subagent 把 legacy `emotiond` reflection / counterfactual 线升格为 formal owner path

## 推荐分派

| Task | Repo Owner | 可并行 | 写入范围 |
|------|------------|--------|----------|
| `T00_AUTHORITY_FREEZE` | Tasks/docs | 否 | `Tasks/MVS_task_plan.md`, `Tasks/MVP15_task_plan.md`, execution pack docs, `PROJECT_MEMORY.md` |
| `T10_FORMAL_OWNER_PACKAGE` | OpenEmotion | 否 | `OpenEmotion/openemotion/reflective_self/*`, `OpenEmotion/tests/mvp15/test_reflective_owner_infra.py` |
| `T20_REPLAY_AUDIT_PROPOSAL_STATE` | OpenEmotion | 否 | `OpenEmotion/openemotion/reflective_self/*`, `OpenEmotion/tests/mvp15/test_reflective_replay_and_governance.py` |
| `T30_PROTO_SELF_CONTRACT_INTEGRATION` | OpenEmotion | 是 | `OpenEmotion/openemotion/proto_self_v2/*`, `OpenEmotion/tests/mvp15/test_reflection_proto_self_integration.py` |
| `T40_EGOCORE_RUNTIME_BRIDGE` | EgoCore | 否 | `EgoCore/app/runtime_v2/*`, `EgoCore/app/openemotion_adapter/*`, EgoCore tests |
| `T50_LEGACY_DEMOTION_AND_MIGRATION` | OpenEmotion | 是 | `OpenEmotion/emotiond/*`, `OpenEmotion/tools/verify_mvp15_mainline_wiring.py`, migration docs/tests |
| `T60_CAUSAL_VALIDATION` | Dual-repo | 否 | `OpenEmotion/tests/mvp15/*`, proof tools/artifacts |
| `T70_CONTROLLED_OBSERVATION` | Dual-repo | 否 | `OpenEmotion/tools/*`, `OpenEmotion/artifacts/mvp15/*`, observation tests |
| `T80_CLOSEOUT` | Tasks/docs | 否 | `STATUS.md`, `README.md`, `PROJECT_MEMORY.md`, `OpenEmotion/artifacts/mvp15/MVP15_COMPLETION_CURRENT.*` |

## 固定依赖

- `T00 -> T10 -> T20`
- `T30` 依赖 `T10 + T20`
- `T40` 依赖 `T30`
- `T50` 依赖 `T10`
- `T60` 依赖 `T30 + T40 + T50`
- `T70` 依赖 `T60`
- `T80` 依赖 `T70`

## 交付要求

每个 subagent 交付必须包含：
- 写入文件列表
- 验证命令
- 完成标准是否满足
- 未证明项
- 回退点
