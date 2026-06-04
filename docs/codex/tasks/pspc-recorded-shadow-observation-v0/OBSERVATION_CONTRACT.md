# PSPC Recorded-Run Shadow Observation v0 Contract

Claim ceiling: `lab_only_proto_self_mechanism_candidate / recorded_shadow_observation_only`

## Inputs

- Recorded EgoOperator report: `EgoOperator/artifacts/human_operator_trial/v2_latest/human_operator_trial_report.json`
- Disabled PSPC shadow hook: `EgoOperator/adapters/pspc_read_only_shadow_hook.py`
- PSPC audit candidate source: fixture shadow trace artifact

## Output

The runner may write only:

- `artifacts/pspc_recorded_shadow_observation_v0/recorded_shadow_observation.json`
- `artifacts/pspc_recorded_shadow_observation_v0/RECORDED_SHADOW_OBSERVATION_REPORT.md`

## Required Invariants

- `recorded_case_count=18`
- `hook_enabled=false`
- `mainline_connected=false`
- `runtime_registered=false`
- `all_user_responses_unchanged=true`
- `memory_diff=false`
- `approval_gate_diff=false`
- `runtime_output_diff=false`
- `pspc_shadow_artifact_only=true`

## Forbidden Surfaces

- live runtime execution
- runtime registration
- runtime gate invocation
- memory write
- approval mutation
- plan mutation
- proposal mutation
- user response mutation
- transport send
- proactive trigger
- PSPC planner/model/training execution

## What This Proves

This proves PSPC shadow observation can be added beside recorded EgoOperator cases without changing recorded output hashes or recorded gate/memory/runtime comparison flags.

## What This Does Not Prove

It does not prove live hook safety, real-time integration safety, adapter readiness, EgoOperator runtime efficacy, stable real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Rollback

Delete this task directory, artifacts, runner, tests, and matching governance/ledger/generated-view entries.
