# PSPC Static Compatibility Review v0 Stage Card

## Frozen Boundary

- lane: `adapter_static_compatibility_only`
- runtime authority: `none`
- runtime registration: `forbidden`
- runtime integration: `forbidden`
- runtime gate invocation: `forbidden`
- memory write: `forbidden`
- direct action: `forbidden`
- direct user message: `forbidden`
- proposal execution: `forbidden`
- trace mutation: `forbidden`
- `mainline_connected`: `false`
- `enabled`: `false`
- claim ceiling: `lab_only_proto_self_mechanism_candidate / static_compatibility_only`

## Problem Reframe

This step does not move PSPC closer to runtime execution. It checks whether the current `audit_candidate` can be classified as audit-only data without being confused with EgoOperator action, runtime proposal, memory write, gate decision, user message, or trace mutation.

## One Hypothesis

If field classification is explicit, negative packet cases are rejected, and EgoOperator runtime sources still do not import or register `PSPCLabAdapter`, then PSPC can proceed to a future fixture-only shadow trace task without becoming an action source.

## Allowed Surface

- `docs/codex/tasks/pspc-static-compatibility-review-v0/`
- `scripts/run_pspc_static_compatibility_review.py`
- `tests/test_pspc_static_compatibility_review.py`
- `artifacts/pspc_static_compatibility_review_v0/`
- necessary governance state, ledger, and generated views

## Forbidden Surface

- `EgoOperator/` runtime files
- runtime registry
- gates
- memory
- approval flow
- human-trial harness
- transport
- proactive channels
- fixture shadow trace implementation

## What This Proves

This proves the current PSPC `audit_candidate` is statically compatible with EgoOperator proposal/gate/trace boundaries as audit-only data: it has no executable action fields, its proposal candidate is only an audit hint, unsafe authority flags are rejected, and EgoOperator runtime sources do not import or register the adapter.

## What This Does Not Prove

It does not prove fixture shadow trace behavior, runtime integration safety, adapter readiness for production, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure means PSPC audit data is not safe to advance toward fixture-only shadow trace. Keep PSPC at adapter_dry_run_only or adapter_skeleton_only until field classification, negative validation, or runtime-source drift is repaired.

## Rollback

Delete `scripts/run_pspc_static_compatibility_review.py`, `tests/test_pspc_static_compatibility_review.py`, this task directory, `artifacts/pspc_static_compatibility_review_v0/`, and matching governance/ledger/generated-view entries.

