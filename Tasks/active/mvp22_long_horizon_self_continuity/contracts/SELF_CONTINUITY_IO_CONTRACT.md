# WP17 / MVP22 Self-Continuity Input / Output Contract

## Purpose

冻结 `WP17/MVP22` 第一刀的输入输出边界。目标是让 long-horizon self-continuity / realized consequence persistence 只通过结构化、可审计、可治理的接口进入主链，不产出任何越权结果。

## Allowed Inputs

- `runtime_summary.initiative_realization_context`
- `runtime_summary.selfhood_integration_context`
- `runtime_summary.self_model_context`
- `runtime_summary.reflective_self_context`
- `runtime_summary.developmental_self_context`
- `runtime_summary.social_self_context`
- `runtime_summary.embodied_self_context`
- `runtime_summary.maintenance_context`
- `runtime_summary.recent_delivery_outcome`
- `runtime_summary.restart_restore_observation_context`

## Input Constraints

- 输入必须是结构化状态、指标、快照或候选，不允许自由文本直接成为 formal continuity state
- `WP17` 只能读取 `WP8~WP16` 的 frozen read surfaces，不允许把 upstream owner internals 当成可任意改写的 mutable state
- `recent_delivery_outcome` 与 `restart_restore_observation_context` 只用于 continuity consolidation / break detection，不构成 authority transfer

## Allowed Outputs

- `self_continuity_delta`
- `realized_commitment_snapshot`
- `consequence_consolidation_candidates`
- `identity_continuity_hints`
- `continuity_break_alerts`
- `self_persistence_tendency`
- `self_continuity_writeback_candidate`
- `trace_payload.self_continuity_context`

## Output Constraints

- 输出必须进入 governed review / persistence / controlled observation path
- 输出必须可 trace / replay / audit
- 输出必须是结构化对象，不是直接用户可见文案
- `self_continuity_writeback_candidate` 必须保持：
  - `proposal_only = true`
  - `behavioral_authority = none`
  - `required_gate = self_continuity_writeback_gate`

## Forbidden Outputs

- final reply text
- tool command
- transport directive
- direct Governor bypass
- direct authority escalation
- direct mutation of `WP8~WP16` owner state
- open-world free-form autonomy release
- live autonomy release

## Mainline Direction

`formal self_continuity owner -> structured continuity proposals -> governed runtime bridge -> downstream continuity review and self_continuity_writeback_candidate path`

## Claim Boundary

- 即使 `WP17` 输入输出 contract 冻结完成，也不能宣称：
  - `MVP22` 已实现
  - `MVP22` 已接主链
  - `MVP22` 已开始 observation
  - `MVP22` 已有 `E4/E5`
