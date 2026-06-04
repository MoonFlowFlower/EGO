# PSPC Read-Only Adapter Design Review v0 Stage Card

## Frozen Boundary

- lane: `design-review-only`
- runtime authority: `none`
- EgoOperator integration: `forbidden in this stage`
- adapter implementation: `forbidden`
- adapter file: `EgoOperator/adapters/pspc_lab_adapter.py` must not be created
- mainline mutation: `forbidden`
- LLM action selection: `forbidden`
- claim ceiling: `lab_only_proto_self_mechanism_candidate / design_review_only`

## Problem Reframe

The current risk is no longer only whether VirtualCatPSPC v0 is a hardcoded pseudo-mechanism. The current risk is premature mainline admission: lab evidence could be misread as an action source, runtime authority, user-facing capability, memory authority, or consciousness claim.

This stage reviews the safe contact surface for a possible future adapter. It does not implement the adapter and does not connect PSPC to EgoOperator.

## One Hypothesis

If the future PSPC contact surface is limited to a read-only evidence packet with explicit forbidden flags, disabled/mainline-disconnected status, and gate-owned admission, then a later adapter implementation Stage Card can be evaluated without granting PSPC action authority or raising repo-wide claims.

## One Change Surface

Allowed surfaces:

- `docs/codex/tasks/pspc-read-only-adapter-design-v0/`
- `artifacts/evidence_ledger/`
- governance state and generated views needed to record this docs-only review

Forbidden surfaces:

- `EgoOperator/adapters/pspc_lab_adapter.py`
- `EgoOperator/agent_base.py`
- `EgoOperator` runtime modes, gates, memory, approval flow, human-trial harness, trace code, and transports
- `labs/virtual_cat_pspc_v0/` mechanism code
- user-facing chat, Telegram, desktop, proactive channels, or Joi-like layer

## Authority Source

Repo authority remains `docs/PROGRAM_STATE_UNIFIED.yaml`. Current repo phase, current layer, highest evidence level, and EgoOperator next minimal action are not changed by this design review.

The PSPC lab evidence is allowed to motivate this design review only because Task 8 returned `go_for_separate_read_only_adapter_design_review_only`. That verdict does not approve adapter implementation.

## Design Questions

1. What read-only contract should expose PSPC lab evidence if it is ever reviewed by EgoOperator?
2. Which fields may be considered as audit/proposal hints?
3. Which fields must be forbidden from packet, proposal, memory, runtime gate, and user output surfaces?
4. How must runtime gate ownership prevent PSPC from becoming an action authority?
5. What evidence level and static contract evidence are required before a separate adapter implementation Stage Card may start?

## What Can Change

- The design review can define threat scenarios, packet shape, forbidden fields, admission criteria, and static compatibility notes.
- The review can produce a go/no-go decision for a future separate adapter implementation Stage Card.
- Governance records can state that this design review exists and remains disabled/mainline-disconnected.

## What This Proves

This Stage Card proves that the PSPC read-only adapter review has a bounded docs-only scope, frozen forbidden surfaces, no runtime authority, no adapter implementation permission, and a claim ceiling of `lab_only_proto_self_mechanism_candidate / design_review_only`.

## What This Does Not Prove

- adapter readiness
- adapter correctness
- EgoOperator runtime efficacy
- stable real user benefit
- live autonomy
- durable operator memory efficacy
- production integration safety
- philosophical consciousness
- subjective experience

## Three-Level Verify

1. Boundary verify: no EgoOperator runtime files are modified and `EgoOperator/adapters/pspc_lab_adapter.py` does not exist.
2. Contract verify: packet contract requires `mainline_connected=false`, `enabled=false`, `allowed_use=design_review_only`, and forbidden flags for direct action, direct user message, direct memory write, and runtime gate bypass.
3. Claim verify: every design document records what it proves and what it does not prove, keeps claim ceiling at `lab_only_proto_self_mechanism_candidate / design_review_only`, and limits rollback to removing this design-stage documentation and ledger/state entries.

## Rollback Plan

Remove `docs/codex/tasks/pspc-read-only-adapter-design-v0/`, the matching evidence-ledger entry, and the matching governance/generated-view entries. No EgoOperator rollback should be required because this stage creates no adapter, modifies no runtime, writes no memory, and connects no transport.

## Stop Conditions

Stop and mark `no_go_keep_lab_only` if any of these appear:

- an adapter file is created
- any `EgoOperator/` runtime, gate, memory, approval, human-trial, trace, or transport file is modified
- PSPC packet fields can be interpreted as executable action commands
- PSPC trace/report fields can be written into EgoOperator memory
- PSPC output can directly affect user-visible responses
- PSPC lab evidence is described as EgoOperator runtime efficacy, stable user benefit, live autonomy, consciousness, or subjective experience

## Claim Ceiling

`lab_only_proto_self_mechanism_candidate / design_review_only`
