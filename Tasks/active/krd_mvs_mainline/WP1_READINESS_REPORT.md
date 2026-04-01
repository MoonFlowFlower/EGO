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
  - `memory_claim_gate` 已进入完整宿主表达主链
  - `numeric_leak = 0`
  - `self_report_contract / SRAP` 约束已完全并入 `ResponsePlan`

## Readiness 分项

| 项目 | 当前结论 | 证据等级 | 说明 |
|------|----------|----------|------|
| `InteractionKind` / `normalize_user_turn` 作为宿主入口 authority | 已接入 | E3 | 已有代码与回归，但本报告不把它单独升级为 E4 |
| `reply_authority / reply_origin` 正式分层 | 已接入且有真实样本 | E4 | Telegram 真实样本已证明 `model_chat` 与 `host_evidence` 可在同一 session 分离 |
| `chat_mainline` 脱离 execution JSON 主链 | 已接入且有真实样本 | E4 | 普通聊天已由 `llm.use_cases.chat` 驱动 |
| `tools.delivery_bridge` | 已接入且有真实样本 | E4 | evidence delivery 已可审计 |
| `ResponsePlan` 为唯一宿主表达合同骨架 | 已接入 | E3 | 方向成立，但字段还不完整 |
| `memory_claim_gate` | 部分接入 | E2 | 仅见 status path 接线与局部测试 |
| `self_report_contract / SRAP` 约束并入 `ResponsePlan` | 未完成 | E1 | 仍停留在计划与方向口径 |
| `numeric_leak = 0` | 未证实 | E0 | 尚无当前口径 readiness 复算结果 |

## 当前 blocker

### Blocker 1
`ResponsePlan` 仍是骨架，不是 `WP1` 完整表达合同。

缺口字段:
- `speaker_mode`
- `epistemic_status`
- `commitment_level`
- `must_include`
- `must_not_upgrade`
- `tone_bounds`

### Blocker 2
`memory_claim_gate` 还没有从 status path 扩到正式宿主表达主链。

### Blocker 3
没有新的 readiness 复算来回答:
- `numeric_leak = 0` 是否成立
- SRAP Shadow 当前是否达到进入下一步的门槛

## 不应误报的事项

- 不能把当前状态报成 `WP1 完成`
- 不能把 `chat_mainline` 的 E4 样本误报成 `WP1 overall ready`
- 不能因为 `memory_claim_gate.py` 已存在就报“memory claim gate 已收口”

## 进入下一阶段前需要满足的条件

最小条件:
1. `ResponsePlan` 吸收 `WP1` 目标字段
2. `memory_claim_gate` 接入正式宿主表达主链
3. 跑一轮新的 readiness 复算，并给出 `numeric_leak` 结论

## 下一步唯一最高优先级动作

先做 `ResponsePlan + memory_claim_gate` 的最小实现收口，再重新生成 `WP1 readiness` 结果。当前不应直接推进到 `WP2`。
