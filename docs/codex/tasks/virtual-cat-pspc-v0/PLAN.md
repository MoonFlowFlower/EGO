# VirtualCatPSPC v0 Evidence Hardening Plan

## Goal

Move VirtualCatPSPC v0 from one-time lab evidence toward a repeatable, ablatable, generalizable, admission-ready proto-self mechanism candidate.

This is not a plan to implement consciousness, a Joi-like companion, a user-facing route, or EgoOperator runtime integration.

## Fixed Constraints

- every round must be a small scoped commit
- every round must have explicit acceptance
- no EgoOperator runtime edits
- no user-facing route
- no repo-wide claim ceiling increase
- every round must state what it proves and what it does not prove
- maximum destination is admission contract; no direct runtime integration

## Roadmap

0. Closeout hygiene: separate PSPC-local success from repo-wide verification gaps.
1. Anti-hardcoding audit: prove the current behavior is not object-name decisioning such as `if cup then avoid`.
2. Multi-seed and multi-layout generalization.
3. World-model causal strength.
4. Self-model causal strength.
5. Memory consolidation admission.
6. Homeostatic value anti-reward-hacking.
7. Admission packet contract, with no adapter.
8. Go / no-go review for a future read-only adapter design.

## Current Milestone

Task 7 only: admission packet contract, with no adapter.

## Out Of Scope For This Milestone

- adapter design or implementation
- EgoOperator adapter file creation
- EgoOperator runtime imports or edits
- user-facing route creation
- repo-wide evidence ceiling uplift

## Acceptance

- `docs/codex/tasks/virtual-cat-pspc-v0/ADMISSION_PACKET_CONTRACT.md` exists.
- `artifacts/virtual_cat_pspc_v0/admission_packet_contract.schema.json` and `ADMISSION_PACKET_CONTRACT_REPORT.md` exist.
- The schema requires `source`, `claim_level`, `mainline_connected`, `enabled`, `proposal`, `evidence`, and `forbidden`.
- The packet requires `claim_level=lab_only_proto_self_mechanism_candidate`, `mainline_connected=false`, and `enabled=false`.
- The packet uses `proposal.trace_refs`; `reason_trace_refs` is rejected.
- All forbidden flags are required and true: `direct_action`, `direct_user_message`, `direct_memory_write`, and `runtime_gate_bypass`.
- Tests prove no EgoOperator runtime import and no `EgoOperator/adapters/pspc_lab_adapter.py` file.
- The report includes what this proves, what this does not prove, failure meaning, and rollback note.

## What This Milestone Can Prove

Within the deterministic PSPC lab, this milestone can prove only that a future host-facing PSPC output is bounded to a disabled, mainline-disconnected, proposal-only packet schema with audited evidence fields and forbidden direct side effects.

## What This Milestone Cannot Prove

It cannot prove adapter readiness, EgoOperator runtime efficacy, stable user benefit, live autonomy, production integration safety, consciousness, or subjective experience.
