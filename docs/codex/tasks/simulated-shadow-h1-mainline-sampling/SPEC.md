# Simulated Shadow H1 Mainline Sampling

## Goal

在不依赖真实 Telegram operator 的前提下，用 simulated Telegram 调用统一 ingress/egress contract，跑同一条 `telegram-like ingress -> runtime_v2 -> native_loop -> proto_self_runtime -> proto_self_adapter -> proto_self_v2 -> egress` 主线，并验证 canonical `shadow_h1` telemetry 是否能进入完整的 simulated mainline bundle。

## Non-goals

- 不把 simulated bundle 冒充 real Telegram / E4 证据
- 不做 repo-level state upgrade
- 不做 H1 live decision promotion 或 runtime efficacy claim
- 不修 seed profile / negative-control 语义本身，除非它阻断当前 harness 收样

## Constraints

- 边界约束：不新建 parallel proto_self engine；只走现有 canonical surfaces
- 仓库约束：`Trial-1/Trial-2` 只当证据源，不回写成 authority implementation
- 环境约束：不用真实 Telegram operator；允许 simulated Telegram transport shape
- 发布约束：当前任务只更新 task docs、scripts、simulated artifacts；不升级 repo-level truth

## Problem framing

- 当前问题表述：
  - real E4 task 仍需要 operator ingress，但项目已经接受“只要中间主链一致，可以模拟 Telegram 调用”
- 归一化后的问题表述：
  - 先证明 canonical H1 telemetry 能通过统一 ingress/egress 主线出现在完整 simulated bundle 中，再决定是否值得继续 real sampling
- 为什么这个 framing 更适合当前任务：
  - 它把外部 operator 依赖从实现验证里剥离，只保留 mainline consistency 与 evidence-capture fidelity

## Unknowns to eliminate

- simulated runner 是否被 task-conflict / autonomy residue 污染
- sample bundle 是否被 finalized/idle 事件覆盖，导致错读非目标 proto_self output
- canonical `shadow_h1` 是否在当前 Telegram-like path 中真实存在
- `seed_v0_2` subject profile 是否会压掉 H1 telemetry

## Acceptance criteria

- [x] frozen sample matrix 的 4 条 prompt 都生成完整 simulated mainline bundle
- [x] bundle 走统一 ingress/egress contract，不依赖真实 Telegram operator
- [x] canonical `shadow_h1` 在正样本路径上可见，或其缺失被定位到单一主线环节并有证据
- [x] `seed_v0_2` external-result path 不再无条件压掉 eligible `shadow_h1` telemetry
- [x] 输出 sample manifest / appearance / failures / sample-level report
- [x] 明确记录未证明项与下一步最小动作

## Disallowed premature claims

- 不能宣称 real Telegram / E4 已通过
- 不能宣称 H1 runtime efficacy 已证明
- 不能宣称 repo-level enablement / 生效 / 稳定成立

## Known risks / dependencies

- 风险：当前 slice 只能证明 simulated mainline；不能替代 real Telegram / E4
- 风险：`seed_v0_2` 现在能暴露 eligible `shadow_h1`，但还没证明 seed path 自己会稳定生成对应 backing shadow state
- 依赖：`FROZEN_SAMPLE_MATRIX.json`、统一 ingress/egress contract、canonical proto_self H1 patch
- 外部 blocker：无；本任务不需要 operator ingress

## Authority refs

- `PROJECT_MEMORY.md`
- `docs/codex/tasks/e4-shadow-h1-formal-mainline-sampling/FROZEN_SAMPLE_MATRIX.json`
- `EgoCore/app/runtime_v2/unified_channel_contract.py`
- `EgoCore/app/telegram_bot.py`
- `EgoCore/app/runtime_v2/proto_self_runtime.py`
- `OpenEmotion/openemotion/proto_self/h1_shadow.py`
