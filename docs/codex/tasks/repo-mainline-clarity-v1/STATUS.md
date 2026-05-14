# Repo Mainline Clarity v1 Status

## Current Milestone

`phase1_mainline_view`

## Status

`verify_passed`

## Current Slice

This task adds a mainline quickstart, generated surface map, and staged operational-exhaust verifier.

## Does Not Change

- No runtime behavior.
- No physical archive moves.
- No split-repo migration.
- No `PROGRAM_STATE_UNIFIED.yaml` update.
- No formal evidence ledger update.

## Completion Criteria

- `README.md` points new agents to `docs/MAINLINE_QUICKSTART.md`. Passed.
- `docs/REPO_SURFACE_MAP.md` is generated and verified. Passed.
- `verify_mainline_clarity.py` passes. Passed.
- `verify_route_convergence.py` still proves exactly one active default lane. Passed.
- `verify_repo.py --mode fast` includes the mainline clarity gate. Passed.

## Verification

- `python3 scripts/codex/generate_route_convergence_views.py` passed.
- `python3 scripts/codex/verify_route_convergence.py` passed with exactly one active default lane.
- `python3 scripts/codex/verify_mainline_clarity.py` passed.
- `python3 scripts/codex/check_program_state_integrity.py --skip-diff-check` passed.
- `python3 -m py_compile ego_desktop_lab/*.py` passed.
- `TMPDIR=/tmp PYTHONDONTWRITEBYTECODE=1 python3 -m pytest ego_desktop_lab/tests -q` passed with `189 passed`.
- `python3 scripts/codex/verify_repo.py --mode fast` passed; OpenEmotion live health smoke was skipped because the local health endpoint was unavailable.
- Scoped whitespace check for this change surface passed.

## Known Limitation

The broad cleanup command `git diff --check -- docs EgoCore OpenEmotion ego_desktop_lab artifacts scripts` is still blocked by pre-existing unrelated runtime artifacts and logs with whitespace issues. This task does not clean or stage those files.

## Claim Ceiling

Repo readability and route discipline only. This does not prove runtime efficacy, live autonomy, consciousness, alive status, or user benefit.
