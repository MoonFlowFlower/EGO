# PSPC Read-Only Shadow Hook Stage Card v0

- lane: `stage-card-only / shadow-audit-only`
- runtime authority: `none`
- hook implementation: `forbidden in this stage`
- hook default state: `disabled`
- EgoOperator runtime modification: `forbidden`
- adapter registration: `forbidden`
- gate invocation: `forbidden`
- memory write: `forbidden`
- user-visible output: `forbidden`
- claim ceiling: `lab_only_proto_self_mechanism_candidate / shadow_hook_stage_card_only`
- next allowed step: `disabled_shadow_hook_implementation_stage_card_or_task_only`

## Problem Reframe

The current risk is not whether PSPC evidence can be represented. That has already been shown at fixture-shadow level. The current risk is that a future shadow hook could be treated as a runtime integration path and accidentally gain proposal, gate, memory, approval, transport, or user-output authority.

This stage only defines the future hook boundary. It does not implement a hook.

## One Hypothesis

If the future PSPC shadow hook contract is frozen before implementation, then any later implementation can be checked against a narrow boundary: disabled by default, shadow/audit mode only, no runtime authority, no mutation of proposal, plan, approval, user response, memory, gate decision, transport, or claim ceiling.

## One Change Surface

Allowed:

- `docs/codex/tasks/pspc-read-only-shadow-hook-stage-card-v0/`
- `artifacts/pspc_read_only_shadow_hook_stage_card_v0/`
- necessary governance, ledger, and generated-view entries

Forbidden:

- `EgoOperator/` runtime files
- runtime registry
- gate
- memory
- approval flow
- human-trial harness
- transport
- proactive channel
- adapter enablement
- adapter registration
- real hook implementation
- user-visible PSPC influence
- PSPC planner/model/training execution
- claim ceiling increase

## Authority Source

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `docs/codex/tasks/pspc-fixture-shadow-trace-v0/STATUS.md`
- `artifacts/pspc_fixture_shadow_trace_v0/shadow_trace.json`
- `docs/codex/tasks/pspc-static-compatibility-review-v0/STATUS.md`

## Required Future Hook Boundary

A future hook, if separately approved, must be:

- default disabled
- shadow/audit mode only
- read-only
- artifact-producing only
- non-blocking
- non-executable
- not registered unless a later explicit stage authorizes registration

It must not:

- change EgoOperator proposal
- change EgoOperator plan
- change approval state
- change gate decision
- change user response
- write memory
- trigger transport
- trigger proactive behavior
- call PSPC planner/model/training
- raise claim ceiling

## Three-Level Verify

- Contract: docs freeze default-off, audit-only, non-mutating hook boundary.
- Static: no EgoOperator runtime file is modified and no `PSPCLabAdapter` runtime import/registry reference exists.
- Evidence: stage-card review artifact records this stage as `shadow_hook_stage_card_only`, not implementation.

## Rollback Plan

Delete this task directory, `artifacts/pspc_read_only_shadow_hook_stage_card_v0/`, and matching governance/ledger/generated-view entries.

## What This Proves

This proves the repo has a bounded design contract for a future read-only PSPC shadow hook and pre-registers that such a hook must be disabled, shadow/audit-only, and non-mutating.

## What This Does Not Prove

It does not prove a hook exists, a hook is safe, runtime integration is safe, adapter readiness, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.
