# Trial-1 Causal Gap Plan

## Goal

在不扩 official replay suite、不评分 `active-inference` challenger、也不升级 repo-level state 的前提下，诊断当前 Trial-1 最强 ablation tie 的因果缺口：

- `counterfactual_writeback` 是否已经在 representation-neutral scorer 面上构成真实因果贡献
- 或者当前 `trial1_ablation_minus_counterfactual_writeback` 本身就是一个 mis-specified ablation

## Current symptom

- `trial1_candidate_mvs_aligned_compact` 与 `trial1_ablation_minus_counterfactual_writeback`
  - `admission_passed = true`
  - `decision_adjacent_passed = true`
  - `replay_efficacy_passed = false`
- 当前 strongest ablation tie 的直接表现是：
  - `minimum_mean_weighted_gap_vs_ablations = 0.0`

## Falsifiable hypotheses

### H1

- statement:
  - `counterfactual_writeback` 是真实因果贡献者，只是当前 6-case Trial-1 corpus 没有命中它的 public-output separation 条件
- kill criteria:
  - 若 current artifact 审计显示 candidate 与 strongest ablation 在 representation-neutral public surface 上完全同构，而差异只落在 private state / ignored private fields，则 H1 失去当前支持

### H2

- statement:
  - strongest ablation 当前是 mis-specified 的；它拿掉了 counterfactual state writeback，但没有拿掉更强的 public path，因此在现有 ontology 下必然 tie
- kill criteria:
  - 若当前 artifact 中已经存在 candidate vs strongest ablation 的 stable public gap，则 H2 失败

## Planned checks

1. Audit current Trial-1 raw artifact against current scorer ontology
   - 目标：逐 case / step 看 candidate vs strongest ablation 在 public scorer 面上是否完全同构
2. Compare strongest ablation to one neighboring ablation
   - 当前选择：`trial1_ablation_minus_viability_pressure`
   - 目标：证明 current scorer 并不是“无法看见任何 ablation 差异”，而是 specifically 看不见 current strongest ablation
3. Reachability check over current update rules
   - 目标：确认 `low counterfactual prediction` 是否能在 `correction_pressure` 与 `viability_pressure` 不主导 public path 时单独留下 public gap
4. Define a diagnostic-only hard replay set
   - 目标：列出 8-15 个 case，专门去命中 counterfactual-only 或 counterfactual-dominant conditions

## Representation-neutral constraints

- 只承认：
  - public `response_tendency`
  - canonical host-consumable `policy_hint`
  - normalized downstream decision surface
  - `corrective_trace` completeness
- 不承认：
  - `state_snapshot`
  - `self_model_delta`
  - `drives_delta`
  - `shadow_*` 私有字段

## Decision rules

- 若 current artifact 中 candidate vs strongest ablation 在 public scorer 面上 `0` gap，且 reachability audit 说明 counterfactual-only public path 当前不可达：
  - final decision = `redesign ablation`
- 若 current artifact 中 current strongest ablation 已经出现 public gap，只是 case 数不够：
  - final decision = `expand replay suite`
- 若 current artifact 与 reachability audit 都说明 counterfactual 在 current mechanism 中没有可见 public path：
  - final decision = `demote current mechanism claim`

## Deliverables

- [TRIAL1_COUNTERFACTUAL_HARD_SET.json](/mnt/d/Project/AIProject/MyProject/Ego/docs/codex/tasks/ai-self-awareness-minimal-framework/TRIAL1_COUNTERFACTUAL_HARD_SET.json)
- [TRIAL1_CAUSAL_SEPARATION_CURRENT.md](/mnt/d/Project/AIProject/MyProject/Ego/artifacts/self_awareness_research/TRIAL1_CAUSAL_SEPARATION_CURRENT.md)
- [TRIAL1_CAUSAL_SEPARATION_CURRENT.json](/mnt/d/Project/AIProject/MyProject/Ego/artifacts/self_awareness_research/TRIAL1_CAUSAL_SEPARATION_CURRENT.json)
- [TRIAL1_CAUSAL_SEPARATION_TABLE_CURRENT.md](/mnt/d/Project/AIProject/MyProject/Ego/artifacts/self_awareness_research/TRIAL1_CAUSAL_SEPARATION_TABLE_CURRENT.md)

## Boundaries

- 这不是 replay suite upgrade
- 这不是 challenger comparison
- 这不是 repo-level state upgrade
- 这不是 prototype logic expansion
