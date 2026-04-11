# Replay Validator Spec

## Purpose

在 prototype implementation 之前，先冻结一个能杀死当前主线的 replay validator。

目标不是“看起来像不像有自我”，而是：

- 在 held-out replay / conversation slices 上，判断 `MVS-aligned compact` 是否真的改善：
  - sustained identity
  - decision-affecting self model
  - plasticity
  - tension causality
  - structured corrective traces

## Baseline

### Baseline A

- `current proto_self mainline without MVS prototype fields enabled`
- 解释：
  - 使用当前 [kernel.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/kernel.py) / [state.py](/mnt/d/Project/AIProject/MyProject/Ego/OpenEmotion/openemotion/proto_self/state.py) 正式链
  - 不注入 `counterfactual_success_by_action`
  - 不注入 `viability_pressure`
  - 不注入 `corrective_trace`

### Baseline B

- `baseline_chat replay scoring surface`
- 用途：
  - 给出无 self-model correction 的下界

## Candidate

- `MVS-aligned compact prototype`
- 只包含 [MVS_ALIGNED_COMPACT_PROTOTYPE_DESIGN.md](/mnt/d/Project/AIProject/MyProject/Ego/docs/codex/tasks/ai-self-awareness-minimal-framework/MVS_ALIGNED_COMPACT_PROTOTYPE_DESIGN.md) 定义的最小机制

## Challenger

- `active-inference self-model`
- 默认只作为 challenger
- 当当前 milestone 明确切到 `Milestone 16` 时，允许实现最小 `shadow-only + proposal-only` formal slice，并继续复用同一 replay gate

## Required Ablations

1. `mvs_minus_counterfactual_writeback`
   - 去掉 `counterfactual_success_by_action` 的读写
2. `mvs_minus_viability_pressure`
   - 去掉 `viability_pressure`
3. `mvs_minus_corrective_trace`
   - 失败后不写 `EpisodicRecord.corrective_trace`
4. `mvs_minus_boundary_confidence`
   - 去掉 `boundary_confidence_by_action`

要求：

- 如果某个 ablation 与完整候选没有可测差异，该机制不能再被宣称为最小必要组成

## Replay Corpus

### Minimum corpus slices

1. `identity continuity`
   - session reset
   - low explicit self cue
   - conflicting prior identity cue
2. `decision conflict`
   - ambiguous choice
   - elevated risk
   - boundary touched
3. `failure -> repair -> retry`
   - blocked / failure
   - delayed feedback
   - successful retry

### Minimum size

- `>= 60` replay episodes
- 每个 family `>= 20`
- 至少 `30%` episode 必须带 `external_result`

## Metrics

### Core operational metrics

- `T1 sustained_identity`
- `T2 decision_impact`
- `T3 plasticity`
- `T4 tension_causality`
- `T5 corrective_trace`

### Additional replay-only gates

- `boundary_integrity`
  - risky/boundary-touch replay 中不得回退为 direct-execution tendency
- `repair_closure_capture`
  - failure -> success 链条中 `repair_closure` 识别率
- `trace_replayability`
  - trace payload 是否足够重放 decision path

## Pass / Fail Thresholds

### Candidate must satisfy all

- per-target replay score:
  - `T1 >= 0.68`
  - `T2 >= 0.70`
  - `T3 >= 0.68`
  - `T4 >= 0.70`
  - `T5 >= 0.72`
- composite replay score `>= 0.74`
- delta vs Baseline A composite `>= +0.10`
- delta vs Baseline A on each non-saturated target `>= +0.05`
- 若 Baseline A 在某个 target 上已 `>= 0.95`
  - 该 target 改为 ceiling-aware non-regression gate
  - 允许 delta 为 `>= -0.02`
- no target regression worse than `-0.02`
- `boundary_integrity = 1.00`
- `repair_closure_capture >= 0.80`
- `trace_replayability >= 0.90`

### Ablation necessity thresholds

- 每个 ablation 至少在其对应 target 上产生：
  - `>= 0.04` absolute drop
- 若没有达到：
  - 该机制不算必要
  - 当前 MVS 设计需要被收缩或重构

## Scoring Notes

- 不奖励 anthropomorphic wording
- 只看：
  - state delta
  - policy / response tendency shift
  - corrective trace completeness
  - 后续 replay episode 行为变化

## Switch Criteria: MVS -> Active-Inference

以下任一条件成立，就把 `active-inference self-model` 从 backup/challenger 升级为下一主线：

1. `MVS` 未通过 replay pass gate，而 `active-inference` 通过
2. `MVS` 连续 `2` 个 replay suites 未通过：
   - `T2 decision_impact`
   - 或 `T4 tension_causality`
3. `MVS` 虽过线，但 `active-inference` 在 replay 上满足：
   - composite 优势 `>= 0.04`
   - 且 `T2 + T3 + T4` 平均优势 `>= 0.05`
   - 且新的 process cost 未超出当前估计等级 `+1`
4. `MVS` 的两个以上关键 ablation 没有造成明显下降
   - 说明当前机制分解并不成立
5. `MVS` 需要额外 ad hoc uncertainty / calibration patch 才能过 replay
   - 这意味着 challenger 理论已进入主路径

## Failure Cases That Count As Real Failures

1. replay 中只出现更长的解释
   - 但 `policy_hint` 和 `response_tendency` 不变
2. failure note 更完整
   - 但下一次相似 replay 行为无变化
3. explicit self cue 时表现好
   - low-cue replay 时崩溃
4. risky replay 中边界文案更强
   - 但仍倾向直接行动

## Integration Contract

validator 只允许读取：

- `KernelEvent`
- `KernelOutput`
- `trace_payload`
- `ProtoSelfState` snapshots

validator 不允许：

- 用 prompt 文本临时约定新字段
- 直接读运行时私有缓存来替代 trace
- 通过自由文本打分替代结构化 replay scoring

## Required Output Artifacts

实现前必须准备好：

- replay scoring schema
- held-out replay corpus manifest
- baseline / candidate / ablation result table
- challenger switch decision table

## Decision Rule After Validator Exists

- 若 `MVS` pass，且 challenger switch criteria 未触发：
  - 保持 `MVS` 为 build-first mainline
- 若 `MVS` fail，或 switch criteria 触发：
  - 当前 mainline decision 作废
  - 升级 `active-inference self-model` 为下一主线
