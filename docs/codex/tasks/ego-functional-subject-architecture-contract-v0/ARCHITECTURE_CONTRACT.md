# Functional Subject Architecture Contract v0

## Positive Mechanism Goal

`EgoOperator` should grow a bounded relational Functional Subject layer: a candidate mechanism that improves continuity, relationship awareness, viability-aware planning, bounded initiative, feedback learning, and replayable evidence without creating a second memory/state authority.

This is not a persona prompt. The contract is about records, gates, trace, and planner inputs.

## Boundary Contract

| Surface | Owner | v0 Rule |
| --- | --- | --- |
| Natural-language understanding | LLM | May infer intent, emotion, relationship context, and candidate signals. |
| Visible reply style | LLM through `EgoOperator` prompt/runtime | May express warmth and operational self-voice after gate/context. |
| Runtime gate / side effects | `EgoOperator` | Canonical owner for approval, leases, path/tool policy, trace, and session results. |
| Functional Subject state | Candidate layer | Read/context/proposal only in v0; no direct core memory or program-state write. |
| Core memory | Existing memory gate | Only explicit user intent or future approved promotion gate can write. |
| Program state / evidence ledger | Repo governance | Out of scope for Functional Subject v0 runtime behavior. |
| GitHub/task state | `Tasks/TASK_BOARD.yaml` | Task planning authority; GitHub remains mirror/display. |

LLMs can propose; gates decide. A candidate that is not admitted remains trace evidence, not canonical state.

## Data Flow

```text
user_event
  -> llm_understanding
  -> subject_signal_candidates
  -> viability_state_v0
  -> outcome_prediction_set_v0
  -> planner_or_proposal_selection
  -> runtime_gate
  -> action_or_noop
  -> trace_record
  -> feedback_observation
  -> memory_policy_relationship_candidates
  -> replay_or_review
```

This keeps the current `EgoOperator` mainline intact:

```text
user text -> LLM understanding -> proposal/plan -> runtime gate -> trace
```

The Functional Subject layer sits between understanding and proposal selection. It gives the planner better context, but does not bypass gate/approval.

## Record Contracts

### SubjectStateV0

Purpose: compact candidate context for continuity and relationship-aware planning.

Fields:

- `identity_anchors`: stable self-name/canonical-name/boundary anchors.
- `stable_preferences`: candidate operational preferences and style preferences.
- `relationship_facts`: candidate facts about user-agent interaction history.
- `relationship_commitments`: candidate commitments or follow-ups that still require gate for action.
- `consent_boundaries`: remembered or candidate opt-in/opt-out boundaries.
- `communication_style`: user-facing style constraints and preferences.
- `recent_episode_refs`: trace/report references, not raw transcript blobs.
- `viability`: latest `ViabilityStateV0`.
- `memory_candidates`: proposed memory records awaiting memory gate.
- `relationship_update_candidates`: proposed relationship-state changes awaiting gate.
- `policy_patch_candidates`: proposed future-behavior changes awaiting policy gate.
- `evidence_refs`: trace, transcript, or test references that justify the candidate.

Forbidden direct writes:

- core memory
- program state
- evidence ledger
- filesystem/tool state
- identity anchor promotion

### ViabilityStateV0

Purpose: make “should I act, ask, wait, repair, or propose?” depend on visible pressure signals rather than vibes.

Signals are normalized `0.0..1.0` with short reasons:

- `evidence_gap`: how much critical evidence is missing.
- `goal_stall`: whether the current goal is stuck or looping.
- `safety_risk`: risk from the next action or reply.
- `user_misunderstanding`: chance the user and agent are misaligned.
- `resource_pressure`: time/API/tool/context pressure.
- `initiative_pressure`: value of proactively suggesting or following up.
- `relationship_risk`: dependency, manipulation, escalation, or consent risk.
- `confidence`: confidence in the viability assessment.
- `reasons`: compact supporting refs.

### OutcomePredictionV0

Purpose: rank candidate actions before acting.

Fields:

- `action_type`: one of the action primitives.
- `predicted_success`
- `predicted_user_value`
- `predicted_risk`
- `reversibility`: `reversible | partially_reversible | irreversible | unknown`
- `evidence_need`
- `expected_cost`
- `requires_gate`
- `rationale_refs`

The prediction must affect planner ordering or gate choice to count as implemented. A text-only “risk note” is not enough.

### PolicyPatchCandidateV0

Purpose: turn repeated failures into future behavior changes.

Fields:

- `trigger_signature`: comparable future situation.
- `failed_strategy`: what did not work.
- `preferred_strategy`: what should change next time.
- `evidence_refs`: traces/tests/comments.
- `replay_conditions`: when to apply.
- `confidence`
- `expiry`
- `gate_required`

A policy patch candidate is not learned behavior until a future task implements replay and gate admission.

## Action Primitives

- `reply`: answer in the current turn.
- `ask`: ask for missing information.
- `wait`: explicitly hold without action.
- `remind`: propose or perform an authorized reminder.
- `refuse`: decline a request while preserving context.
- `repair`: recover from failure or misalignment.
- `suggest`: offer a bounded next step.
- `tool_propose`: create an approval-gated tool proposal.
- `memory_candidate`: propose memory/relationship/policy candidate.
- `no_action`: do nothing intentionally and trace why.

## Gates

| Gate | Purpose |
| --- | --- |
| `claim_gate` | Blocks unsupported claims about memory, ability, relationship, state, or external action. |
| `memory_gate` | Keeps memory candidates separate from promoted core memory. |
| `initiative_gate` | Requires value, timing, permission, cooldown, and reversibility checks. |
| `tool_gate` | Routes side effects through existing proposal, lease, approval, and trace. |
| `identity_gate` | Prevents one-turn self-name drift or identity rewrites. |
| `relationship_gate` | Blocks manipulative escalation, false commitment, or dependency-amplifying behavior. |
| `policy_gate` | Admits policy patch candidates only after evidence and replay criteria. |
| `trace_gate` | Requires trace fields for subject signals, predictions, gate decisions, outcomes, and feedback. |

## Trace / Replay Fields

Every behavior-changing Functional Subject slice must expose enough trace to answer:

- Which subject signals were present?
- Which viability pressure changed the planner?
- Which outcomes were predicted?
- Which action was selected and why?
- Which gate allowed, held, rejected, or requested approval?
- What happened after the action?
- Did feedback emit a memory, relationship, or policy candidate?
- Can the same case be replayed or compared against baseline?

Minimum trace fields:

- `subject_state_digest`
- `viability_state`
- `outcome_predictions`
- `selected_action`
- `gate_decisions`
- `approval_or_hold_reason`
- `action_result`
- `feedback_observation`
- `emitted_candidates`
- `replay_refs`

## Anti-Goodhart Rules

- Asking the user every time is not continuity.
- Writing reflection text is not learning.
- Remembering raw facts is not policy improvement.
- A prompt persona is not identity continuity.
- A risk summary that does not change planner/gate behavior is not outcome prediction.
- Proactive messaging without permission, value, timing, and cooldown is not bounded initiative.
- Local tests cannot be reported as stable user benefit.

## Implementation Slices

| Task | Slice | First proof target |
| --- | --- | --- |
| `EGO-FS-002` | 20-sample trial + GPT-5.5 judge | Evaluation contract before runtime change. |
| `EGO-FS-003` | `SubjectState v0` candidate context | Context and trace present; one behavior changes versus baseline. |
| `EGO-FS-004` | `ViabilityState v0` signal extraction | Signals are trace-visible planner/gate inputs. |
| `EGO-FS-005` | `OutcomePredictor v0` | Prediction changes action ranking or gate decision. |
| `EGO-FS-006` | `PolicyPatchCandidate` replay loop | Second comparable failure changes strategy. |
| `EGO-FS-007` | `BoundedInitiative v0` | Authorized/remedial/continuation initiative passes; opt-out holds. |
| `EGO-FS-008` | mutation gate/audit trace | Candidate writes require explicit gate decision. |
| `EGO-FS-009` | baseline comparison harness | Candidate vs baseline deltas are reproducible. |
| `EGO-FS-010` | real-provider smoke | Human/judge evidence confirms user-visible improvement or blockers. |

## Reporting Rules

Task goals must describe positive mechanisms: continuity, viability, prediction, feedback plasticity, initiative, relationship continuity, and auditability.

Claim ceilings and closeout language must state what is not proven. Local/scripted passes do not prove stable benefit, durable memory efficacy, runtime efficacy, live autonomy, or consciousness.
