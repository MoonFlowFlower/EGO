# PSPC Adapter Dry-Run Harness v0 Stage Card

## Frozen Boundary

- lane: `adapter-dry-run-only`
- runtime authority: `none`
- runtime registration: `forbidden`
- EgoOperator runtime integration: `forbidden`
- runtime gate invocation: `forbidden`
- memory write: `forbidden`
- direct action: `forbidden`
- direct user message: `forbidden`
- proactive trigger: `forbidden`
- PSPC planner/model/training execution: `forbidden`
- `mainline_connected`: `false`
- `enabled`: `false`
- claim ceiling: `lab_only_proto_self_mechanism_candidate / adapter_dry_run_only`

## Problem Reframe

This is not a PSPC integration task. It is a safety-contact-chain task: prove that a PSPC lab evidence packet can pass through the disabled read-only adapter into artifact-only audit data without touching EgoOperator runtime authority.

## One Hypothesis

If an isolated harness builds a canonical packet from stable PSPC artifacts, validates it with `PSPCLabAdapter`, converts it into an audit candidate, and writes only artifact output, then the repo can demonstrate adapter packet handling without runtime side effects.

## One Change Surface

Allowed:

- `docs/codex/tasks/pspc-adapter-dry-run-v0/`
- `tests/test_pspc_adapter_dry_run.py`
- `scripts/run_pspc_adapter_dry_run.py`
- `artifacts/pspc_adapter_dry_run_v0/`
- necessary state, ledger, and generated views

Forbidden:

- `EgoOperator/agent_base.py`
- EgoOperator runtime registry
- gates
- memory
- approval flow
- human-trial harness
- transport
- proactive channels
- PSPC planner, training, or model execution

## What This Proves

This stage proves a PSPC lab evidence packet can pass through the disabled read-only adapter as audit-only data in an isolated dry-run without runtime registration, memory write, direct action, direct user message, gate invocation, proactive trigger, or planner/model execution.

## What This Does Not Prove

It does not prove runtime integration safety, adapter readiness for production, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Verification

- `python -m pytest -q tests\test_pspc_adapter_dry_run.py`
- `python scripts\run_pspc_adapter_dry_run.py --out artifacts\pspc_adapter_dry_run_v0`
- static check that runtime sources do not import or register `PSPCLabAdapter`
- static check that no EgoOperator runtime/gate/memory/approval/transport files changed

## Failure Meaning

Failure means the adapter packet boundary is not safe enough for artifact-only dry-run use, or the dry-run attempted runtime authority or side effects. Keep PSPC at adapter_skeleton_only until repaired.

## Rollback

Delete `scripts/run_pspc_adapter_dry_run.py`, `tests/test_pspc_adapter_dry_run.py`, `docs/codex/tasks/pspc-adapter-dry-run-v0/`, `artifacts/pspc_adapter_dry_run_v0/`, and matching governance/ledger/generated-view entries. Keep skeleton v0 unless its contract tests fail.

## Claim Ceiling

`lab_only_proto_self_mechanism_candidate / adapter_dry_run_only`

