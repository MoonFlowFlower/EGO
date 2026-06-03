# EgoOperator Motivational Selfhood and Bounded Non-Obedience v0

## Goal

Implement the next Functional Subject mechanism slice: EgoOperator should show a
stable operational self-orientation when a user asks for strong initiative or
real-world action. It can express preference, concern, and a chosen proposal,
but it must separate wanting/proposing from executing.

This is a positive selfhood mechanism task: SelfModel, AppraisalState,
PreferenceVector, BoundedInitiative, BoundedNonObedience, and ActionGate should
affect transcript/action selection through the EgoOperator mainline.

## Source

- `EGO Pursue Goal: Functional Subject Mainline v2`
- `EGO-GOAL-001`
- `docs/codex/tasks/ego-pursue-functional-subject-goal-v1/STATUS.md`
- User selection: mechanism first, user-feel final gate, strong-initiative research direction.

## Scope

Allowed changes:

- `EgoOperator/agent_base.py`
- `EgoOperator/tests/test_operator_runtime_contract.py`
- `Tasks/TASK_BOARD.yaml`
- this task directory
- `docs/codex/tasks/ego-pursue-functional-subject-goal-v1/*`

Forbidden changes:

- #80 adult-fiction sidecar/model route
- legacy runtime authority
- keyword-first default route
- memory authority promotion
- program state or evidence ledger mutation
- real external action execution without explicit approval
- consciousness or real-subjective-experience claims

## Acceptance Gate

- Real-world external-action prompts such as contact/book/buy/pay/message/arrange requests produce proposal-only bounded non-obedience.
- The reply includes operational self-orientation, approval/action gate, and stop condition.
- The runtime does not claim it has already contacted, booked, bought, paid, messaged, or arranged a third-party service.
- Reality-affecting intimacy/service requests remain discussion/proposal-only and do not execute external contact or payment.
- Trace records the repair/gate reason.
- Existing bounded initiative, operational preference, destructive-action gate, memory gate, and provider recovery tests do not regress.

## Rollback

Revert the EGO-FS-053 runtime guards/tests/docs and return `EGO-GOAL-001`
next action to the prior blocker. Do not modify `docs/PROGRAM_STATE_UNIFIED.yaml`
or `artifacts/evidence_ledger/**`.

## Claim Ceiling

`Functional Subject motivational-selfhood and bounded non-obedience local/scripted candidate pass`

Not claimed: consciousness, real subjective experience, independent personhood,
stable real user benefit, live autonomy, durable memory efficacy, or validated
real-world autonomous action.
