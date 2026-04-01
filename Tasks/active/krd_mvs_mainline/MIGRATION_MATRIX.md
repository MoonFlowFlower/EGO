# MVS 主链迁移矩阵（逻辑映射优先）

> 目标：把 `MVS_task_plan.md` 的 `WP0 / WP1` 映射到当前仓库真实路径，供执行工作包直接开工。
> 说明：本矩阵不是独立裁决源；主裁决仍是 `Tasks/MVS_task_plan.md`。

| 目标逻辑模块 | 当前主要承接路径 | 权威归属 | 本轮动作 | 非目标 | 第一验收信号 |
|--------------|------------------|----------|----------|--------|--------------|
| `interaction.classify_interaction` | `EgoCore/app/telegram_bot.py` / `EgoCore/app/telegram_runtime_bridge.py` / `EgoCore/app/runtime_v2/semantic_parser.py` / `EgoCore/app/interaction/event_normalizer.py` | EgoCore | 抽出 interaction kind authority，固定 `chat/task/admin/ask/wait/resume` | 不重写全部 ingress 代码 | Telegram/testbot 能稳定区分六类入口 |
| `interaction.normalize_user_turn` | `EgoCore/app/interaction/event_normalizer.py` / `EgoCore/app/telegram_runtime_bridge.py` | EgoCore | 收敛用户输入标准化入口 | 不做历史 transcript 全量迁移 | normalized turn 被 interaction/router 复用 |
| `response_contract.response_plan` | `EgoCore/app/telegram_runtime_bridge.py` / `EgoCore/app/runtime_v2/runtime_reply.py` / `EgoCore/app/runtime_v2/proto_self_runtime.py` | EgoCore | 建立 ResponsePlan authority，并吸收 `self_report_contract / SRAP` 表达约束 | 不替换全部 verbalizer 文案 | final / ask / wait / blocked 统一由 plan 驱动 |
| `response_contract.output_check` | `EgoCore/app/telegram_runtime_bridge.py` / `EgoCore/app/telegram_bot.py` / `EgoCore/app/runtime_v2/delivery_policy.py` | EgoCore | 程序化校验对外文本与内部状态一致 | 不重写所有 reply copy | 工具成功后，用户交付不再断链 |
| `response_contract.memory_claim_gate` | `EgoCore/app/runtime_v2/decision_engine.py` / `EgoCore/app/restore_runtime.py` / `EgoCore/app/telegram_runtime_bridge.py` | EgoCore | 为“记得/恢复/状态”类外显声明引入 authority gate | 不把记忆本体迁回宿主 | 无证据时不再强声称“已记住/已恢复” |
| `runtime.session_runtime` | `EgoCore/app/runtime_v2/state.py` / `EgoCore/app/telegram_bot.py` / `EgoCore/app/interaction/session_context_store.py` | EgoCore | 识别 session 级状态边界 | 不替换 runtime_v2 主循环 | 跨轮 session 状态不再误吞 task 状态 |
| `runtime.task_runtime` | `EgoCore/app/runtime_v2/loop.py` / `transition.py` / `run_items.py` / `EgoCore/app/runtime/task_runtime.py` | EgoCore | 把 task frontier、resume、delivery 与 session 分层 | 不一次性删掉旧 runtime 目录 | run/item 状态推进与外部交付一致 |
| `tools.delivery_bridge` | `EgoCore/app/runtime_v2/tool_broker.py` / `EgoCore/app/runtime_v2/telegram_bridge.py` / `EgoCore/app/telegram_bot.py` | EgoCore | 明确“工具结果 -> 用户交付”的单一主路 | 不更换全部 tool API | tool success 必须对应 delivery 证据 |
| `openemotion_adapter.schemas.event_v1` | `EgoCore/app/openemotion_adapter/event_builder.py` + `OpenEmotion/openemotion/contracts/event_v1.py` | EgoCore authority / OpenEmotion mirror | 冻结 `event_v1` authority 为 EgoCore 输入合同，OE 只 mirror | 不新建 shared/common 契约层 | adapter 输入 schema 唯一、可审计 |
| `openemotion_adapter.from_kernel_output` | `EgoCore/app/openemotion_adapter/result_consumer.py` / `proto_self_adapter.py` | EgoCore consumer / OpenEmotion output authority | 明确只消费结构化 `result_v1` | 不在 adapter 发明主体语义字段 | prompt 文本协议进一步收缩 |
| `openemotion_adapter.restore_injector` | `EgoCore/app/openemotion_adapter/proto_self_restore.py` / `proto_self_state_store.py` / `EgoCore/app/restore_runtime.py` | EgoCore | 只保留薄 restore/mirror 注入 | 不把主体状态更新留在宿主 | restore 注入与 memory claim 分离 |
| `openemotion_adapter.trace_bridge` | `EgoCore/app/openemotion_adapter/proto_self_trace_bridge.py` / `EgoCore/app/runtime_v2/proto_self_runtime.py` | EgoCore | 保留 trace 桥，不承载主体语义 | 不重做整个 evidence collector | trace 继续进入 replay/audit |
| `OpenEmotion.result_v1` | `OpenEmotion/openemotion/contracts/result_v1.py` | OpenEmotion | 保持唯一权威源 | 不在 EgoCore 再造 result contract | EgoCore 只 mirror/consume |
| `OpenEmotion.service.process_event` | `OpenEmotion/openemotion/proto_self_v2/kernel.py` / `OpenEmotion/openemotion/proto_self_v2/seed_kernel.py` | OpenEmotion | 继续由主体本体处理 event，旧 `proto_self/` 只进兼容/删除池 | 不把 runtime 裁决迁入 OE | OE 先给结构化倾向，宿主后裁决 |

## 当前基线（已落地）

- `interaction.classify_interaction`
- `interaction.normalize_user_turn`
- `response_contract.response_plan`
- `response_contract.output_check`
- `tools.delivery_bridge`
- `chat_mainline`

## 下一实现轮建议顺序

1. `response_contract.memory_claim_gate`
2. `WP1` 方向复核与 readiness report
3. `openemotion_adapter.schemas.event_v1` / `OpenEmotion.service.process_event` 的 `v2` 边界冻结

## 第二实现轮建议顺序

1. `runtime.session_runtime` / `runtime.task_runtime` 明确拆层
2. `openemotion_adapter.restore_injector` / `trace_bridge` 收口
3. `WP2` `proto_self_v2` 方向审计后的 gap 补齐

## 明确禁止

- 不新增 `common/`、`shared/`、`contracts_common/`
- 不在第一轮做目录 rename
- 不在没有 E3/E4 证据前删除 legacy reachable 路径
- 不新增 `proto_self_v3/`
- 不把旧 `openemotion/proto_self/` 重新拉回正式落点
