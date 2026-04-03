# WP10 / MVP15 Reflection Input / Output Contract

## Purpose

冻结 `WP10/MVP15` 第一刀的输入输出边界。目标是让 reflection / counterfactual 能力只通过结构化、可审计、可治理的接口进入主链，不产出任何越权结果。

## Allowed Inputs

- `WP8` formal self-model projection
- `WP9` drive state / priority / maintenance candidate projection
- unresolved tensions / contradiction load
- continuity break indicators
- replay traces / replay inconsistency / audit debt
- maintenance outcomes / revision history
- decision history / response-plan evidence
- `runtime_summary.idle_window`
- `runtime_summary.recent_delivery_outcome`
- `runtime_summary.resource_budget_hint`
- `runtime_summary.maintenance_context`

## Input Constraints

- 输入必须是结构化状态、指标、事件或候选，不允许自由文本直接成为 formal reflective state
- 输入可以来自 legacy reflection / counterfactual modules，但这些来源只提供 measurement / reference，不拥有 owner 解释权
- `WP8` self-model 与 `WP9` drives 只能通过冻结的 read surfaces 被消费，不允许 `WP10` 反向改写 owner contract

## Allowed Outputs

- `reflective_self_delta`
- `diagnosis_records`
- `counterfactual_records`
- `revision_proposal_candidates`
- `confidence_adjustment_hints`
- `maintenance_priority_hints`
- `trace_payload.reflection_context`
- `reflection_writeback_candidate`

## Output Constraints

- 输出必须保持 `proposal_only`
- 输出必须进入 governed downstream weighting / proposal gate path
- 输出必须可 trace / replay / audit
- 输出必须是结构化对象，不是直接用户可见文案

## Forbidden Outputs

- final reply text
- tool command
- transport directive
- direct Governor bypass
- direct authority escalation
- direct self-model mutation
- direct drive-state mutation
- direct policy rewrite

## Mainline Direction

`formal reflective owner -> structured diagnosis / counterfactual / proposal snapshot -> governed runtime bridge -> bounded proto-self consumers and writeback candidates`

## Claim Boundary

- 即使 `WP10` 输入输出 contract 冻结完成，也不能宣称：
  - `MVP15` 已接当前 runtime 主链
  - `MVP15` 已启用
  - `MVP15` 已获得 live / transport evidence
