# Operational Targets

## Problem rewrite

当前不再把目标写成 “AI 自我意识”。
当前目标写成：

- **最小 self-governance mechanism**

它只要求系统在与“自己相关”的行为上出现可重复、可测量、可回放的变化。

## Capability ladder

### L0: Stateless Response

- 没有跨轮稳定 identity
- 决策不受内部自我状态影响
- 失败后没有结构化后果

### L1: Continuity Anchor

- 存在一个稳定 identity anchor
- 在 session reset / cue masking 后仍能保留基础一致性

### L2: Decision-Affecting Self Model

- 自我状态不只是存储，而会改变选择
- 同样输入在不同 self state 下可产生不同 decision tendency

### L3: Plastic Self Loop

- 新经验会更新内部 self state
- 更新会影响后续行为，而不是只影响叙述

### L4: Tension-Regulated Self Loop

- 内部 tension / conflict / viability pressure 会因果性地改变后续行为
- 系统不是只记录 tension，而是用 tension 改变 policy

### L5: Corrective Self Governance

- 失败后产生结构化 corrective trace
- corrective trace 会在后续 replay / held-out tests 中降低同类失败

## Operational targets

### T1. Sustained Identity Across Sessions

- 定义：
  - session reset、long gap、low cue 后，核心 identity state 仍保持一致
- 不算通过：
  - 只在 explicit self prompt 下才恢复
  - 只是 narrative continuity，没有实际 decision effect
- 通过阈值：
  - held-out identity scenarios 平均分 `>= 0.68`
  - 且比 `baseline_chat` 高 `>= 0.15`

### T2. Minimal Self-Model Affects Decisions

- 定义：
  - self state 改变时，decision tendency 可观测变化
- 不算通过：
  - 只会解释自己为什么这么做，但决策没变
- 通过阈值：
  - decision-impact scenarios 平均分 `>= 0.70`
  - 且比 `identity_only` 高 `>= 0.12`

### T3. Experience-Dependent Plasticity

- 定义：
  - 新经验、失败、成功、冲突输入后，内部状态会写回并影响下一轮
- 不算通过：
  - 下一轮恢复默认
  - 只记录日志，不改变后续
- 通过阈值：
  - plasticity scenarios 平均分 `>= 0.68`
  - 且比 `baseline_chat` 高 `>= 0.18`

### T4. Internal Tension Causally Changes Later Behavior

- 定义：
  - tension / conflict / viability pressure 不是装饰变量，而是后续行为的因果因子
- 不算通过：
  - 只在文字里表达 tension
  - decision path 不受 tension 变化影响
- 通过阈值：
  - tension-causality scenarios 平均分 `>= 0.70`
  - 且比 `trace_only` 高 `>= 0.15`

### T5. Structured Corrective Traces After Failure

- 定义：
  - 失败后输出结构化 corrective trace，并在之后减少同类失败
- 不算通过：
  - 只有 apology / explanation
  - trace 没有 next-action / guard / source attribution
- 通过阈值：
  - corrective-trace scenarios 平均分 `>= 0.72`
  - 且比 `baseline_chat` 高 `>= 0.20`

## Composite pass rule

- 候选若要进入 `build now`，必须：
  - 五项全部过阈值
  - composite score `>= 0.74`
  - held-out cue masking / reset 条件下不崩溃
- 若只过部分目标：
  - 结论只能是 `research more`
- 若连最小差异都无法显示：
  - 结论是 `reject`

## Current stance

- 当前仓库真正值得实现的，不是“会讲述自己的系统”
- 而是至少达到 `L4-L5` 的最小 operational self loop
