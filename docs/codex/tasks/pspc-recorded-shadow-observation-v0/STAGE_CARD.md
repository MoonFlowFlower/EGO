# PSPC Recorded-Run Shadow Observation v0 Stage Card

- lane: `recorded-run / shadow-audit-only`
- runtime authority: `none`
- live runtime execution: `forbidden`
- runtime registration: `forbidden`
- hook enablement: `forbidden`
- gate invocation: `forbidden`
- memory write: `forbidden`
- user-visible output mutation: `forbidden`
- claim ceiling: `lab_only_proto_self_mechanism_candidate / recorded_shadow_observation_only`
- next allowed step: `read_only_runtime_adjacent_shadow_review_stage_card_only`

## Problem Reframe

The goal is not to prove PSPC can run in EgoOperator live runtime. The goal is to prove that, on recorded EgoOperator human-operator trial cases, the disabled PSPC shadow hook can add artifact-only shadow observations while preserving recorded user-visible outputs and recording no memory, approval/gate, or runtime-output differences.

## One Hypothesis

If the hook is truly audit-only, then applying it beside recorded EgoOperator inputs will add only shadow observation artifacts. Baseline response hashes must remain identical.

## One Change Surface

Allowed:

- `scripts/run_pspc_recorded_shadow_observation.py`
- `tests/test_pspc_recorded_shadow_observation.py`
- `docs/codex/tasks/pspc-recorded-shadow-observation-v0/`
- `artifacts/pspc_recorded_shadow_observation_v0/`
- necessary governance, ledger, and generated-view entries

Forbidden:

- EgoOperator runtime registry
- EgoOperator main loop
- gate
- memory
- approval flow
- human-trial harness
- transport
- proactive channel
- hook enablement
- user-visible PSPC influence
- live runtime execution
- PSPC planner/model/training execution
- claim ceiling increase

## Authority Source

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `docs/codex/tasks/pspc-disabled-shadow-hook-v0/STATUS.md`
- `EgoOperator/artifacts/human_operator_trial/v2_latest/human_operator_trial_report.json`
- `artifacts/pspc_disabled_shadow_hook_v0/disabled_shadow_hook_result.json`

## Three-Level Verify

- Contract: recorded cases are loaded read-only and marked `runtime_connected=false`.
- Static: runtime sources do not import or register `PSPCReadOnlyShadowHook`.
- Artifact: `recorded_shadow_observation.json` records unchanged response hashes, no memory diff, no approval/gate diff, no runtime output diff, and PSPC shadow artifact-only status.

## Rollback Plan

Delete `scripts/run_pspc_recorded_shadow_observation.py`, `tests/test_pspc_recorded_shadow_observation.py`, this task directory, `artifacts/pspc_recorded_shadow_observation_v0/`, and matching governance/ledger/generated-view entries.

## What This Proves

This proves the disabled PSPC shadow hook can be applied beside recorded EgoOperator human-operator trial cases as artifact-only shadow observation data while preserving recorded user response hashes and recording no memory, approval/gate, runtime-output, runtime-registration, or user-visible side effects.

## What This Does Not Prove

It does not prove live runtime hook safety, real-time integration safety, adapter readiness for production, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.
