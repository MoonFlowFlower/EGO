# PSPC Read-Only Adapter Design Review v0 Admission Criteria

## Purpose

Define the minimum criteria required before PSPC may move from design review to a separate adapter implementation Stage Card. This document does not approve implementation.

Claim ceiling: `lab_only_proto_self_mechanism_candidate / design_review_only`

## Current Stage Admission

This design-review stage is admissible because prior PSPC Task 8 returned `go_for_separate_read_only_adapter_design_review_only`, while PSPC remained:

- `adapter_created=false`
- `mainline_connected=false`
- `enabled=false`
- no EgoOperator runtime import
- no adapter file
- no user-facing output
- no direct memory write

## Criteria For A Future Adapter Implementation Stage Card

All criteria must be true before a future adapter implementation Stage Card may be opened:

| criterion | required evidence | failure meaning |
|---|---|---|
| PSPC evidence artifacts stable | PSPC reports and hashes exist and still pass local lab acceptance. | Keep PSPC lab-only until evidence is regenerated or repaired. |
| Packet schema reviewed | `PACKET_CONTRACT.md` has reviewed required/forbidden fields. | Adapter could accidentally expose action authority. |
| No runtime imports planned | Future adapter plan states it will not import or mutate EgoOperator runtime/gate/memory modules during packet creation. | Adapter may become a second runtime authority. |
| No memory writes | Future adapter plan forbids `remember_note`, memory patches, memory file writes, and operator memory promotion. | PSPC trace may contaminate mainline memory. |
| No user-facing output | Future adapter plan forbids direct message text and transport/proactive triggers. | PSPC may affect real users before admission. |
| Gate compatibility proven in static contract test | A future test checks packet rejection/acceptance rules without running PSPC inside EgoOperator. | Runtime gate semantics are not protected. |
| Claim ceiling unchanged | Repo-wide highest evidence remains unchanged and PSPC claims remain lab/design-only. | Design review is overclaiming. |
| Rollback path documented | Removing adapter files and docs restores no-PSPC runtime state. | Integration is not reversible. |
| Separate Stage Card exists | A new adapter implementation Stage Card explicitly scopes files, tests, rollback, and forbidden surfaces. | This stage is being used as implementation permission. |

## Required No-Go Triggers

Return `no_go_keep_lab_only` if any of these are true:

- `EgoOperator/adapters/pspc_lab_adapter.py` already exists before a separate adapter Stage Card is approved
- any EgoOperator runtime, gate, memory, approval, trace, human-trial, or transport file must be changed for design review
- future packet shape includes action, tool call, user message, memory write, gate decision, approval, transport, schedule, or enablement fields
- PSPC lab evidence is treated as EgoOperator runtime efficacy, stable real user benefit, live autonomy, consciousness, or subjective experience

## Allowed Verdicts

- `go_for_adapter_implementation_stage_card`: a future separate Stage Card may be written for adapter implementation. This is not permission to implement in this stage.
- `no_go_keep_lab_only`: PSPC must remain lab-only and no adapter implementation Stage Card should start until blockers are repaired.

## What This Proves

This document proves that movement from design review to adapter implementation is gated by explicit evidence, schema, static compatibility, claim ceiling, and rollback criteria.

## What This Does Not Prove

It does not prove adapter readiness, adapter correctness, EgoOperator runtime efficacy, stable real user benefit, live autonomy, durable operator memory efficacy, production integration safety, consciousness, or subjective experience.

## Rollback Note

Rollback requires removing this design-review task directory, the matching evidence-ledger entry, and the matching governance/generated-view entries. No EgoOperator rollback is required because this stage creates no adapter and modifies no runtime.

