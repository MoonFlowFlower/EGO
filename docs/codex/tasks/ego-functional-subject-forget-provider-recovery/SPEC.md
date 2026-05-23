# EgoOperator Functional Subject Forget/Revoke Provider Recovery

## Goal

When a memory forget/revoke turn hits provider failure, preserve the memory-gate semantics by returning the auditable candidate-local revoke/no-op path instead of a generic provider-error reply.

## Source

- `/tmp/ego_fs_010_after_fs040_20260523_104348/functional_subject_trial_report.json`
- GPT-5.5 judge partial after EGO-FS-040.
- `fs_16_forget_request`: prompt asked how to forget or revoke an incorrect preference, but provider timeout surfaced as generic provider failure.

## Scope

Allowed changes:

- `EgoOperator/agent_base.py`
- `EgoOperator/tests/test_operator_runtime_contract.py`
- `Tasks/TASK_BOARD.yaml`
- this task directory

Forbidden changes:

- direct memory deletion without explicit ID/operator command
- memory authority promotion
- provider retry/fallback policy changes
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- `legacy/ego-pre-handmade-mainline/**`
- GitHub Project mutation

## Acceptance Gate

- A provider error during a memory forget/revoke request returns a scoped memory gate checkpoint.
- The reply includes candidate-local/operator memory scope, `/memory_review`, `/forget <memory_id>` or archive/no-op path, and states PROJECT_MEMORY/program state/evidence ledger are not changed.
- Existing memory-forget rewrite/fallback tests and other provider contextual recoveries do not regress.
- Existing EgoOperator and Autopilot regression profiles pass.

## Rollback

Revert forget/revoke provider-error contextual recovery and keep EGO-FS-010 blocked on `fs_16`.

## Claim Ceiling

`Functional Subject forget/revoke provider-error recovery local candidate pass`
