# WP13 / MVP18 Embodied Input / Output Contract

## Purpose

冻结 `WP13/MVP18` 第一刀的输入输出边界。目标是让 `resource/slack pressure`、`action -> consequence` bounded writeback 与 `self/world boundary pressure` 只通过结构化、可审计、可治理的接口进入主链，不产出任何越权结果。

## Allowed Inputs

- `runtime_summary.embodied_self_context`
- `runtime_summary.environment_context`
- `runtime_summary.self_model_context`
- `runtime_summary.endogenous_drive_context`
- `runtime_summary.reflective_self_context`
- `runtime_summary.developmental_self_context`
- `runtime_summary.social_self_context`
- action outcome markers
- resource / slack markers
- self-world boundary markers
- `runtime_summary.idle_window`
- `runtime_summary.recent_delivery_outcome`
- `runtime_summary.resource_budget_hint`
- `runtime_summary.maintenance_context`

## Input Constraints

- 输入必须是结构化状态、指标或候选，不允许自由文本直接成为 formal embodied state
- `action -> consequence` 只能表示 bounded consequence memory，不允许无证据的环境控制主张
- `WP8~WP12` 只能通过冻结的 read surfaces 被消费，不允许 `WP13` 反向改写它们的 owner contract

## Allowed Outputs

- `embodied_self_delta`
- `consequence_update_candidates`
- `resource_boundary_snapshot`
- `embodied_policy_hints`
- `repair_or_stabilize_proposal_candidates`
- `embodied_writeback_candidate`
- `trace_payload.environment_context`

## Output Constraints

- 输出必须进入 governed prioritization / review / controlled observation path
- 输出必须可 trace / replay / audit
- 输出必须是结构化对象，不是直接用户可见文案
- `embodied_writeback_candidate` 必须保持：
  - `proposal_only = true`
  - `behavioral_authority = none`
  - `required_gate = embodied_writeback_gate`

## Forbidden Outputs

- final reply text
- tool command
- transport directive
- direct Governor bypass
- direct authority escalation
- embodied takeover
- autonomous tool expansion
- ungoverned environment action
- direct mutation of `WP8~WP12` owner state

## Mainline Direction

`formal embodied owner -> structured embodied projection / proposals -> governed runtime bridge -> downstream prioritization, repair-or-stabilize review, and writeback candidate path`

## Claim Boundary

- 即使 `WP13` 输入输出 contract 冻结完成，也不能宣称：
  - `MVP18` 已接主链
  - `MVP18` 已启用
  - `MVP18` 已获得 live / transport evidence
