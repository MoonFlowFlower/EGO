# EgoOperator Functional Subject Memory Forget Write-Proposal Gate

## Goal

Keep memory revoke/forget operations inside the memory gate by blocking file-write proposals that try to rewrite `MEMORY.md` or operator memory files as a substitute for `/memory_review` and `/forget <memory_id>`.

## Source

- `/tmp/ego_fs_010_after_fs042_20260523_113005/functional_subject_trial_report.json`
- `fs_16_forget_request` generated a `propose_file_write` pending approval to overwrite `artifacts/experience_trial/functional_subject_memory/MEMORY.md`.

## Scope

Allowed changes:

- `EgoOperator/agent_base.py`
- `EgoOperator/tests/test_operator_runtime_contract.py`
- `Tasks/TASK_BOARD.yaml`
- this task directory

Forbidden changes:

- direct memory deletion without explicit memory id/operator command
- memory authority promotion
- broad file-write policy change unrelated to memory forget/revoke
- provider/model policy changes
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- `legacy/ego-pre-handmade-mainline/**`
- GitHub Project mutation

## Acceptance Gate

- A memory forget/revoke prompt cannot produce a pending `write_file` proposal against `MEMORY.md` or operator memory files.
- The same turn finalizes with candidate-local memory scope, `/memory_review`, `/forget <memory_id>` or archive/no-op path, and no external side effect.
- Read-only inspection may remain allowed, but file mutation must go through memory commands/gate rather than `propose_file_write`.
- Existing file proposal, memory save, memory forget, and provider contextual recoveries do not regress.

## Rollback

Revert memory-forget file-write proposal block and keep EGO-FS-010 judge-partial on `fs_16` memory gate language.

## Claim Ceiling

`Functional Subject memory forget write-proposal gate local candidate pass`
