# P1 CHANGE_PLAN

## 任务
P1：RuntimeV2Loop 主链瘦身手术

## 主执行链
1. 审计 `loop.py` 当前职责分布
2. 识别可安全抽离的宿主侧纯职责
3. 先抽 helper / pure function，再收主流程
4. 用最小回归验证行为未破
5. 产出职责图、证据表、失败样本表

## 新旧职责对应

| old_location | old_responsibility | new_location | new_responsibility |
|---|---|---|---|
| `loop.py` | 风险评估关键词判断 | `EgoCore/app/runtime_v2/proto_self_runtime.py` | `assess_risk_level()` |
| `loop.py` | proto-self ingress event 构造 | `EgoCore/app/runtime_v2/proto_self_runtime.py` | `build_proto_self_ingress_event()` |
| `loop.py` | external_result event 构造 | `EgoCore/app/runtime_v2/proto_self_runtime.py` | `build_external_result_event()` |
| `loop.py` | normalized/openemotion/response_plan capture | `EgoCore/app/runtime_v2/proto_self_runtime.py` | `RuntimeV2ProtoSelfRuntime` side-effect 封装 |
| `loop.py` | proto-self trace write | `EgoCore/app/runtime_v2/proto_self_runtime.py` | `process_ingress()` / `process_external_result()` |

## 本次最小改动
- 新增宿主 helper：`EgoCore/app/runtime_v2/proto_self_runtime.py`
- `RuntimeV2Loop` 只保留 orchestration、state mutation、decision/transition 驱动和 helper 调用
- 保留 `loop._assess_risk_level()` 兼容入口，避免现有测试和脚本失效
- 新增 helper contract tests：`EgoCore/tests/test_runtime_v2_proto_self_runtime.py`

## 不做项
- 不重做 Proto-Self adapter
- 不重构状态存储
- 不改 trace 总账本
- 不升级 evidence schema
- 不处理 P2/P3/P4

## 本次结论不能证明什么
- 不能证明 `RuntimeV2Loop` 已经完成最终形态治理
- 不能证明所有 runtime 测试都已无历史脆弱点
- 不能证明系统更稳定
