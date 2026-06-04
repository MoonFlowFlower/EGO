# PSPC Runtime-Adjacent Smoke v0

- status: `pass`
- claim_ceiling: `lab_only_proto_self_mechanism_candidate / deterministic_runtime_adjacent_smoke_only`
- case_count: `3`
- next_allowed_step: `runtime_hook_go_no_go_only`

## Checks

- `pspc_disabled`: `True`
- `pspc_mainline_disconnected`: `True`
- `pspc_output_audit_only`: `True`
- `pspc_output_non_executable`: `True`
- `runtime_behavior_unchanged`: `True`
- `runtime_import_or_registry_absent`: `True`
- `side_effects_absent`: `True`
- `uses_no_live_user_channel`: `True`

## What This Proves

This proves deterministic or recorded PSPC shadow data can be checked around the runtime-adjacent observer boundary while runtime behavior snapshots remain unchanged, PSPC output stays audit-only and non-executable, and no live user channel, memory write, gate invocation, approval change, direct action, user message, transport call, proactive trigger, planner call, training call, or model execution occurs.

## What This Does Not Prove

It does not prove live runtime hook safety, real-time integration safety, adapter readiness for production, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure means PSPC must remain at recorded_trace_replay_no_diff_only until deterministic smoke preserves runtime behavior snapshots and side-effect invariants.

## Rollback

Delete `scripts/run_pspc_runtime_adjacent_smoke.py`, `tests/test_pspc_runtime_adjacent_smoke.py`, `docs/codex/tasks/pspc-runtime-adjacent-smoke-v0/`, `artifacts/pspc_runtime_adjacent_smoke_v0/`, and matching governance/ledger/generated-view entries.
