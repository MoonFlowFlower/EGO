# PSPC Disabled Shadow Hook v0 Stage Card

- lane: `disabled-shadow-hook-only`
- runtime authority: `none`
- hook state: `implemented but disabled`
- runtime registration: `forbidden`
- EgoOperator mainline mutation: `forbidden`
- gate invocation: `forbidden`
- memory write: `forbidden`
- user-visible output: `forbidden`
- claim ceiling: `lab_only_proto_self_mechanism_candidate / disabled_shadow_hook_only`
- next allowed step: `recorded_run_shadow_observation_stage_card_or_task_only`

## Problem Reframe

The goal is not to connect PSPC to EgoOperator. The goal is to prove a disabled read-only hook object can render PSPC audit data as shadow audit data without runtime registration, gate invocation, memory write, proposal/plan/approval mutation, user-response mutation, transport, or proactive behavior.

## One Hypothesis

If the hook remains disabled, mainline-disconnected, read-only, non-executable, and unregistered, then it can exist inside the repo as a testable artifact renderer without changing EgoOperator runtime behavior.

## One Change Surface

Allowed:

- `EgoOperator/adapters/pspc_read_only_shadow_hook.py`
- `scripts/run_pspc_disabled_shadow_hook_review.py`
- `tests/test_pspc_disabled_shadow_hook.py`
- `docs/codex/tasks/pspc-disabled-shadow-hook-v0/`
- `artifacts/pspc_disabled_shadow_hook_v0/`
- necessary governance, ledger, and generated-view entries

Forbidden:

- runtime registry
- EgoOperator main loop
- gate
- memory
- approval flow
- human-trial harness
- transport
- proactive channel
- adapter enablement
- user-visible PSPC influence
- PSPC planner/model/training execution
- claim ceiling increase

## Authority Source

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `docs/codex/tasks/pspc-read-only-shadow-hook-stage-card-v0/STATUS.md`
- `artifacts/pspc_fixture_shadow_trace_v0/shadow_trace.json`
- `EgoOperator/docs/ALGORITHM_INVENTORY.md`

## Three-Level Verify

- Contract: hook defaults are disabled, mainline-disconnected, `runtime_authority=none`, and side effects are disallowed.
- Static: EgoOperator runtime sources do not import or register `PSPCReadOnlyShadowHook`.
- Artifact: `artifacts/pspc_disabled_shadow_hook_v0/disabled_shadow_hook_result.json` records no side effects and no executable output.

## Rollback Plan

Delete `EgoOperator/adapters/pspc_read_only_shadow_hook.py`, `scripts/run_pspc_disabled_shadow_hook_review.py`, `tests/test_pspc_disabled_shadow_hook.py`, this task directory, `artifacts/pspc_disabled_shadow_hook_v0/`, and matching governance/ledger/generated-view entries.

## What This Proves

This proves a disabled PSPC read-only shadow hook can render audit-only data from fixture shadow trace data while remaining default-off, mainline-disconnected, non-executable, unregistered by runtime, and side-effect-free.

## What This Does Not Prove

It does not prove runtime registration safety, live runtime hook safety, real EgoOperator trace compatibility, adapter readiness for production, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.
