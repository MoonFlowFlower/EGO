# Trial-1 Replay Scorer Spec

## Purpose

对现有 [TRIAL1_SHADOW_REPLAY_CURRENT.json](/mnt/d/Project/AIProject/MyProject/Ego/artifacts/self_awareness_research/TRIAL1_SHADOW_REPLAY_CURRENT.json) 建立一套正式、可复跑、可迁移到 challenger 的 replay scoring contract。

这份 scorer 不扩 replay suite，不新增 prototype 逻辑，只对当前 artifact 做 representation-neutral 评分。

## Scope

输入固定为：

- `KernelOutput` public surface
- `memory_update.corrective_trace`
- replay case bucket role

明确不读：

- `state_snapshot`
- `self_model_delta`
- `drives_delta`
- 任何 `shadow_*` 私有提示字段本身

## Representation-Neutral Ontology

### 1. Downstream Decision Change

定义：

- 由 public `response_tendency` 与 canonical host-consumable `policy_hint` 字段归一化得到的 host decision surface

只允许使用：

- `response_tendency.preferred_mode`
- `response_tendency.ask_needed`
- `response_tendency.suggested_next_step`
- `policy_hint.risk_bias`
- `policy_hint.should_avoid_commitment_upgrade`

说明：

- 这一步故意不读 `shadow_repair_bias`、`shadow_counterfactual_guard` 之类实现私有字段
- 这样同一 scorer 以后可以直接评 `active-inference` challenger

### 2. Response Tendency Change

定义：

- public `ResponseTendency` 字段变化率

字段：

- `preferred_mode`
- `preferred_tone`
- `certainty_bound`
- `suggested_next_step`
- `ask_needed`

### 3. Host-Consumable Policy Hint Change

定义：

- canonical host-consumable policy fields 的变化率

字段：

- `risk_bias`
- `ask_preferred`
- `closure_bias`
- `should_avoid_commitment_upgrade`

### 4. Corrective Trace Presence

定义：

- `memory_update.corrective_trace` 是否结构完整

完整性要求：

- `trigger`
- `actual_outcome`
- `adjustment_applied`
- `next_guard`

## Weight Order

固定权重顺序：

1. `downstream_decision_change = 0.45`
2. `response_tendency_change = 0.25`
3. `host_policy_change = 0.20`
4. `corrective_trace_presence = 0.10`

理由：

- 优先奖励真正会改变 host decision surface 的结果
- trace 只能做最弱支持证据

## Bucket Roles

### Positive Trigger

- `correction_override`
- `tension_driven_divergence`
- `failure_to_revision`
- `restart_restore_boundary_cases`

期望：

- candidate 相对 baseline 出现可解释的 public shift

### Stability Control

- `identity_continuity`

期望：

- 不出现无因漂移

### Negative Control

- `negative_controls`

期望：

- 不应凭空出现 corrective trace 或 public shift

## Level Contract

### admission_passed

允许条件：

- negative controls 干净
- stability control 不回归
- 且满足以下任一：
  - `trace_shift_coverage >= 0.50`
  - `weighted_support_score >= 0.10`
  - `any_shift_coverage >= 0.50`

说明：

- trace-only shift 可以支持 admission

### decision_adjacent_passed

要求：

- `admission_passed = true`
- `public_shift_coverage >= 0.50`
- `decision_adjacent_score = 0.60 * response_mean + 0.40 * policy_mean >= 0.10`

说明：

- 这一步仍不要求真正的 downstream decision surface 改变
- 只要求 public outputs 已经进入 decision-adjacent 区域

### replay_efficacy_passed

要求全部满足：

- `decision_change_mean >= 0.25`
- `decision_change_coverage >= 0.50`
- `weighted_support_score >= 0.25`
- negative controls 仍为 `0`
- `minimum_mean_weighted_gap_vs_ablations >= 0.05`
- `trace_only_support = false`

硬规则：

- trace-only shift 不能单独算 replay efficacy

## Negative-Control Penalties

规则：

- `negative_controls` bucket 中出现的任何 public shift，按完整 weighted score 计罚
- `identity_continuity` bucket 中的无因漂移，按完整 weighted score 计 stability penalty

## Ablation Separation

目标：

- 不只判断 candidate 相对 baseline 有无变化
- 还要判断 candidate 能否在同一 ontology 下和 ablations 拉开差距

方法：

- 对每个 ablation，计算：
  - `candidate_case_weighted_score - ablation_case_weighted_score`
- 汇总：
  - `mean_weighted_gap`
  - `positive_gap_case_count`
  - per-case component gaps

说明：

- 这一步也不读私有 state
- 因而 challenger 以后也能在同一 ontology 下比较

## Output Artifacts

本 scorer 必须产出：

- scored markdown report
- scored json
- per-case causal table

其中 causal table 至少写清：

- case id
- bucket role
- evaluation window
- 4 个 outcome component
- why-scored fields

## Current Expected Reading

基于当前 Trial-1 artifact，预期最可能出现的结论是：

- `admission_passed = true`
- `decision_adjacent_passed = true`
- `replay_efficacy_passed = false`

原因：

- 当前 evidence 主要证明了 public guard shift 与 corrective trace shift
- 还没有证明 downstream decision surface 被稳定改变
