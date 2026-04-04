# WP12 / MVP17 Social Input / Output Contract

## Purpose

冻结 `WP12/MVP17` 第一刀的输入输出边界。目标是让 `trust / commitment / repair` 与 bounded other-modeling 只通过结构化、可审计、可治理的接口进入主链，不产出任何越权结果。

## Allowed Inputs

- `runtime_summary.social_context`
- `runtime_summary.social_self_context`
- `runtime_summary.self_model_context`
- `runtime_summary.endogenous_drive_context`
- `runtime_summary.reflective_self_context`
- `runtime_summary.developmental_self_context`
- relationship continuity markers
- commitment breach signals
- unresolved repair queue markers
- trust drift / social boundary markers
- `runtime_summary.idle_window`
- `runtime_summary.recent_delivery_outcome`
- `runtime_summary.resource_budget_hint`
- `runtime_summary.maintenance_context`

## Input Constraints

- 输入必须是结构化状态、指标或候选，不允许自由文本直接成为 formal social state
- `other-modeling` 只能表示 bounded role / relation state，不允许无证据的宽泛心智推断
- `WP8~WP11` 只能通过冻结的 read surfaces 被消费，不允许 `WP12` 反向改写它们的 owner contract

## Allowed Outputs

- `social_self_delta`
- `relation_update_candidates`
- `trust_commitment_snapshot`
- `social_policy_hints`
- `repair_proposal_candidates`
- `social_writeback_candidate`
- `trace_payload.social_context`

## Output Constraints

- 输出必须进入 governed prioritization / review / controlled observation path
- 输出必须可 trace / replay / audit
- 输出必须是结构化对象，不是直接用户可见文案
- `social_writeback_candidate` 必须保持：
  - `proposal_only = true`
  - `behavioral_authority = none`
  - `required_gate = social_writeback_gate`

## Forbidden Outputs

- final reply text
- tool command
- transport directive
- direct Governor bypass
- direct authority escalation
- autonomous social outreach
- direct identity rewrite without governed intake
- ungoverned mutation of `WP8~WP11` owner state

## Mainline Direction

`formal social owner -> structured social projection / proposals -> governed runtime bridge -> downstream prioritization, repair review, and writeback candidate path`

## Claim Boundary

- 即使 `WP12` 输入输出 contract 冻结完成，也不能宣称：
  - `MVP17` 已接主链
  - `MVP17` 已启用
  - `MVP17` 已获得 live / transport evidence
