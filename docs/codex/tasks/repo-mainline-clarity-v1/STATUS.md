# Repo Mainline Clarity v1 Status

## Current Milestone

`phase2a_archive_reconciliation`

## Status

`verify_passed`

## Current Slice

This slice reconciles the already half-applied archive migration for two superseded docs and historical cleanup bundles `P0` through `P7`.

## Does Not Change

- No runtime behavior.
- No new archive class beyond the already admitted / half-applied moved slice.
- No split-repo migration.
- No `PROGRAM_STATE_UNIFIED.yaml` update.
- No formal evidence ledger update.

## Completion Criteria

- `README.md` points new agents to `docs/MAINLINE_QUICKSTART.md`. Passed.
- `docs/REPO_SURFACE_MAP.md` is generated and verified. Passed.
- `verify_mainline_clarity.py` passes. Passed.
- `verify_route_convergence.py` still proves exactly one active default lane. Passed.
- `verify_repo.py --mode fast` includes the mainline clarity gate. Passed.
- Archived docs and `P0` through `P7` cleanup bundles remain findable through `docs/archive/ARCHIVE_INDEX.yaml`.
- `verify_archive_reconciliation.py` passes and is included in `verify_repo.py --mode fast`.
- Current authority paths and the active default lane remain unchanged.

## Verification

- `python3 scripts/codex/generate_route_convergence_views.py` passed.
- `python3 scripts/codex/verify_route_convergence.py` passed with exactly one active default lane.
- `python3 scripts/codex/verify_mainline_clarity.py` passed.
- `python3 scripts/codex/check_program_state_integrity.py --skip-diff-check` passed.
- `python3 -m py_compile ego_desktop_lab/*.py` passed.
- `TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests -q` passed with `189 passed`.
- `python3 scripts/codex/verify_repo.py --mode fast` passed; OpenEmotion live health smoke was skipped because the local health endpoint was unavailable.
- Scoped whitespace check for this change surface passed.

## Phase 2A Verification Target

- `python3 -m py_compile scripts/codex/verify_archive_reconciliation.py scripts/codex/verify_repo.py` passed.
- `python3 scripts/codex/verify_archive_reconciliation.py` passed with `2` moved docs and `8` moved artifact dirs.
- `python3 scripts/codex/generate_program_state_views.py` passed.
- `python3 scripts/codex/check_program_state_integrity.py --skip-diff-check` passed.
- `python3 scripts/codex/verify_route_convergence.py` passed with exactly one active default lane.
- `python3 scripts/codex/verify_mainline_clarity.py` passed.
- `python3 scripts/codex/verify_repo.py --mode fast` passed with the archive reconciliation gate included.
- Scoped whitespace check for the archive reconciliation surface passed.

## Known Limitation

The broad cleanup command `git diff --check -- docs EgoCore OpenEmotion ego_desktop_lab artifacts scripts` is still blocked by pre-existing unrelated runtime artifacts and logs with whitespace issues. This task does not clean or stage those files.

## Claim Ceiling

Repo readability and route discipline only. This does not prove runtime efficacy, live autonomy, consciousness, alive status, or user benefit.
