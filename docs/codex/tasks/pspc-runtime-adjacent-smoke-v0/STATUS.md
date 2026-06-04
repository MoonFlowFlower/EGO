# PSPC Runtime-Adjacent Smoke v0

- task_id: `PSPC-SHADOW-005`
- status: `accepted`
- lane: `pspc_runtime_adjacent_shadow`
- claim_ceiling: `lab_only_proto_self_mechanism_candidate / deterministic_runtime_adjacent_smoke_only`
- runtime_authority: `none`
- enabled: `false`
- mainline_connected: `false`

## Result

Deterministic/no-live-user smoke now runs at `scripts/run_pspc_runtime_adjacent_smoke.py` and writes artifacts under `artifacts/pspc_runtime_adjacent_smoke_v0/`.

The smoke uses only prior PSPC observer/replay artifacts:

- `artifacts/pspc_runtime_adjacent_observer_v0/runtime_adjacent_observer.json`
- `artifacts/pspc_recorded_trace_replay_no_diff_v0/recorded_trace_replay_no_diff.json`

## Acceptance Evidence

- deterministic or recorded inputs only: `pass`
- live user channel absent: `pass`
- runtime behavior snapshot unchanged with and without PSPC shadow data: `pass`
- PSPC output remains audit-only and non-executable: `pass`
- `enabled=false`: `pass`
- `mainline_connected=false`: `pass`
- runtime import/registry reference absent in EgoOperator runtime sources: `pass`
- memory write, gate invocation, approval change, direct action, user message, transport call, proactive trigger, planner call, training call, and model execution absent: `pass`

## What This Proves

This proves deterministic or recorded PSPC shadow data can be checked around the runtime-adjacent observer boundary while runtime behavior snapshots remain unchanged, PSPC output stays audit-only and non-executable, and no live user channel or runtime side effect is introduced.

## What This Does Not Prove

This does not prove live runtime hook safety, real-time integration safety, adapter readiness for production, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure would mean PSPC must remain at `recorded_trace_replay_no_diff_only` until deterministic smoke preserves runtime behavior snapshots and side-effect invariants.

## Rollback

Delete:

- `scripts/run_pspc_runtime_adjacent_smoke.py`
- `tests/test_pspc_runtime_adjacent_smoke.py`
- `docs/codex/tasks/pspc-runtime-adjacent-smoke-v0/`
- `artifacts/pspc_runtime_adjacent_smoke_v0/`
- matching governance, ledger, generated-view, and task-board updates

## Next Allowed Step

Only `PSPC-SHADOW-006` go/no-go review for a future separate disabled runtime hook insertion stage is allowed. This task does not implement, register, enable, import, or connect PSPC to EgoOperator runtime.
