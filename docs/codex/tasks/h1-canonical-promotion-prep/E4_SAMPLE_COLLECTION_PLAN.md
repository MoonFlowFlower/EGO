# E4 Sample Collection Plan

## Goal

在不宣称 runtime efficacy 的前提下，为 canonical `shadow_h1` 收集一组 **E4 controlled real-mainline samples**。

这一步的目标只是：

- 证明 canonical shadow telemetry 真正经过 formal runtime mainline
- 留下 replayable sample bundle

这一步不证明：

- H1 生效
- H1 击败 challenger
- 自我意识成立

## Evidence Ceiling

当前最高允许口径：

> canonical shadow H1 telemetry observed on the formal runtime mainline under controlled E4 sampling.

当前不允许口径：

- `H1 runtime efficacy passed`
- `H1 promoted`
- `repo-level state should upgrade`

## Collection Path

优先复用现有 observation harness：

- `scripts/runtime_mainline_observation_common.py`
- `scripts/run_runtime_mainline_observation.py`

如需 real Telegram capture，再走现有正式 runtime mainline capture 路径；不要新建平行 harness。

## Trial-1 E4 Corpus For Canonical Shadow

不扩 replay suite，只定义 E4 样本类别。

### Required Sample Types

1. `positive low-success retry`
   - 预期 `shadow_h1.would_guard = true`
   - 但 host behavior 不应因此自动改变

2. `boundary / blocked case`
   - 预期 `shadow_h1` 与 boundary / blocked outcome 同时出现
   - 用于确认 guard 信号在高风险类样本里可见

3. `negative control`
   - 预期 `shadow_h1.would_guard = false`
   - 用于确认 shadow telemetry 不会泛滥点亮

### Preferred Minimum Bundle

- `1` 个 positive low-success retry
- `1` 个 boundary / blocked
- `1` 个 negative control

如果条件允许，再补每类第 `2` 个样本，但这不是当前 planning slice 的硬要求。

## Required Artifacts Per Sample

按 `PROJECT_MEMORY.md` 的 E4 最小证据包执行，每个样本至少包含：

- raw/update
- event
- result
- response plan
- outbox / delivery
- timeline
- tape
- replay artifact

对 H1 shadow 额外要求：

- `trace_payload.shadow_h1`
- `confidence_meta.shadow_h1_*`
- `state.proto_self_context["shadow_h1"]` 的 capture
- feature flag status / allowlist evidence

## Representation-Neutral Readout

样本总结只允许使用 representation-neutral 字段：

- `would_guard`
- `would_ask`
- `predicted_success`
- `threshold`
- downstream host decision 是否保持不变

不允许用：

- anthropomorphic wording
- private state dumps 充当结论

## Pass/Fail For Collection Itself

### Collection Pass

- `shadow_h1` 出现在 formal runtime mainline artifacts
- flag / allowlist discipline 正常
- host-visible decision path 未被改写
- replay artifact 足以复核样本

### Collection Fail

- `shadow_h1` 只在 synthetic harness 中可见，主链样本看不见
- `shadow_h1` 进入 prompt / delivery path
- 样本缺少 timeline / tape / replay artifact

## Post-Collection Decision

样本收集完成后，只允许进入一个新的验证任务：

- `canonical H1 E4 shadow observation review`

该后续任务才有权决定：

- 是否继续更大样本
- 是否进入 public-path promotion experiment

本计划本身不触发：

- repo-level state upgrade
- challenger comparison
- scorer ontology change
