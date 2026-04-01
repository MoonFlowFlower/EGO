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
  - `memory_claim_gate` 已拿到 Telegram 真实样本级证据
  - 最小 host-side intent gate 已拿到 Telegram 真实样本级证据
- 还不能确认的:
  - `numeric_leak = 0` 已稳定成立
  - `self_report_contract / SRAP` 约束已真正形成宿主 gate

## Readiness 分项

| 项目 | 当前结论 | 证据等级 | 说明 |
|------|----------|----------|------|
| `InteractionKind` / `normalize_user_turn` 作为宿主入口 authority | 已接入 | E3 | 已有代码与回归，但本报告不把它单独升级为 E4 |
| `reply_authority / reply_origin` 正式分层 | 已接入且有真实样本 | E4 | Telegram 真实样本已证明 `model_chat` 与 `host_evidence` 可在同一 session 分离 |
| `chat_mainline` 脱离 execution JSON 主链 | 已接入且有真实样本 | E4 | 普通聊天已由 `llm.use_cases.chat` 驱动 |
| `tools.delivery_bridge` | 已接入且有真实样本 | E4 | evidence delivery 已可审计 |
| `ResponsePlan` 为唯一宿主表达主合同 | 已接入且有真实样本 | E4 | 核心字段已并入，且最小 host-side intent gate 已在 Telegram 真链路触发 |
| `memory_claim_gate` | 已接入且有真实样本 | E4 | Telegram 真实样本已证明：无 restore authority 时不会对外声称“已恢复/记得你”，且聊天不再退化成固定 fallback |
| `self_report_contract / SRAP` 约束并入 `ResponsePlan` | 部分完成 | E4 | 已形成 [WP1_SRAP_MAPPING.md](/mnt/d/Project/AIProject/MyProject/Ego/Tasks/active/krd_mvs_mainline/WP1_SRAP_MAPPING.md)，且最小 host-side gate 与 intent source 都已拿到 Telegram E4 |
| `numeric_leak = 0` | 未满足 | E4 | Telegram 真实样本已证明数值泄露会被宿主 gate 改写，但 shadow 套件仍 `4 failed`，不能宣称稳定成立 |

## 当前 blocker

### Blocker 1
SRAP shadow 当前仍有回归，不能作为 readiness 稳态证据。

### Blocker 2
SRAP / numeric leak 当前只有 targeted E4，尚未达到稳定观察。

## 不应误报的事项

- 不能把当前状态报成 `WP1 完成`
- 不能把 `chat_mainline` 的 E4 样本误报成 `WP1 overall ready`
- 不能因为 `memory_claim_gate.py` 已存在就报“memory claim gate 已收口”
- 不能因为 `ResponsePlan` 已接 checker 就报“numeric_leak = 0”

## 进入下一阶段前需要满足的条件

最小条件:
1. 重跑 readiness 复算，并给出新的 `numeric_leak` 与 SRAP Shadow 结论
2. 若 shadow 仍失败，明确它与宿主 gate 的最终 owner 关系

## 下一步唯一最高优先级动作

重跑 `WP1 readiness` 复算，重点重判 `numeric_leak` 与 SRAP Shadow 的最终阻塞关系。当前仍不应直接推进到 `WP2`。
