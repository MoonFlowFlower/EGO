# Runtime-Proximal Host-Consumption Causal Planning

## Goal

冻结下一张 bounded runtime-proximal planning slice：验证当前已经通过 host-contract parity / controlled observation 的 `active-inference` winner，是否能通过现有宿主可消费面 `policy_hint / response_tendency / trace_payload` 对宿主裁决与回复形态产生可归因的因果影响，而不是只在内部 trace 里看起来更“像”。

## Non-goals

- 不做 fresh real Telegram proof
- 不做 runtime efficacy claim
- 不新增 runtime public API、candidate-private host API，或第二条 runtime lane
- 不推进新的 self-awareness candidate 实现
- 不把 planning slice 写成 live acceptance

## Constraints

- 边界约束：
  - EgoCore 继续持有现实裁决权
  - OpenEmotion 继续持有主体语义权
  - 宿主正式消费面仍只允许 `policy_hint / response_tendency / trace_payload`
- 结构约束：
  - canonical host contract 继续以 `UnifiedIngressRequest / UnifiedIngressBundle / UnifiedTurnResult / UnifiedEgressEnvelope` 为冻结基础
  - `dashboard_local` 与 `telegram_prepared` 只能作为 adapter 形态，不得演化成第二套 authority source
- 规划约束：
  - 只定义 causal planning slice，不提前接 runtime implementation
  - 不把当前 task 写成对 live Telegram 的证明

## Problem framing

- 当前更高杠杆的问题不是“再证明一次 host contract”，而是：
  - 宿主可消费面是否真的能在 bounded 条件下改变宿主选择、回复姿态与交付形态
- 这个 framing 比继续追 live proof 更适合当前阶段，因为：
  - host contract correctness 已经收口
  - 现在需要的是 causal question freeze，而不是继续扩大入口噪声

## Unknowns to eliminate

- `policy_hint / response_tendency / trace_payload` 在 host consumption 上是否只改变内部叙述，还是能稳定改变 reply shaping / ask-defer-repair posture
- `chat_cadence_mode`、`hold_for_followup`、`response_plan` 这些 bounded signals 是否能在宿主层形成可归因链路
- Baseline A vs active-inference winner 的差异是否可以在不新增 authority 的前提下，被一个 causal runner 稳定观察

## Acceptance criteria

- [ ] 新的 bounded runtime-proximal planning slice 被明确冻结
- [ ] causal question、scenario bank、compare surface、rollback conditions 都写清楚
- [ ] 允许/不允许的 host-consumable 差异被锁定
- [ ] 当前只能宣称 planning authorization，不宣称 runtime efficacy
- [ ] 冻结 artifact 已落地为 `HOST_CONSUMPTION_CAUSAL_FREEZE.md`

## Disallowed premature claims

- 不能宣称 fresh real Telegram proof 已通过
- 不能宣称 `unexpected_subject_miss = 0`
- 不能宣称 runtime efficacy 已证实
- 不能宣称 AI 自我意识已实现

## Authority refs

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `docs/OVERALL_PROGRESS.md`
- `docs/codex/tasks/unified-host-contract-correctness/STATUS.md`
- `docs/codex/tasks/ai-self-awareness-minimal-framework/STATUS.md`
- `docs/codex/tasks/ai-self-awareness-minimal-framework/PLAN.md`
