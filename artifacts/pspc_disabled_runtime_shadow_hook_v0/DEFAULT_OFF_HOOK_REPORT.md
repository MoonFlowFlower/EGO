# PSPC Default-Off Runtime Shadow Hook v0

- status: `pass`
- claim_ceiling: `lab_only_proto_self_mechanism_candidate / default_off_hook_module_only`
- next_allowed_step: `runtime_snapshot_no_diff_with_hook_present_only`

## Checks

- `audit_only`: `True`
- `hook_disabled`: `True`
- `hook_mainline_disconnected`: `True`
- `hook_runtime_authority_none`: `True`
- `non_executable`: `True`
- `read_only`: `True`
- `runtime_import_or_registry_absent`: `True`
- `side_effects_absent`: `True`

## What This Proves

This proves a default-off PSPC runtime shadow hook module can validate a shadow context and render audit-only, read-only, non-executable artifact data while remaining unregistered, disabled, mainline-disconnected, and free of runtime authority.

## What This Does Not Prove

It does not prove hook registration safety, runtime integration safety, adapter readiness, EgoOperator PSPC capability, EgoOperator runtime efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, or subjective experience.

## Failure Meaning

Failure means PSPC must remain at Stage Card-only hook evidence until disabled defaults, validation, non-executable output, or runtime import isolation is repaired.

## Rollback

Delete `EgoOperator/adapters/pspc_disabled_runtime_shadow_hook.py`, `scripts/run_pspc_disabled_runtime_shadow_hook.py`, `tests/test_pspc_disabled_runtime_shadow_hook.py`, `docs/codex/tasks/pspc-disabled-runtime-shadow-hook-v0/`, `artifacts/pspc_disabled_runtime_shadow_hook_v0/`, and matching governance/ledger/generated-view entries.
