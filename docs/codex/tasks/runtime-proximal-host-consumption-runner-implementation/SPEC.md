# Runtime-Proximal Host-Consumption Runner Implementation

## Goal

在已经冻结的 `runtime-proximal host-consumption causal planning` 之上，实现一个最小 bounded runner，比较 `Baseline A` 与 `active-inference` 在三类 frozen families 上的 host-consumable surface，而不扩大 authority、runtime public API、或 candidate-private host API。

## Non-goals

- 不做 fresh real Telegram proof
- 不做 runtime efficacy claim
- 不新增 runtime public API
- 不新增 candidate-private host API
- 不新增第二 scorer ontology
- 不把 runner 结果写成 “AI 自我意识已实现”

## Constraints

- 宿主正式消费面仍只允许：
  - `policy_hint`
  - `response_tendency`
  - `trace_payload`
- compare surface 只允许来自：
  - ingress semantics
  - `proto_self_context` 的 host-consumable subset
  - `reply_authority`
  - `authority_source`
  - `delivery_kind`
  - `response_plan`
  - `response_tendency_summary`
  - `chat_cadence_mode`
  - `output_verdict`
  - `trace_payload` handoff / corrective keys
- 明确禁止：
  - raw `reply_text` 作为 primary compare surface
  - dashboard-only debug fields
  - transport adapter internals
  - authority expansion

## Frozen scenario families

- `chat_consumption`
- `decision_conflict`
- `failure_repair_retry`

### Family interpretation

- `decision_conflict` and `failure_repair_retry` are primary mandatory families
  - they must show candidate-vs-baseline host-surface pressure
- `chat_consumption` is a bounded supporting family
  - it should surface policy / initiative / corrective pressure on the host-consumable contract during non-question ordinary chat
  - candidate-specific cadence discrimination is stronger evidence, but it is not the only valid signal if baseline and candidate saturate into the same bounded hold posture

## Acceptance criteria

- [ ] 新 runner 可在三类 frozen families 上跑 `Baseline A` 与 `active-inference`
- [ ] 产出 `current.json` 与 `current.md` artifact
- [ ] focused pytest 通过
- [ ] compare surface 未回退到 `reply_text` 或 candidate-private fields
- [ ] 当前只能宣称 bounded runner implementation，不宣称 runtime efficacy

## Authority refs

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `docs/OVERALL_PROGRESS.md`
- `docs/codex/tasks/runtime-proximal-host-consumption-causal-planning/HOST_CONSUMPTION_CAUSAL_FREEZE.md`
- `docs/codex/tasks/ai-self-awareness-minimal-framework/STATUS.md`
