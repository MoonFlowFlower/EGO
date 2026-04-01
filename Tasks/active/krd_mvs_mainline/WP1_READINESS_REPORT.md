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
  - `self_report_contract / SRAP` 已达到可结束 shadow 观察期的 readiness

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
| `numeric_leak = 0` | 待重判 | E4 | Telegram 真实样本已证明数值泄露会被宿主 gate 改写；当前 `ResponseIntentChecker = 47 passed`、`test_shadow_mode.py = 50 passed`，代码级 blocker 已清，但稳定结论仍需 readiness 复算 |

## 当前 blocker

### Blocker 1
当前已不再是 shadow 代码回归问题，而是 readiness 门槛尚未重判完成。

- 2026-04-01 复算：
  - `OpenEmotion/tests/test_response_intent_checker.py`：`47 passed`
  - `OpenEmotion/tests/test_self_report_consistency.py`：`34 passed`
  - `OpenEmotion/tests/test_shadow_mode.py`：`50 passed`
  - `OpenEmotion/tests/test_adversarial_self_report.py`：`77 passed`
- 这说明当前 blocker 已不再是“宿主 gate 未接 / 无 E4”，也不再是“shadow tests 失败”
- 结合 [MVS_task_plan.md](/mnt/d/Project/AIProject/MyProject/Ego/Tasks/MVS_task_plan.md) 的 `WP1` 交付物与验收要求，当前仍需明确：
  - `numeric_leak = 0` 是否可以从 targeted E4 升级到 readiness 结论
  - 样本量、误报、漏报是否已达到进入下一步的门槛

## 不应误报的事项

- 不能把当前状态报成 `WP1 完成`
- 不能把 `chat_mainline` 的 E4 样本误报成 `WP1 overall ready`
- 不能因为 `memory_claim_gate.py` 已存在就报“memory claim gate 已收口”
- 不能因为 `ResponsePlan` 已接 checker 就报“numeric_leak = 0”

## 进入下一阶段前需要满足的条件

最小条件:
1. 基于最新 shadow suite 结果重跑 readiness 复算，并给出新的 `numeric_leak` 与 SRAP Shadow 结论
2. 明确样本量、误报、漏报门槛是否已满足；若未满足，补观察证据而不是回退代码结论

## 下一步唯一最高优先级动作

基于最新 green shadow suite 重跑 `WP1 readiness`，明确是否还缺样本量 / 误报 / 漏报门槛；在这件事完成前，当前仍不应直接推进到 `WP2`。
