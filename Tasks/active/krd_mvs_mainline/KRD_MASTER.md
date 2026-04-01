# K / R / D 重构清单（MVS 主链首批总表）

> 父级裁决源：`Tasks/MVS_task_plan.md`
> 作用：承接 `WP0 / WP1` 的执行层总表，不与总纲并列裁决。

> 口径：
> - K = 保留并整理，不改其权威职责
> - R = 以当前仓库现状为基座重写或重收口
> - D = 进入删除池，但必须晚于新主链 E3/E4 证据

| ID | 模块/路径 | 当前职责 | 正式归属 | 权威源 | 当前证据 | 主链接入 | 启用 | K/R/D | 核心问题 | 耦合对象 | 双主风险 | Shim 状态 | 失败兜底 | 本轮动作 | 目标去向/替代物 | 删除条件 | Owner |
|----|-----------|----------|----------|--------|----------|----------|------|-------|----------|----------|----------|-----------|----------|----------|-----------------|----------|-------|
| K-01 | `EgoCore/app/telegram_evidence_collector.py` / `EgoCore/app/dashboard/` / `scripts/run_telegram_real_channel_capture.py` | replay / audit / evidence / gap 汇总 | EgoCore | 宿主治理链 | E4 | 已接入 | 已启用 | K | 不应与业务重写混删 | Telegram 主链 / dashboard | 低 | 无 | governance block | 保留并登记 | `governance/replay/audit/gate` | 不删 | EgoCore |
| K-02 | `EgoCore/artifacts/` / `EgoCore/data/session_logs/` / trace/tape/replay 产物 | 真相链产物 | EgoCore | artifacts + logs | E4 | 已接入 | 已启用 | K | 是判断“重构是否变好”的基线 | runtime_v2 / evidence collector | 低 | 无 | evidence 缺失则降口径 | 保留并在矩阵里映射 | `artifacts/` 保留为 authority output | 不删 | EgoCore |
| K-03 | `EgoCore/tests/test_runtime_v2_*` / testbot / replay scenarios | 对话主链回归与 replay 证据 | EgoCore | tests + replay harness | E3 | 已接入 | 已启用 | K | 没有它无法判定新链是否真接入 | runtime_v2 / Telegram | 低 | 无 | regression fail | 保留并分类 | `tests/e2e/testbot` 逻辑集合 | 不删 | EgoCore |
| K-04 | `PROJECT_MEMORY.md` / `docs/AGENT_DEVELOPMENT_PLAYBOOK.md` / 边界与验收文档 | 边界宪章 / 证据口径 | Dual | 文档真相源 | E2 | 已接入候选 | 已启用候选 | K | 文档必须跟新链同步 | EgoCore + OpenEmotion | 中 | 无 | 文档落后时降口径 | 保留并同步引用 | `boundary/evidence/gate docs` | 不删 | Dual |
| R-01 | `EgoCore/app/telegram_bot.py` / `app/telegram_runtime_bridge.py` / `app/runtime_v2/semantic_parser.py` / `app/interaction/event_normalizer.py` | interaction ingress 分流 | EgoCore | 宿主 control plane | E3 | 已接入 | 已启用 | R | 分流仍散，chat/task/admin/ask/wait/resume 没有单一 authority | Telegram / runtime_v2 | 高 | 部分隐式 | generic fallback | 收到第一实现轮 | `interaction.classify_interaction` + `normalize_user_turn` | 新链 E4 后可绞杀旧分流 | EgoCore |
| R-02 | `EgoCore/app/telegram_runtime_bridge.py` / `app/runtime_v2/runtime_reply.py` / `app/response/verbalizer*.py` / `app/runtime_v2/proto_self_runtime.py` | response plan / reply skeleton / verbalize | EgoCore | `ResponsePlan` | E2 | 已接入候选 | 已启用候选 | R | renderer 与 contract authority 混在一起 | runtime_v2 / verbalizer / Telegram | 高 | 隐式 | bridge fallback | 第一实现轮重点 | `response_contract.response_plan` + `output_check` | 新链 E3/E4 后旧 verbal flow 才能下沉 | EgoCore |
| R-03 | `EgoCore/app/runtime_v2/tool_broker.py` / `app/runtime_v2/telegram_bridge.py` / `app/telegram_bot.py` | tool execute -> user delivery | EgoCore | delivery contract | E4 | 已接入 | 已启用 | R | 之前多次出现“工具成功但用户没拿到结果” | runtime_v2 / Telegram | 中 | 显式桥接 | blocked / final delivery | 保留主链再重收口 | `tools.executor` + `delivery_bridge` 逻辑 authority | 新 delivery E4 后可删旧旁路 | EgoCore |
| R-04 | `EgoCore/app/runtime_v2/state.py` / `loop.py` / `transition.py` / `app/runtime/task_runtime.py` | session/task runtime | EgoCore | host runtime state | E4 | 已接入 | 已启用 | R | session 与 task 状态仍存在边界混用风险 | runtime_v2 / restore / Telegram | 高 | 有历史兼容 | blocked / resume | 第二实现轮前半 | `session_runtime` / `task_runtime` 逻辑拆分 | 新 runtime E4 后再清旧路径 | EgoCore |
| R-05 | `EgoCore/app/openemotion_adapter/event_builder.py` / `proto_self_adapter.py` / `result_consumer.py` / `proto_self_contract_validator.py` / `OpenEmotion/openemotion/proto_self_v2/*` | schema adapter / kernel bridge | Dual | event/result contracts + `proto_self.v2` | E3 | 已接入 | 已启用 | R | adapter 中仍有边界漂移风险，且 `proto_self_v2` canonical path 需正式冻结 | OpenEmotion contracts / runtime_v2 | 高 | 有 mirror | contract guard | 第二实现轮前半 | `openemotion_adapter/schemas + trace_bridge + restore_injector + proto_self_v2 canonical path` | 新 contract E3/E4 后可绞杀旧隐式协议 | Dual |
| R-06 | `EgoCore/app/telegram_runtime_bridge.py` / `app/runtime_v2/decision_engine.py` / `app/response/verbalizer*.py` / `app/restore_runtime.py` | memory claim / restore outward statement | EgoCore | `MemoryClaimVerdict` | E2 | 已接入候选 | 已启用候选 | R | “记得/恢复/状态”类外显声明仍缺显式 gate | restore / response / OE output | 高 | 隐式 | soft wording | 第一实现轮或紧随其后 | `response_contract.memory_claim_gate` | 新 gate E4 后才允许删旧话术兜底 | EgoCore |
| D-01 | decision prompt / response prompt 中的暗约定字段 | prompt 文本协议 | None | 无正式 authority | E1 | 已接入候选 | 已启用候选 | D | 字段靠 prompt 文本暗约定，不可审计 | decision engine / verbalizer | 高 | 隐式黑箱 | heuristic fallback | 进入删除池 | 显式 contract / type | 新 contract E3 后 | Dual |
| D-02 | `EgoCore/app/openemotion_adapter/developmental_writeback.py` 及宿主内主体语义残留 | 宿主偷做主体更新 | OpenEmotion | self-model / appraisal / reflection | E2 | 已接入候选 | 已启用候选 | D | 边界漂移 | adapter / restore / OE | 高 | 未登记 | host workaround | 进入删除池 | 迁回 OpenEmotion 本体 | 新 OE 主链 E4 后 | Dual |
| D-03 | `EgoCore/app/runtime/interaction_loop.py` / `app/handlers/social_chat_handler.py` / 历史宿主假设路径 | 旧主链兼容路径 | EgoCore | 无单一 authority | E2 | 已接入候选 | 可能启用 | D | 已被 runtime_v2 与新宿主链替代但仍可达 | legacy runtime / social chat | 高 | 未登记 | generic fallback | 进入删除池 | 新 host chain skeleton | 新 host chain E4 后 | EgoCore |
| D-04 | generic fallback / busy reply / “当前没有运行中的任务”等通用兜底 | 症状压制型回复 | EgoCore | 无单一 authority | E3 | 已接入 | 已启用 | D | 容易遮蔽 interaction-aware state | Telegram / runtime_v2 | 中 | 隐式 | default fallback | 进入删除池 | interaction-aware router + response plan | 新 router E4 后 | EgoCore |
| D-05 | 未登记 shim / compat helper / 旧 `openemotion/proto_self/` 兼容路径 | 未治理 shim | Dual | SHIM register | E0 | 未接入 | 未启用 | D | 长期会长成黑箱与第二落点 | adapter / runtime / contracts | 高 | 未登记 | 无 | 进入删除池 | 登记后保留或删除 | 完成 shim inventory 后 | Dual |
| D-06 | 已被新链替代但仍在可达主链上的旧 handler / old bridge | 重复真相源 | EgoCore | 新 host chain | E2 | 已接入候选 | 可能启用 | D | 双主风险 | telegram bridge / handlers | 高 | 隐式 | legacy branch | 进入删除池 | 新 host chain skeleton | 新链 E4 后 | EgoCore |

## 当前结论

- 本轮不删除任何 D 项。
- `WP1` 基线已不止 `R-01 / R-02 / R-06`，还包括 `output_check`、`delivery_bridge`、`chat_mainline` 等已落地主链切片。
- 下一最小闭环动作是 `memory_claim_gate + WP1 direction audit + v2 boundary freeze`，不是新开平行宿主线。
- `K-01 ~ K-04` 继续作为观测与判真的基线，不进大清理。
