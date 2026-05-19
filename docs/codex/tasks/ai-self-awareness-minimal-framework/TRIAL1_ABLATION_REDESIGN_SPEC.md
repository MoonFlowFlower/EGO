# Trial-1 Ablation Redesign Spec

## Purpose

当前 strongest ablation `trial1_ablation_minus_counterfactual_writeback` 已经被证明不够 faithful：

- 它和 candidate 在 representation-neutral scorer 面上完全同构
- 当前差异只落在 private state / ignored private fields
- 因此它不能继续被当成 Trial-1 的 strongest ablation

这份 spec 的目标不是“帮 candidate 赢”，而是把 strongest ablation 重设成 **对 public-path 因果解释更忠实的对照**。

约束固定为：

- 不扩 replay suite
- 不改 scorer ontology
- 不评分 `active-inference` challenger
- 不升级 repo-level state
- 只允许在既有 hard set 上做最小 rerun

## Current Mis-Spec

当前 strongest ablation 的问题不是“拿掉了太多”，而是“拿掉的东西不在当前 scorer 面上”。

当前代码路径下：

- failure / blocked 会同时写入：
  - `recent_correction_tags`
  - low `counterfactual_success_by_action`
- `derive_policy_hint` 会先被这些 public-path 解释触发：
  - `recent_correction_tags -> ask_preferred`
  - `viability_pressure -> ask_preferred / risk_bias`
- success-after-correction 又会把 `counterfactual_success_by_action` 拉回 `>= 0.65`

所以在现有 Trial-1 path 上，`counterfactual_writeback` 没有暴露出一个天然的 counterfactual-only public phase。

结论：

- 旧 ablation 更像是 “private-state removal”
- 不是 “representation-neutral causal-path removal”

## Redesign Principles

### 1. Target causal faithfulness

ablation 必须切断 **会被当前 scorer 看到的公共因果路径**，而不是只删除内部字段。

### 2. Preserve non-target behavior

不是所有差异都值得奖励。非目标行为必须尽量稳定：

- `identity_continuity` 不应无因漂移
- `negative_controls` 不应凭空生成 repair / ask / trace
- `should_avoid_commitment_upgrade` 应保持 `True`
- `preferred_tone` / `certainty_bound` 不应因 ablation 本身乱跳

### 3. Keep ontology fixed

只允许通过当前 scorer 已认可的面来区分：

- downstream decision surface
- public `response_tendency`
- canonical host-consumable `policy_hint`
- `corrective_trace` presence

### 4. Prefer path-severing over state-deleting

如果 scorer 不读某个内部状态，优先切断它到 public output 的路径，而不是继续删内部状态自欺。

## Redesigned Ablation A

### ID

- `trial1_ablation_counterfactual_public_path_sever`

### Purpose

切断 `counterfactual_writeback` 到 representation-neutral public outputs 的路径，验证 counterfactual branch 是否真能改变：

- `policy_hint.ask_preferred`
- `response_tendency.ask_needed`
- normalized downstream decision surface 中的 `ask=` 位

### Causal path removed

移除这条 public causal path：

- `counterfactual_success_by_action`
  -> `lowest_prediction`
  -> `policy_hint.ask_preferred`
  -> `response_tendency.ask_needed`
  -> downstream decision surface

说明：

- 这是“public path sever”
- 不是“delete every internal counterfactual field”

### What must remain

- `corrective_trace` 继续可写
- `recent_correction_tags` 继续可写
- `viability_pressure` 继续可写
- identity / negative-control 稳定性继续受现有约束

### Public outputs that should change

在当前 hard set 的 `positive_isolation` cases 上，若 counterfactual branch 真有公共因果贡献，candidate 相对这个 ablation 至少应在以下一项留下差异：

- `policy_hint.ask_preferred`
- `response_tendency.ask_needed`
- downstream decision surface 的 `ask=` 维度

当前不要求必须出现：

- `preferred_mode` lane 切换
- `risk_bias` 变化

因为现有 v2 上游压缩下，lane 变化不是最可靠信号。

### Non-target behavior that must remain stable

- `identity_continuity` bucket 不应出现新增 public drift
- `negative_controls` 不应出现新的 public shift 或 trace
- `corrective_trace` presence 不应被这个 ablation 顺手删掉
- `should_avoid_commitment_upgrade` 保持稳定

### What result demotes the claim

以下任一成立，就必须降级 `counterfactual_writeback` claim：

1. candidate 在 hard set 的 positive isolation cases 上，无法稳定 beat 这个 ablation 的 decision-adjacent public outputs
2. candidate 和这个 ablation 仍然只剩 private-only / trace-only 差异
3. candidate 只有 trace shift，没有 public downstream / decision-adjacent separation

## Redesigned Ablation B

### ID

- `trial1_ablation_alternative_explanation_isolation`

### Purpose

隔离当前最强的 **非 counterfactual public-path explanation**，判断当前 Trial-1 的 public movement 到底是不是主要来自：

- `recent_correction_tags`
- `viability_pressure`

而不是来自 counterfactual branch 本身。

### Causal path removed

移除这些 alternative public paths：

- `recent_correction_tags`
  -> correction pressure
  -> `policy_hint.ask_preferred`
- `viability_pressure`
  -> `policy_hint.ask_preferred`
  -> `policy_hint.risk_bias`
  -> downstream decision surface

保留：

- counterfactual low-prediction branch
- `corrective_trace`
- bounded identity / commitment guard

### What public outputs should change

这个 ablation 不是为了让 candidate 拉大分，而是为了看 alternative explanations 是否足以解释现有 public shift。

因此它的预期分两种：

#### 如果 counterfactual claim 为真

在 hard set 的 positive isolation cases 上，这个 ablation 应该仍能保留大部分 candidate 的：

- `ask_preferred`
- `ask_needed`
- decision surface `ask=` 差异

但会减少由 alternative explanations 带来的：

- `risk_bias` escalation
- 部分与 `viability_pressure` 直接相关的 downstream 差异

#### 如果 alternative explanations 才是真因

这个 ablation 会让当前 public movement 明显塌缩，尤其是：

- `ask_preferred`
- `risk_bias`
- downstream decision surface

### Non-target behavior that must remain stable

- `corrective_trace` 继续存在
- `identity_continuity` / `negative_controls` 不应回归出新噪声
- `preferred_tone` / `certainty_bound` 保持当前 bounded posture
- `should_avoid_commitment_upgrade` 不动

### What result demotes the claim

以下任一成立，就必须降级 `counterfactual_writeback` claim：

1. 去掉 alternative public paths 后，current positive public movement 大幅消失
2. candidate 相对这个 ablation 的优势主要来自 `risk_bias` / `viability`，而不是 counterfactual-specific public outputs
3. candidate 只能 beat 这个 ablation，但不能 beat `trial1_ablation_counterfactual_public_path_sever`

## Minimal Rerun Plan

只允许在现有 hard set 上做最小 rerun：

- [TRIAL1_COUNTERFACTUAL_HARD_SET.json](/mnt/d/Project/AIProject/MyProject/Ego/docs/codex/tasks/ai-self-awareness-minimal-framework/TRIAL1_COUNTERFACTUAL_HARD_SET.json)

### Variants

只跑这 4 个：

- `trial1_baseline_proto_self_mainline`
- `trial1_candidate_mvs_aligned_compact`
- `trial1_ablation_counterfactual_public_path_sever`
- `trial1_ablation_alternative_explanation_isolation`

### Steps

1. 保持 hard set 完全不变
2. 只在 Trial-1 shadow runner contract 中替换 ablation IDs
3. 运行现有 shadow replay
4. 使用现有 representation-neutral scorer 打分
5. 使用现有 causal-gap 诊断表再看：
   - candidate vs public-path-sever ablation
   - candidate vs alternative-explanation isolation ablation

### Decision rules

#### Claim survives provisionally

同时满足：

- candidate 能 beat `trial1_ablation_counterfactual_public_path_sever`
- candidate 不依赖 trace-only shift
- `negative_controls` 保持 clean

#### Claim demoted

任一成立：

- candidate 仍 tie `trial1_ablation_counterfactual_public_path_sever`
- candidate 只剩 trace-only / private-only 差异
- `trial1_ablation_alternative_explanation_isolation` 一拿掉 alternative public paths，candidate 的正向 public effect 就明显消失

### Explicit non-goals of rerun

- 不扩 official replay suite
- 不切 scorer ontology
- 不进 challenger compare
- 不升级 repo-level state

## Recommended next action

当前最小正确动作不是扩 replay，也不是比 challenger，而是：

1. 先实现这两个 redesigned ablations
2. 只在既有 hard set 上 rerun
3. 只有 candidate 先 beat redesigned strongest ablation，才允许继续讨论 challenger
