# PSPC Fixture-Only Shadow Trace v0 Stage Card

- lane: `fixture-only / audit-only`
- runtime authority: `none`
- EgoOperator runtime integration: `forbidden`
- adapter registration: `forbidden`
- gate invocation: `forbidden`
- memory write: `forbidden`
- user-visible output: `forbidden`
- claim ceiling: `lab_only_proto_self_mechanism_candidate / fixture_shadow_trace_only`
- next allowed step: `read_only_shadow_hook_stage_card_only`

## Problem Reframe

The current question is not whether PSPC should be connected to EgoOperator. The question is whether a fixture operator context plus the current PSPC `audit_candidate` can be represented as a non-executable shadow trace record without touching runtime, gate, memory, approval, transport, or user response surfaces.

## One Hypothesis

If PSPC stays as audit-only data, then a synthetic fixture operator context can be combined with the current PSPC `audit_candidate` into a shadow trace artifact whose baseline comparison shows no user response change, memory diff, gate diff, runtime output diff, adapter registration, or runtime side effect.

## One Change Surface

Allowed:

- `scripts/run_pspc_fixture_shadow_trace.py`
- `tests/test_pspc_fixture_shadow_trace.py`
- `docs/codex/tasks/pspc-fixture-shadow-trace-v0/`
- `artifacts/pspc_fixture_shadow_trace_v0/`
- necessary governance, ledger, and generated-view entries

Forbidden:

- EgoOperator runtime, gate, memory, approval, human-trial harness, transport, proactive channel, registry, or main loop changes
- adapter enablement
- adapter registration
- real runtime hook
- direct action
- direct user message
- direct memory write
- runtime gate bypass
- PSPC planner/model/training execution
- claim ceiling increase

## Authority Source

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `docs/codex/tasks/pspc-static-compatibility-review-v0/STATUS.md`
- `artifacts/pspc_static_compatibility_review_v0/static_compatibility_review.json`
- `artifacts/pspc_adapter_dry_run_v0/dry_run_result.json`

## Three-Level Verify

- Contract: fixture context is not a runtime context; shadow trace has no executable fields.
- Static: EgoOperator runtime sources still do not import or register `PSPCLabAdapter`.
- Artifact: `artifacts/pspc_fixture_shadow_trace_v0/shadow_trace.json` records no response, memory, gate, runtime, or proactive side effects.

## Rollback Plan

Delete `scripts/run_pspc_fixture_shadow_trace.py`, `tests/test_pspc_fixture_shadow_trace.py`, `docs/codex/tasks/pspc-fixture-shadow-trace-v0/`, `artifacts/pspc_fixture_shadow_trace_v0/`, and matching governance/ledger/generated-view entries.

## What This Proves

This proves a fixture operator context and the current PSPC audit candidate can be written as a shadow trace artifact without runtime connection, adapter registration, gate invocation, memory write, direct action, direct user message, proactive trigger, or runtime output difference.

## What This Does Not Prove

It does not prove real EgoOperator trace compatibility, runtime hook safety, runtime integration safety, adapter readiness for production, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.
