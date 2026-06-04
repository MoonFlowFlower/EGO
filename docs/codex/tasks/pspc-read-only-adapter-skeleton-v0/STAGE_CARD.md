# PSPC Read-Only Adapter Skeleton v0 Stage Card

## Frozen Boundary

- lane: `adapter-skeleton-only`
- runtime authority: `none`
- runtime registration: `forbidden`
- runtime integration: `forbidden`
- memory write: `forbidden`
- direct action: `forbidden`
- direct user message: `forbidden`
- runtime gate invocation: `forbidden`
- PSPC planner/model/training execution: `forbidden`
- proactive trigger: `forbidden`
- `mainline_connected`: `false`
- `enabled`: `false`
- claim ceiling: `lab_only_proto_self_mechanism_candidate / adapter_skeleton_only`

## Problem Reframe

The task is not to connect PSPC to EgoOperator. The task is to prove that a PSPC lab evidence packet can be represented inside the repo as read-only audit data while preserving no runtime authority.

The danger is adapter creep: a "read-only" adapter becoming a runtime import, registry entry, memory writer, action selector, gate bypass, or user-message source.

## One Hypothesis

If the adapter exposes only `validate_packet`, `to_audit_candidate`, and `assert_no_runtime_authority`, and static tests prove it is disabled, mainline-disconnected, unregistered, and side-effect free, then PSPC evidence can be safely read in repo space without changing EgoOperator runtime behavior.

## One Change Surface

Allowed:

- `EgoOperator/adapters/pspc_lab_adapter.py`
- `tests/test_pspc_lab_adapter_contract.py`
- `docs/codex/tasks/pspc-read-only-adapter-skeleton-v0/`
- `artifacts/pspc_adapter_skeleton_v0/`
- necessary governance state, evidence ledger, and generated views

Forbidden:

- `EgoOperator/agent_base.py`
- runtime registry
- gates
- memory
- approval flow
- human-trial harness
- transport
- proactive channels
- PSPC planner, training, or model execution

## Authority Source

This task is authorized by `docs/codex/tasks/pspc-read-only-adapter-implementation-v0/GO_NO_GO_REVIEW.md`, which returned `go_for_adapter_skeleton_stage_card_only`.

Repo-wide authority remains `docs/PROGRAM_STATE_UNIFIED.yaml`. This task does not change current phase, current layer, highest evidence level, or the current EgoOperator human-trial next action.

## What This Proves

This stage proves a disabled PSPC lab adapter skeleton can validate PSPC evidence packets and convert them into audit-only candidate data while static tests show no runtime registration, no runtime import, no direct action, no user message, no memory write, and no gate bypass path.

## What This Does Not Prove

It does not prove adapter readiness, runtime integration safety, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, production safety, consciousness, or subjective experience.

## Three-Level Verify

1. Contract tests: `python -m pytest -q tests\test_pspc_lab_adapter_contract.py`.
2. Static boundary checks: adapter is absent from EgoOperator runtime imports/registry and only `EgoOperator/adapters/pspc_lab_adapter.py` changes under `EgoOperator/`.
3. Governance checks: program state integrity, route convergence, mainline clarity, lint, diff check, and closeout gate.

## Rollback

Delete `EgoOperator/adapters/pspc_lab_adapter.py`, `tests/test_pspc_lab_adapter_contract.py`, `docs/codex/tasks/pspc-read-only-adapter-skeleton-v0/`, `artifacts/pspc_adapter_skeleton_v0/`, and matching governance/ledger/generated-view entries. No runtime rollback should be required because the adapter is not registered and does not write memory or emit user-visible output.

## Stop Conditions

Stop and roll back if:

- adapter is imported by runtime
- adapter is registered
- `enabled=true`
- `mainline_connected=true`
- adapter output can directly drive action
- adapter can write memory
- adapter can generate user messages
- adapter invokes gate or approval
- adapter calls PSPC planner/model/training
- claim ceiling is raised

## Claim Ceiling

`lab_only_proto_self_mechanism_candidate / adapter_skeleton_only`

