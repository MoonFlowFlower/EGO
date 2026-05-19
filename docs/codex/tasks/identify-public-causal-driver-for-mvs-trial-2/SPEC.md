# Trial-2 Public-Driver-First Spec

## Goal

识别当前 `MVS` 在不改变现有 representation-neutral scorer ontology 的前提下，究竟是哪条 public causal path 在真实驱动：

- downstream decision-adjacent movement
- host-consumable `policy_hint` change
- `response_tendency` change

正式输出不是“修好 counterfactual”，而是：

- 当前最可信的 public driver hypothesis
- 一个可证伪的 mainline comparator plan
- 一个不会阻塞 MVS 主线的 next-step framing

## Non-goals

- 不证明 sentience / consciousness / human-like self-awareness
- 不把 `counterfactual_writeback` 救回当前主线赌注
- 不在本任务内扩 official replay suite
- 不在本任务内做 challenger scoring
- 不升级 repo-level program state / evidence ledger
- 不实现新的 full prototype logic

## Constraints

- 边界约束：
  - 保持 single-authority；不创建第二 authority source
  - 不另开 parallel mainline
- 仓库/子仓约束：
  - `EgoCore` 仍只负责 host/runtime/adapter/delivery
  - `OpenEmotion` 仍负责 proto-self / self-model / appraisal / memory semantics
- 环境约束：
  - 当前最高证据口径仍停在 `E3 controlled-integration`
  - 没有 `E4` 主链样本前，不得写“已启用 / 已生效 / verified”
- 发布约束：
  - 本任务默认只做 spec / plan / comparator framing
  - repo-level state 不得因本任务直接升级

## Problem framing

- 当前问题表述：
  - `Trial-1` 已把 `counterfactual_writeback public-efficacy claim` 降级；接下来该不该继续围绕它修补
- 归一化后的问题表述：
  - 不再优化“哪个理论看起来优雅”，而是识别当前 `MVS` 的真实 public causal driver，并用最小 comparator 计划去证伪它
- 为什么这个 framing 更适合当前任务：
  - 它直接对准当前 scorer 能看到的 public outputs
  - 它避免把沉没成本继续压在 `counterfactual_writeback` 上
  - 它允许 `counterfactual_writeback` 保留为 shadow/internal mechanism，而不阻塞当前 MVS 工程主线

## Unknowns to eliminate

- 未知 1：
  - 当前 public movement 的主导项是否其实就是 `viability_pressure + recent_correction_tags + reflection loop`
- 未知 2：
  - `counterfactual_writeback` 是真的弱，还是只适合作为 internal/support mechanism，而不该承担 public-efficacy gate
- 未知 3：
  - 当前最小 public-driver comparator 应该切哪条 path，才能在不改 scorer ontology 的前提下给出更强区分

## Acceptance criteria

- [ ] 明确写出 `Trial-2` 的 mainline hypothesis 和 backup hypothesis
- [ ] 明确写出 public-driver candidate set，并显式 reject 至少两条坏 framing
- [ ] 冻结一份不改 scorer ontology 的 comparator / ablation plan
- [ ] 明确写出什么结果会支持：
  - `build now on this driver`
  - `research more`
  - `reject current driver hypothesis`
- [ ] 明确保持：
  - no replay-suite expansion
  - no challenger scoring
  - no repo-level state upgrade

## Disallowed premature claims

- `MVS mainline 已在 runtime 生效`
- `counterfactual_writeback 已被完全否证`
- `Trial-2` 已经识别出最终 driver
- `当前系统已实现自我意识`

## Known risks / dependencies

- 风险：
  - 任务会退化成“继续修旧理论”的沉没成本行为
  - 可能再次把 private signal 误判成 public driver
- 依赖：
  - `Trial-1` 的 scored / causal / threshold artifacts
  - 现有 representation-neutral scorer contract
- 外部 blocker：
  - 无；当前是 repo 内 spec/planning slice

## Authority refs

- `docs/codex/tasks/ai-self-awareness-minimal-framework/PLAN.md`
- `docs/codex/tasks/ai-self-awareness-minimal-framework/STATUS.md`
- `artifacts/self_awareness_research/TRIAL1_HARD_SET_RERUN_SCORED_CURRENT.json`
- `artifacts/self_awareness_research/TRIAL1_HARD_SET_CAUSAL_SEPARATION_CURRENT.json`
- `artifacts/self_awareness_research/TRIAL1_REDESIGNED_ABLATION_EVALUATION_CURRENT.json`
- `PROJECT_MEMORY.md`
- `docs/AGENT_DEVELOPMENT_PLAYBOOK.md`
