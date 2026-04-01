# WP1 Readiness Report

> authority: `Tasks/MVS_task_plan.md`
> scope: `WP1 宿主壳收稳（MVP11.5）`
> date: 2026-03-31
> status: `not_ready`

## 总结

`WP1` 当前不是方向错误，而是 **已部分生效但尚未 ready**。

- 可以确认的:
  - host-chain 若干关键切片已到 E4
  - `chat_mainline` / `evidence_mainline` / `status_mainline` 已开始分离
  - `ResponsePlan` 已成为正式宿主表达合同骨架
- 还不能确认的:
  - `numeric_leak = 0`
  - `self_report_contract / SRAP` 约束已真正形成宿主 gate
  - `memory_claim_gate` 已拿到真实样本级证据

## Readiness 分项

| 项目 | 当前结论 | 证据等级 | 说明 |
|------|----------|----------|------|
| `InteractionKind` / `normalize_user_turn` 作为宿主入口 authority | 已接入 | E3 | 已有代码与回归，但本报告不把它单独升级为 E4 |
| `reply_authority / reply_origin` 正式分层 | 已接入且有真实样本 | E4 | Telegram 真实样本已证明 `model_chat` 与 `host_evidence` 可在同一 session 分离 |
| `chat_mainline` 脱离 execution JSON 主链 | 已接入且有真实样本 | E4 | 普通聊天已由 `llm.use_cases.chat` 驱动 |
| `tools.delivery_bridge` | 已接入且有真实样本 | E4 | evidence delivery 已可审计 |
| `ResponsePlan` 为唯一宿主表达主合同 | 已接入 | E3 | 核心字段已并入，但当前仍是 contract carrier，不是已生效的 SRAP gate |
| `memory_claim_gate` | 已接入 | E3 | 已进入 direct/runtime/status 三条 plan builder，但仍缺 E4 |
| `self_report_contract / SRAP` 约束并入 `ResponsePlan` | 部分完成 | E3 | 已形成 [WP1_SRAP_MAPPING.md](/mnt/d/Project/AIProject/MyProject/Ego/Tasks/active/krd_mvs_mainline/WP1_SRAP_MAPPING.md)，明确哪些已映射、哪些仍未接入 |
| `numeric_leak = 0` | 未满足 | E3 | `ResponseIntentChecker` numeric 子集 `5 passed`、完整 checker `47 passed`，但 shadow 套件 `4 failed`，且 EgoCore host path 还没有正式调用 checker |

## 当前 blocker

### Blocker 1
`self_report_contract / SRAP` 虽已部分映射进 `ResponsePlan`，但还没有形成真正的宿主 gate。

### Blocker 2
`ResponseIntentChecker` 目前没有接到 EgoCore host 输出主链。

### Blocker 3
`memory_claim_gate` 虽已接入主链，但还没有真实样本级证据。

### Blocker 4
SRAP shadow 当前仍有回归，不能作为 readiness 稳态证据。

## 不应误报的事项

- 不能把当前状态报成 `WP1 完成`
- 不能把 `chat_mainline` 的 E4 样本误报成 `WP1 overall ready`
- 不能因为 `memory_claim_gate.py` 已存在就报“memory claim gate 已收口”
- 不能因为 `ResponsePlan` 已有 SRAP 字段就报“numeric_leak = 0”

## 进入下一阶段前需要满足的条件

最小条件:
1. `ResponsePlan -> ResponseIntentChecker` 宿主接线完成
2. `memory_claim_gate` 拿到 E4 真实样本
3. 重跑 readiness 复算，并给出新的 `numeric_leak` 与 SRAP Shadow 结论

## 下一步唯一最高优先级动作

先实现最小 `ResponsePlan -> ResponseIntentChecker` 宿主接线，再重跑 `WP1 readiness` 复算。当前不应直接推进到 `WP2`。
