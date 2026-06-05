# PSPC Default-Off Runtime Shadow Hook v0

- task_id: `PSPC-SHADOW-HOOK-002`
- status: `accepted`
- lane: `pspc_runtime_adjacent_shadow`
- claim_ceiling: `lab_only_proto_self_mechanism_candidate / default_off_hook_module_only`
- runtime_authority: `none`
- enabled: `false`
- mainline_connected: `false`

## Result

The default-off PSPC runtime shadow hook module now exists at `EgoOperator/adapters/pspc_disabled_runtime_shadow_hook.py`.

It exposes only:

- `assert_no_runtime_authority()`
- `validate_shadow_context()`
- `render_shadow_artifact()`

## Acceptance Evidence

- disabled defaults: `pass`
- `mainline_connected=false`: `pass`
- `runtime_authority=none`: `pass`
- audit-only/read-only/non-executable output: `pass`
- runtime-authority fields rejected: `pass`
- side effects all false: `pass`
- active EgoOperator runtime import/registry reference absent: `pass`
- targeted tests: `7 passed`

## Artifact

- `artifacts/pspc_disabled_runtime_shadow_hook_v0/default_off_hook_result.json`
- `artifacts/pspc_disabled_runtime_shadow_hook_v0/DEFAULT_OFF_HOOK_REPORT.md`

## What This Proves

This proves a default-off PSPC runtime shadow hook module can validate a shadow context and render audit-only, read-only, non-executable artifact data while remaining unregistered, disabled, mainline-disconnected, and free of runtime authority.

## What This Does Not Prove

This does not prove hook registration safety, runtime integration safety, adapter readiness, EgoOperator PSPC capability, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure would mean PSPC must remain at Stage Card-only hook evidence until disabled defaults, validation, non-executable output, or runtime import isolation is repaired.

## Rollback

Delete:

- `EgoOperator/adapters/pspc_disabled_runtime_shadow_hook.py`
- `scripts/run_pspc_disabled_runtime_shadow_hook.py`
- `tests/test_pspc_disabled_runtime_shadow_hook.py`
- `docs/codex/tasks/pspc-disabled-runtime-shadow-hook-v0/`
- `artifacts/pspc_disabled_runtime_shadow_hook_v0/`
- matching task-board, governance, ledger, and generated-view entries

## Next Allowed Step

Only `PSPC-SHADOW-HOOK-003` runtime snapshot no-diff with hook present is allowed. The hook remains unregistered and disabled.
