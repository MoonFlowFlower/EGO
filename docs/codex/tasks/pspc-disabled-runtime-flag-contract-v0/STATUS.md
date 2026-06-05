# PSPC Disabled Runtime Flag Contract v0

- status: `accepted`
- task_board_id: `PSPC-SHADOW-HOOK-005`
- claim_ceiling: `lab_only_proto_self_mechanism_candidate / disabled_runtime_flag_contract_only`
- flag_name: `PSPC_SHADOW_OBSERVATION_LOCAL`
- default_value: `false`
- admitted_runtime_value_when_requested_true: `false`
- enabled: `false`
- mainline_connected: `false`
- runtime_authority: `none`

## Scope

This task defines and verifies a local PSPC shadow flag contract without installing that flag into EgoOperator runtime. The contract is represented by an isolated runner and tests. It is not imported, registered, or branched on by active EgoOperator runtime files.

## Evidence

- runner: `scripts/run_pspc_disabled_runtime_flag_contract.py`
- tests: `tests/test_pspc_disabled_runtime_flag_contract.py`
- result JSON: `artifacts/pspc_disabled_runtime_flag_contract_v0/disabled_runtime_flag_contract.json`
- report: `artifacts/pspc_disabled_runtime_flag_contract_v0/DISABLED_RUNTIME_FLAG_CONTRACT_REPORT.md`

## Result

- default flag value: `false`
- requested true value admitted to runtime: `false`
- requested true value artifact output: `true`
- active runtime scan offenders: `0`
- side effects: `none`
- next allowed step: `local_manual_shadow_session_harness_only`

## What This Proves

The local PSPC shadow flag contract is default-false and admits no runtime value. Even when a requested true value is represented, it can only produce artifact-only shadow data and cannot register runtime, alter user responses, mutate proposals or plans, write memory, invoke gate or approval, call transport, trigger proactive behavior, call planner/training/model execution, or raise the claim ceiling.

## What This Does Not Prove

This does not prove a runtime flag is installed, local manual shadow sessions are safe, proposal hinting is safe, runtime integration safety, adapter readiness, EgoOperator PSPC capability, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure would mean PSPC must remain disabled shadow-only and cannot proceed to a local manual shadow session harness until the flag contract is default-false, artifact-only, non-executable, and side-effect-free.

## Rollback

Delete `scripts/run_pspc_disabled_runtime_flag_contract.py`, `tests/test_pspc_disabled_runtime_flag_contract.py`, `docs/codex/tasks/pspc-disabled-runtime-flag-contract-v0/`, `artifacts/pspc_disabled_runtime_flag_contract_v0/`, and matching task-board/program-state/evidence-ledger/generated-view entries.

## Next Allowed Step

Only `PSPC-SHADOW-HOOK-006` local manual shadow session harness may proceed next. PSPC remains disabled, mainline-disconnected, audit-only, and side-effect-free.
