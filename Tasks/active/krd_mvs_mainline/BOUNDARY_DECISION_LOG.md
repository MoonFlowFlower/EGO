# MVS Boundary Decision Log

> 作用：记录 `WP0` 已锁定的边界与裁决决策，避免后续实现时再次出现双口径。

## DEC-001
- 日期：2026-03-31
- 决策：`Tasks/MVS_task_plan.md` 是 MVS 主线唯一最终裁决源。
- 影响：`Tasks/active/krd_mvs_mainline/` 只作为执行工作包，不再与总纲并列裁决。

## DEC-002
- 日期：2026-03-31
- 决策：`proto_self_v2 + seed_v0_2` 是当前正式现实与未来唯一主体核落点。
- 影响：`OpenEmotion/openemotion/proto_self_v2/` 是后续唯一正式主体路径；旧 `openemotion/proto_self/` 进入 compatibility / deletion inventory。

## DEC-003
- 日期：2026-03-31
- 决策：最近已落地的宿主主链切片纳入 `WP1` 基线。
- 范围：`InteractionKind`、`normalize_user_turn`、`ResponsePlan`、`output_check`、`tools.delivery_bridge`、`chat_mainline`、`reply_authority / reply_origin`、evidence/status/chat 隔离。
- 影响：`WP1` 不从零重做，先做方向复核，再补缺口。

## DEC-004
- 日期：2026-03-31
- 决策：`ResponsePlan` 是唯一正式宿主表达合同。
- 影响：`self_report_contract / SRAP` 的表达约束必须并入 `ResponsePlan`，禁止再造并行 `response_contract_v2`。

## DEC-005
- 日期：2026-03-31
- 决策：`event_v1` 视为 EgoCore 输入 authority；`result_v1` 视为 OpenEmotion 输出 authority。
- 影响：OE 侧 `event_v1.py` 当前只允许作为 mirror 落点解释；adapter 不得自行发明第二套 event/result 语义。

## DEC-006
- 日期：2026-03-31
- 决策：`WP2 / WP3` 只允许在现有 `proto_self_v2` 和 adapter 主线上原地替换。
- 影响：禁止新增 `proto_self_v3`、禁止回退到旧 `proto_self/` 平行线、禁止新建并行 adapter。
