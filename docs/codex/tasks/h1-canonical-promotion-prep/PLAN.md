# H1 Canonical Promotion Prep - PLAN

## Task summary

这是一个 planning-only 任务。目标不是实现 H1，而是判断：

- `H1` 是否能被 canonical proto_self kernel 小改表达
- 若能，如何把 Trial-2 结果翻译成 shadow-only canonical promotion prep

## Execution mode

- mode: planning
- why this mode:
  - 当前需要的是 authority-safe mapping，而不是继续实验或写代码
- proof required after discovery:
  - 只到 `planning/proposal` 级别；不构成 runtime proof

## Milestones

### M0: Canonical surface fit check

- question:
  - H1 能否在现有 canonical kernel surface 内表达，而不需要 contract stabilization
- acceptance:
  - 明确 yes / no
  - 若 no，则任务在此关闭并建议 stabilization first
- terminal label:
  - `continue` or `close`

### M1: Mapping + patch prep

- question:
  - H1 到 canonical proto_self surface 的最小映射是什么
- acceptance:
  - 交付 mapping spec 与 canonical patch plan
- terminal label:
  - `continue`

### M2: Host bridge + E4 prep

- question:
  - EgoCore 如何以最小 host bridge 消费 H1 shadow telemetry，并为 E4 样本采集留出路径
- acceptance:
  - 交付 feature flag / rollback / frontend bridge / E4 collection plans
- terminal label:
  - `close`

## Progress

- current_status: `m2_closed_shadow_promotion_prep_ready`
- current_milestone: `M2: Host bridge + E4 prep`
- milestone_state: `completed`
- candidate_vs_proof: `proof_pending`

## Decision log

- 2026-04-09:
  - `Trial-1` 与 `Trial-2` 已关闭，只能作为 evidence source
  - 这轮任务不实现 canonical patch，只做 promotion prep
  - `M0 = continue`
    - 结论：`H1` 可以表达为 canonical proto_self 的小改，不需要 `canonical-contract-stabilization first`
    - 前提：promotion 只能是 `shadow-only + flag-guarded + rollback-safe`
  - `M1 = continue`
    - 结论：H1 应映射到 canonical `SelfModel / policy_hint shadow telemetry / confidence_meta / trace_payload` surfaces
    - 明确排除：复用 `trial1_shadow.py` 作为 authority implementation
  - `M2 = close`
    - 结论：最小 EgoCore bridge 只做 read-only shadow telemetry 转发与样本采集，不改变 host decision path
    - 明确排除：把 H1 直接接入 `decision_engine.build_policy_hint_context()`

## Risks

- 最大风险：
  - 把 Trial research helper 当成 authority implementation
- 次级风险：
  - 把 shadow-only patch 偷写成 host-active behavior path
 - 现有 live reducer 风险：
   - `counterfactual_success_by_action` 一旦开始 canonical 写入，如果不先把 public derivation 与 shadow telemetry 分离，可能意外点亮 live `ask_preferred`
 - closeout 口径风险：
   - planning prep 容易被误写成 `canonicalized` 或 `runtime efficacy`

## Next step

- 当前 planning slice 已关闭
- 若继续，下一步最小动作应是新开 implementation task：
  - 在 canonical `proto_self` 上只落 `shadow-only H1 telemetry` 的最小补丁
  - 同时保持 `decision_engine` 与 scorer ontology 不变
