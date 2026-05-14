# Subjective Loop v1 Product Cut Spec

## Goal

Consolidate `ego_desktop_lab` and the main EGO line around one minimal closed-loop contract:

`user event -> subject understanding / affective appraisal -> internal state delta -> autonomous proposal -> EgoCore gate -> natural response -> user feedback -> changed next behavior`.

## Authority

- `ego_desktop_lab` is a reference kernel and acceptance harness.
- Formal runtime remains `EgoCore + OpenEmotion`.
- EgoCore owns runtime ingress, safety gate, transport, output check, and external action boundary.
- OpenEmotion owns self-model, memory, appraisal, reflection, and subject-side response tendency.
- Shell / Telegram must read unified DecisionView / ResponsePlan outputs and must not recalculate selected decisions.

## Current Slice

Milestone 1: Human Conversation Loop, lab parity slice.

Implemented in this slice:

- `SubjectEvent`, `AffectiveAppraisal`, `SubjectDecision`, and `SubjectEvidence` reference contract in `ego_desktop_lab`.
- Feedback command routing for “你误解了 / 这样不对 / 有帮助 / 没帮助” style inputs.
- Session-local feedback outcome that changes the next clarification reply.
- Mainline parity harness at the decision-class level.
- Affective grounding tests that require acknowledging misalignment before proposing next steps.

## Frozen Development Surfaces

These existing proactive branches remain regression evidence only for this product cut:

- `thought_probe`
- weak-generic rebind
- bare-continue repair
- proactive timing
- self-DM live gate

They must not become the next default development surface until Milestone 1-3 replay is stable.

## Non-Goals

- No GUI.
- No real desktop action.
- No real file read/write/delete.
- No system command execution.
- No external send.
- No live LLM admission.
- No consciousness / alive / soul / live autonomy / runtime efficacy claim.

## Claim Ceiling

This cut can only support: `replay-validated subjective-agent proxy`.

It cannot prove consciousness, alive status, soul, stable live autonomy, runtime efficacy, or user benefit.
