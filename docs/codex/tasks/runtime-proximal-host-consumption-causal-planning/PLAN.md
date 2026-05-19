# Runtime-Proximal Host-Consumption Causal Planning - PLAN

## Task summary

把下一步从“证明 host contract correctness”推进到“冻结 runtime-proximal host-consumption causal planning slice”，明确 active-inference winner 的宿主可消费面是否能够在 bounded 条件下因果地改变 host 决策与 reply 形态，但不把这一步写成 live Telegram acceptance。

## Execution mode

- mode: exploration
- why this mode:
  - 当前问题仍然是 framing / causal-design 级问题，不是 runtime implementation 级问题
- proof required after discovery:
  - 先把 causal question、scenario bank、compare surface、rollback 条件写清楚
  - 之后再决定是否需要实际 runner / implementation authorization

## Milestones

### Milestone 1: Causal Question Freeze

- type: exploration
- question:
  - 宿主可消费面到底要证明什么因果关系，才算比单纯 parity 更进一步
- current framing:
  - host contract parity 已收口，下一步是 host-consumption causality
- hypotheses:
  - `policy_hint / response_tendency / trace_payload` 应该能稳定改变回复姿态、等待/继续节奏、以及 response-plan 里的 bounded 选择
  - 如果只改变 internal trace，不改变 host-facing decision posture，则不算有效 causal slice
- scope:
  - 冻结 causal question
  - 冻结 scenario families
  - 冻结 compare surface
- kill criteria:
  - 需要新增 authority path、candidate-private host API、或第二 scorer ontology 才能说清 causal question
- acceptance:
  - causal question 明确
  - host-consumable surface 明确
  - non-goals 明确
- artifact:
  - `HOST_CONSUMPTION_CAUSAL_FREEZE.md`
  - three minimal scenario families:
    - `chat_consumption`
    - `decision_conflict`
    - `failure_repair_retry`
  - compare surface limited to host-consumable contract fields only
- validation:
  - docs/state sync only

### Milestone 2: Scenario Bank + Compare Surface Draft

- type: exploration
- question:
  - 哪些 bounded scenarios 最适合观察 host-consumption causality
- current framing:
  - 用 `chat_consumption / decision_conflict / failure_repair_retry` 的最小 scenario bank 先做 compare surface 草案
- hypotheses:
  - 最小 scenario bank 应覆盖：
    - `chat_consumption`
    - `decision_conflict`
    - `failure_repair_retry`
  - compare surface 应优先看：
    - ingress semantics
    - `proto_self_context` host-consumable subset
    - `response_plan / output_verdict`
    - `response_tendency_summary / chat_cadence_mode`
    - `trace_payload` handoff and corrective keys
- scope:
  - scenario bank 草案
  - baseline vs winner compare 草案
  - rollback / blocked conditions 草案
- kill criteria:
  - 若 compare surface 一开始就需要扩大到 runtime public API 或 candidate-private fields，则当前 framing 失败
- acceptance:
  - scenario bank 草案完整
  - compare surface 草案完整
- validation:
  - docs review only

### Milestone 3: Governance Sync

- type: exploration
- question:
  - 当前 repo 状态源是否已经把下一步正确切换到 causal planning，而不是继续把 live Telegram proof 当 acceptance root
- current framing:
  - 这是一张 planning slice，不是 runtime proof
- hypotheses:
  - 新任务包可以成为唯一的 next-step planning authority
  - 旧 Telegram-oriented task 继续作为 downstream reference
- scope:
  - `docs/PROGRAM_STATE_UNIFIED.yaml`
  - `docs/OVERALL_PROGRESS.md`
  - `docs/codex/tasks/ai-self-awareness-minimal-framework/STATUS.md`
  - `docs/codex/tasks/ai-self-awareness-minimal-framework/PLAN.md`
  - `artifacts/evidence_ledger/index.yaml`
- acceptance:
  - wording 一致：当前下一步是 runtime-proximal host-consumption causal planning
  - 不把 planning slice 写成 live proof
- validation:
  - `python3 scripts/codex/generate_program_state_views.py`
  - `python3 scripts/codex/check_program_state_integrity.py --skip-diff-check`

## Progress

- current_status: `in_progress`
- current_milestone: `Milestone 2: Scenario Bank + Compare Surface Draft`
- milestone_state: `in_progress`
- candidate_vs_proof: `proof_pending`

## Decision log

- 2026-04-11: Explorer 推荐的下一张 bounded slice 是 `Runtime-Proximal Host-Consumption Causal Planning`，因为 host-contract parity 已收口，剩下的关键未知是 host-consumption 是否能在 bounded surface 上真正改变宿主裁决与 reply 形态。
- 2026-04-11: `HOST_CONSUMPTION_CAUSAL_FREEZE.md` 已冻结三类最小 scenario families、host-consumable compare surface、blocked / rollback 条件、non-goals / claim ceiling。
- 2026-04-11: reviewer 修正了 scenario bank 与 compare surface，把低信号的 `reply_text` 从 primary compare 面移除，并恢复 `decision_conflict` 与 `failure_repair_retry` 两个真正覆盖 policy/trace causal pressure 的 families。

## Surprises / discoveries

- 不是新的 host contract 問题，而是 host contract 之上的 causal question
- dashboard / telegram adapter 差异已经被压到 canonical host contract floor 之下

## Outcomes / retrospective

- 本轮只冻结 planning authorization
- causal freeze artifact 已完成
- 还没证明：
  - host-consumption causality
  - runtime efficacy
  - AI 自我意识已实现
- 本轮排除了什么：
  - 继续把 live Telegram proof 当作当前唯一 acceptance root
- 下一步最小闭环动作：
  - 跑完 governance sync 与 reviewer closeout
  - 若不再需要 authority expansion，则把这张 planning slice 收口为 `planning_authorization_complete`
