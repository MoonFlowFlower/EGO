# MVP13 Subagent Assignment

## 规则

- 所有 subagent 任务都以 `Tasks/MVS_task_plan.md` 为 parent authority
- 所有 subagent 任务都以 `Tasks/MVP13_task_plan.md` 为 phase-detail authority
- 不允许 subagent 自行扩 scope 到 `MVP14+`
- 不允许 subagent 把 legacy mirror 线升格为 formal owner path

## 推荐分派

| Task | Repo Owner | 可并行 | 写入范围 |
|------|------------|--------|----------|
| `T00_AUTHORITY_FREEZE` | Tasks/docs | 否 | `Tasks/MVS_task_plan.md`, `Tasks/MVP13_task_plan.md`, execution pack docs |
| `T10_OWNER_CONTRACT_CONVERGENCE` | OpenEmotion | 否 | `OpenEmotion/openemotion/self_model/*`, `OpenEmotion/schemas/self_model.schema.json`, `OpenEmotion/tests/mvp13/test_self_model_owner_contract.py` |
| `T20_PERSISTENCE_AUDIT_REPLAY` | OpenEmotion | 是 | `OpenEmotion/openemotion/self_model/*`, `OpenEmotion/tests/mvp13/test_self_model_infra.py` |
| `T30_IDENTITY_INVARIANTS_AND_DRIFT` | OpenEmotion | 否 | `OpenEmotion/openemotion/self_model/*`, `OpenEmotion/tests/mvp13/*` |
| `T40_PROTO_SELF_READ_INTEGRATION` | OpenEmotion | 是 | `OpenEmotion/openemotion/proto_self_v2/*` |
| `T50_GOVERNED_WRITEBACK` | OpenEmotion | 否 | `OpenEmotion/openemotion/proto_self_v2/*`, `OpenEmotion/openemotion/self_model/*` |
| `T60_EGOCORE_BRIDGE` | EgoCore | 否 | `EgoCore/app/runtime_v2/*`, `EgoCore/app/openemotion_adapter/*`, EgoCore tests |
| `T70_EVIDENCE_AND_ACCEPTANCE` | Dual-repo | 否 | `OpenEmotion/tools/*`, `OpenEmotion/tests/mvp13/*`, reports |

## 固定依赖

- `T00 -> T10`
- `T20` 与 `T40` 可并行
- `T30` 依赖 `T20`
- `T50` 依赖 `T20 + T30 + T40`
- `T60` 依赖 `T40 + T50`
- `T70` 依赖 `T20 + T30 + T40 + T50 + T60`

## 交付要求

每个 subagent 交付必须包含：
- 写入文件列表
- 验证命令
- 完成标准是否满足
- 未证明项
- 回退点
