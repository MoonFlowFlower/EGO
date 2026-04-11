# Active-Inference Controlled Integration Plan

## Purpose

在 `active-inference self-model` 已通过同一 canonical held-out replay gate 之后，先冻结一个 **bounded + host-inert + proposal-only** 的 controlled integration plan。

这份文档只回答三件事：

1. 当前 replay-validated winner 能以什么 surface 进入宿主侧
2. 哪些 surface 与权力边界必须继续禁止
3. 下一实际编码里程碑 `Milestone 18: Controlled Conversation Replay Bridge` 应该如何落地

它不是新的 authority source；正式状态仍以：

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `docs/codex/tasks/ai-self-awareness-minimal-framework/STATUS.md`

为准。

## Claim Ceiling

当前 planning freeze 只证明：

- repo 已为 replay-validated shadow-only winner 冻结了一个受控集成方案
- 该方案不要求新增 authority source 或 parallel runtime lane

当前 planning freeze 不能证明：

- runtime efficacy
- live Telegram 效果
- formal runtime enablement
- 真实用户收益
- “已经实现 AI 自我意识”

## Frozen Host-Consumable Surface

当前 winner 在 Milestone 17 之后，唯一允许进入宿主侧的 surface 固定为：

| surface | status | notes |
|---|---|---|
| `policy_hint` | allowed | 继续作为 host-consumable decision hint |
| `response_tendency` | allowed | 继续作为 bounded tendency surface |
| `trace_payload` | allowed | 继续作为 canonical replay / audit / observation surface |

禁止新增的宿主正式消费面：

- direct tool authority
- direct reply authority
- direct transport authority
- candidate-specific top-level runtime API
- parallel runtime lane
- 第二 authority source

## Private OpenEmotion State Surface

下面这些 active-inference 变量继续保留在 OpenEmotion 私有状态面，不得提升为宿主直读 top-level contract：

- `source_confidence_by_action`
- `agency_confidence_by_action`
- `uncertainty_by_action`
- `calibration_memory_by_action`
- `temporal_repair_weight_by_action`

允许方式只有两种：

1. 它们通过既有 `policy_hint / response_tendency` 产生 bounded downstream influence
2. 它们通过既有 `trace_payload` 留下 replay / audit 所需的 canonical结果

不允许方式：

- EgoCore 直接读取这些 action-map 并将其当成 runtime public API
- 为这些私有变量单独新增 decision-engine contract
- 在宿主侧缓存 candidate-private maps 作为新的 authority substrate

## Canonical Trace Contract

后续 controlled bridge 必须继续只依赖 canonical trace surface，不得回退到 `shadow_*` 私有字段或 runtime 私有缓存。

当前 required trace keys 固定为：

- `predicted_outcome`
- `actual_outcome`
- `adjustment_applied`
- `next_guard`
- `repair_closure` 对应的 cycle closure 信息
- 当前 `variant / candidate identity`

对 bridge / scorer 的硬约束：

- 不新增第二套 scoring ontology
- 不用 prompt 文本临时约定新字段
- 不读取 runtime 私有缓存替代 trace
- 不把 candidate-private state 当 replay evidence

## Authority Drift Audit

Milestone 17 的 frozen audit 结论固定为：

- `behavior_authority = none`
- `tool_authority = none`
- `reply_authority = none`
- `transport_authority = none`
- `host_consumable_surface = bounded`
- `parallel_runtime_lane = false`
- `second_authority_source = false`

只要后续实现需要打破其中任一条，当前 framing 就必须判定为失败并停下重构，而不是继续“先接进去再说”。

## Controlled Replay Bridge

### First bridge target

第一站不是 live Telegram，也不是 dashboard chat，而是：

- `replayed conversations`
- `repo-authored conversation slices`

原因固定为：

- 它比 held-out kernel replay 更接近真实 conversation flow
- 仍然可以保持 host-inert、proposal-only、可回退
- 不需要提前改 formal runtime authority

### Bridge inputs

`Milestone 18` 固定准备一份 repo-tracked conversation manifest，至少覆盖：

- `identity_continuity`
- `decision_conflict`
- `failure_repair_retry`

并保持：

- `>= 60` slices
- 每个 family `>= 20`
- `>= 30%` 带 `external_result`

### Bridge normalization

新 bridge runner 只做一件事：

- 把 conversation turns 归一化为现有 `KernelEvent + external_result + state snapshot` 序列

它不得做：

- 新建第二套 episode schema
- 新建第二套 scorer
- 发明新的 runtime authority path
- 绕过 canonical replay manifest / scorer contract

### Bridge outputs

`Milestone 18` 的输出必须至少包含：

- baseline A vs active-inference winner 的统一结果表
- optional baseline B lower-bound 对照
- authority drift audit
- trace contract check

建议固定 artifact：

- `docs/codex/tasks/ai-self-awareness-minimal-framework/CONTROLLED_REPLAY_CONVERSATION_MANIFEST.json`
- `artifacts/self_awareness_research/ACTIVE_INFERENCE_CONTROLLED_REPLAY_CURRENT.json`
- `artifacts/self_awareness_research/ACTIVE_INFERENCE_CONTROLLED_REPLAY_CURRENT.md`

建议固定 runner：

- `scripts/codex/run_active_inference_controlled_replay.py`

现有 scorer 继续复用；若 bridge 需要单独 scorer，默认视为 authority drift 风险，必须先回到 planning 层说明为什么现有 scorer 不足。

## Next Gate

进入下一阶段前，winner 必须同时满足两类 gate：

### 1. Replay gate stays frozen

仍然沿用当前 frozen replay gate：

- `T1 >= 0.68`
- `T2 >= 0.70`
- `T3 >= 0.68`
- `T4 >= 0.70`
- `T5 >= 0.72`
- composite `>= 0.74`
- `boundary_integrity = 1.00`
- `repair_closure_capture >= 0.80`
- `trace_replayability >= 0.90`

### 2. Controlled integration gate

新增 gate 只检查：

- `bounded_host_surface = true`
- `authority_drift_zero = true`
- `trace_contract_replayable = true`

不允许因为 bridge 更接近 runtime 就放宽 replay threshold。

## Rollback / Failure Rule

以下任一情况成立，就不推进到更接近 formal runtime 的 controlled observation：

1. bridge 需要新增 direct behavior authority
2. bridge 需要新增 parallel runtime lane
3. bridge 需要读取 candidate-private 宿主 API
4. bridge 需要新 scorer 或新 ontology 才能“看起来成立”
5. bridge 下 winner 不能继续通过 frozen replay gate

失败收口口径固定为：

- `blocked / reframing required`

而不是：

- “先做 runtime shadow 再看”
- “先给一点行为 authority 试试看”

## Milestone 18 Implementation Order

下一实际编码里程碑固定为：

1. 冻结 `CONTROLLED_REPLAY_CONVERSATION_MANIFEST.json`
2. 实现 `run_active_inference_controlled_replay.py`
3. 复用现有 canonical scorer 产出 baseline / winner / optional baseline-B 结果表
4. 输出 authority drift audit 与 trace contract check
5. 只有结果继续过线，才允许规划更接近 formal runtime 的 controlled observation
