# P1 RESPONSIBILITY_MAP

## 重构前：`RuntimeV2Loop.run_turn_typed()` 当前职责

| area | current_responsibility | evidence |
|---|---|---|
| session orchestration | turn 启动、generation 注入、state 获取 | `EgoCore/app/runtime_v2/loop.py:168` |
| input hygiene | 用户输入截断并写入 state/history | `EgoCore/app/runtime_v2/loop.py:177` |
| proto-self ingress | 构造 `proto_self_event` 并调用 `handle_event()` | `EgoCore/app/runtime_v2/loop.py:182` |
| risk signal | 在 loop 内直接做关键词风险评估 | `EgoCore/app/runtime_v2/loop.py:188` |
| evidence capture | 在 loop 内直接捕获 `normalized_event/openemotion_result/response_plan` | `EgoCore/app/runtime_v2/loop.py:214`, `EgoCore/app/runtime_v2/loop.py:344` |
| trace write | 在 loop 内直接写 proto-self trace | `EgoCore/app/runtime_v2/loop.py:231`, `EgoCore/app/runtime_v2/loop.py:321` |
| external_result feedback | 工具执行后回构 `external_result_event` 再回流 adapter | `EgoCore/app/runtime_v2/loop.py:283` |
| decision loop | `_decide()` + transition apply + done handling | `EgoCore/app/runtime_v2/loop.py:255` |

## P1 拟拆分后的职责边界

| target | owned_responsibility | not_owned |
|---|---|---|
| `RuntimeV2Loop` | turn orchestration、state mutation、decision/transition 驱动、最终 result 返回 | 不直接拼 proto-self event、不开展 evidence 细节捕获、不直接编码 external_result event 结构 |
| new runtime helper | proto-self ingress event 构造、risk signal 注入、feedback event 构造、trace/evidence side-effect 封装 | 不拥有 session/state 生命周期 |
| evidence collector | 证据落盘细节 | 不拥有 runtime orchestration |
| adapter | `handle_event()` 边界调用 | 不吸收 runtime 编排逻辑 |

## 本轮选择
- 不直接抽成厚 adapter
- 先抽宿主侧 helper / pure function，再让 `loop.py` 只保留调用点
- 保持 `run_turn_typed()` 的输入输出契约不变
