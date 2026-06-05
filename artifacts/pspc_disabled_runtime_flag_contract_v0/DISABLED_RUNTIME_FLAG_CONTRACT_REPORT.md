# PSPC Disabled Runtime Flag Contract v0

- status: `pass`
- claim_ceiling: `lab_only_proto_self_mechanism_candidate / disabled_runtime_flag_contract_only`
- flag_name: `PSPC_SHADOW_OBSERVATION_LOCAL`
- default_value: `False`
- admitted_runtime_value_when_requested_true: `False`
- next_allowed_step: `local_manual_shadow_session_harness_only`

## Checks

- `active_runtime_scan_clean`: `True`
- `default_contract_valid`: `True`
- `default_flag_false`: `True`
- `enabled_false`: `True`
- `flag_true_admits_runtime_false`: `True`
- `flag_true_artifact_only`: `True`
- `flag_true_contract_valid`: `True`
- `mainline_connected_false`: `True`
- `runtime_authority_none`: `True`
- `shadow_observation_non_executable`: `True`
- `side_effects_absent`: `True`

## What This Proves

This proves the local PSPC shadow flag contract is default-false, admits no runtime value, and can represent a requested true value only as artifact-only shadow data without runtime registration, user response mutation, proposal/plan mutation, memory write, gate or approval invocation, transport call, proactive trigger, planner call, training call, model execution, or claim-ceiling upgrade.

## What This Does Not Prove

It does not prove a runtime flag is installed, local manual shadow sessions are safe, proposal hinting is safe, runtime integration safety, adapter readiness, EgoOperator PSPC capability, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure means PSPC must remain disabled shadow-only and cannot proceed to a local manual shadow session harness until the flag contract is default-false, artifact-only, non-executable, and side-effect-free.

## Rollback

Delete `scripts/run_pspc_disabled_runtime_flag_contract.py`, `tests/test_pspc_disabled_runtime_flag_contract.py`, `docs/codex/tasks/pspc-disabled-runtime-flag-contract-v0/`, `artifacts/pspc_disabled_runtime_flag_contract_v0/`, and matching task-board/program-state/evidence-ledger/generated-view entries.
