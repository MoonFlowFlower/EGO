# Proto-Self V2 / Seed V0.2 契约冻结说明

> 作用：`WP0` 的 task-scoped contract freeze 文档。
> 注意：这不是新的 schema 真相源；它只把当前正式权威源、代码路径和边界决策收成一张执行图。

## 契约族与正式归属

| 契约 | 正式归属 | 当前 canonical source | 用途 |
|------|----------|------------------------|------|
| `event_v1` | EgoCore authority / OpenEmotion mirror | `OpenEmotion/openemotion/contracts/event_v1.py` + EgoCore adapter ingress 逻辑 | EgoCore -> OpenEmotion 结构化输入 |
| `result_v1` | OpenEmotion authority | `OpenEmotion/openemotion/contracts/result_v1.py` | OpenEmotion -> EgoCore 结构化输出 |
| `proto_self.v2` | Dual boundary contract | `OpenEmotion/openemotion/proto_self_v2/schemas.py` + `EgoCore/contracts/proto_self_v2.schema.json` | 更新包、内核输出、trace bridge 的正式边界 |
| `proto_self_seed.v0.2` | OpenEmotion seed profile contract | `OpenEmotion/openemotion/proto_self_v2/seed_schemas.py` | 当 `subject_profile=seed_v0_2` 时的 seed event 子契约 |

## 正式路径

- Proto-Self 主体核：`OpenEmotion/openemotion/proto_self_v2/`
- Host-side adapter：`EgoCore/app/openemotion_adapter/`
- Host-side ingress schema：`EgoCore/contracts/proto_self_v2.schema.json`
- 参考规范：`OpenEmotion/docs/PROTO_SELF_KERNEL_V2_SPEC.md`

## 边界冻结

### EgoCore 正式主权
- 入口事件标准化
- runtime / task / tool / delivery / response plan / audit
- `event_v1` 的输入语义和 host-side 构造
- replay / trace 消费与现实裁决

### OpenEmotion 正式主权
- `result_v1`
- `proto_self_v2` 状态、更新法则、候选动作与反思结构
- `seed_v0_2` subject profile 语义
- 任何 identity / self-model / memory / appraisal / reflection 更新规则

### 明确禁止
- OpenEmotion 直接输出现实执行命令
- EgoCore 在 adapter 中偷做主体语义
- 旧 `openemotion/proto_self/` 继续承接新功能
- 再造 `proto_self.v3` 平行路径

## Replay / Trace 规则

- 真实回放优先读 trace，不允许拿当前 store 重算旧轮主体结果。
- host-side mirror 只缓存，不拥有解释权。
- `policy_hint / response_tendency` 只能影响宿主排序与倾向，不能绕过 Governor。

## 例子

- `contracts/examples/event_v1_user_message.json`
- `contracts/examples/result_v1_policy_hint.json`
- `contracts/examples/update_packet_v2_seed_user_event.json`
- `contracts/examples/update_packet_v2_exec_result.json`
