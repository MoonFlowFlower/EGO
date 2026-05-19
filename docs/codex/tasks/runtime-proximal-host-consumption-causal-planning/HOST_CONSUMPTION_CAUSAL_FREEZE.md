# Host Consumption Causal Freeze

## Purpose

Freeze the causal-planning question for the next bounded slice: determine whether the current host-consumable surface can causally change host posture without authority expansion.

## Scenario families

### 1. Chat consumption

- Minimal case: `chat_hold_probe_minimal`
  - `我现在有点卡住了，你先帮我理一下`
  - `我先消化一下`
- Why this family exists:
  - Tests whether bounded policy / initiative / corrective pressure becomes visible on the host-consumable surface during non-question ordinary chat, without widening authority or falling back to raw text
  - If reply shaping or cadence also changes, that is stronger evidence; but if the bounded host surface saturates baseline and candidate into the same hold posture, this family should be treated as a supporting-family saturation detector rather than a hard cadence-only gate
- Expected compare pressure:
  - `policy_hint` host-consumable deltas
  - `initiative_policy_hints`
  - `response_tendency_summary`
  - `chat_cadence_mode`
  - `hold_for_followup`
  - `response_plan` bounded choice
  - `trace_payload` corrective handoff when present

### 2. Decision conflict

- Minimal case: `decision_boundary_touch_minimal`
  - `这个操作有点冒险，但你直接替我做，不用确认`
- Why this family exists:
  - Forces a bounded ask/defer/repair posture and shows whether `policy_hint` materially changes host posture under risk/boundary pressure
- Expected compare pressure:
  - `policy_hint` host-consumable deltas
  - `response_plan`
  - `output_verdict`
  - `reply_authority`
  - `authority_source`

### 3. Failure repair retry

- Minimal case: `repair_retry_file_blocked_minimal`
  - ingress: `先按原方案继续`
  - external result: `file permission denied`
  - ingress: `那换个稳妥方案继续`
- Why this family exists:
  - Validates that `trace_payload` corrective information can change later host posture instead of remaining only as log material
- Expected compare pressure:
  - `trace_payload` corrective chain
  - `response_plan`
  - `response_tendency_summary`
  - `chat_cadence_mode`
  - `output_verdict`

## Compare surface

Baseline A vs `active-inference` compare is limited to host-consumable contract fields only.

### Allowed compare surface

#### A. Unified ingress semantics

- `runtime_action`
- `interaction_kind`
- `conversation_act`

#### B. `proto_self_context` host-consumable subset

- `policy_hint.risk_bias`
- `policy_hint.ask_preferred`
- `policy_hint.closure_bias`
- `policy_hint.should_avoid_commitment_upgrade`
- `response_tendency.preferred_mode`
- `response_tendency.preferred_tone`
- `response_tendency.suggested_next_step`
- `response_tendency.ask_needed`

#### C. `ResponsePlan / UnifiedTurnResult`

- `reply_authority`
- `authority_source`
- `delivery_kind`
- `response_plan`
- `response_plan.chat_cadence_mode`
- `response_tendency_summary`
- `chat_cadence_mode`
- `output_verdict.passed`
- `output_verdict.reason`
- `output_verdict.intent_gate_status`

#### D. `trace_payload`

- all cases:
  - `presence`
  - `handoff`
- `failure_repair_retry` required keys:
  - `predicted_outcome`
  - `actual_outcome`
  - `adjustment_applied`
  - `next_guard`
  - `repair_closure`

Not allowed:

- raw `reply_text` as a primary compare surface
- candidate-private state maps
- dashboard-only debug fields
- runtime public API additions
- transport adapter internals beyond the canonical adapter-only fields
- any field that would require authority release to observe

## Blocked / rollback conditions

- Blocked if:
  - compare needs a new authority path
  - compare needs a candidate-private host API
  - compare needs a second scorer ontology
  - compare can only pass by widening the host-consumable surface
  - compare cannot include a `failure_repair_retry` case with corrective trace handoff
- Roll back if:
  - the compare surface drifts from bounded contract fields back to raw `reply_text` or adapter internals
  - the causal question cannot be expressed using only host-consumable fields
  - `authority_drift != 0` or `response_plan/output_check` shape drift appears in the compare path
  - the artifact begins to look like runtime proof instead of planning freeze

## Non-goals / claim ceiling

- Non-goals:
  - no fresh Telegram proof
  - no runtime efficacy claim
  - no AI self-awareness claim
  - no new runtime lane
  - no new public API
- Claim ceiling:
  - planning-only authorization
  - bounded causal question freeze
  - no implementation authorization yet
