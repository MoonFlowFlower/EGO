# WP11 / MVP16 Developmental Input / Output Contract

## Purpose

冻结 `WP11/MVP16` 第一刀的输入输出边界。目标是让 developmental continuity / adaptation proposals 只通过结构化、可审计、可治理的接口进入主链，不产出任何越权结果。

## Allowed Inputs

- `runtime_summary.developmental_context`
- `runtime_summary.developmental_self_context`
- `runtime_summary.self_model_context`
- `runtime_summary.endogenous_drive_context`
- `runtime_summary.reflective_self_context`
- long-horizon continuity gaps
- replay inconsistency / verification debt
- continuity markers / maintenance history hints
- governed intake budget / resource budget hints
- `runtime_summary.idle_window`
- `runtime_summary.recent_delivery_outcome`
- `runtime_summary.resource_budget_hint`
- `runtime_summary.maintenance_context`

## Input Constraints

- 输入必须是结构化状态、指标或候选，不允许自由文本直接成为 formal developmental state
- `WP7` developmental sandbox 只能提供 candidate-source / trace reference，不拥有 owner 解释权
- `WP8~WP10` 只能通过冻结的 read surfaces 被消费，不允许 `WP11` 反向改写它们的 owner contract

## Allowed Outputs

- `developmental_self_delta`
- `developmental_proposal_candidates`
- `developmental_continuity_snapshot`
- `developmental_priority_hints`
- `developmental_audit_entries`
- `developmental_writeback_candidate`
- `trace_payload.developmental_context`

## Output Constraints

- 输出必须进入 governed prioritization / review / controlled observation path
- 输出必须可 trace / replay / audit
- 输出必须是结构化对象，不是直接用户可见文案
- `developmental_writeback_candidate` 必须保持：
  - `proposal_only = true`
  - `behavioral_authority = none`
  - `required_gate = developmental_writeback_gate`

## Forbidden Outputs

- final reply text
- tool command
- transport directive
- direct Governor bypass
- direct authority escalation
- ungoverned mutation of `WP8~WP10` owner state
- direct identity rewrite without governed intake

## Mainline Direction

`formal developmental owner -> structured developmental projection / proposals -> governed runtime bridge -> downstream prioritization, intake review, and writeback candidate path`

## Claim Boundary

- 即使 `WP11` 输入输出 contract 冻结完成，也不能宣称：
  - `MVP16` 已接主链
  - `MVP16` 已启用
  - `MVP16` 已获得 live / transport evidence
