# Plan

1. Recover repo state and accepted 014 source/capture design.
2. Define the 015 source-manifest schema and candidate admission table.
3. Define download, cache, privacy, and license boundaries before any data movement.
4. Add 015 task docs and mutation scope.
5. Add `EGODESKTOP-GABLATION-015` to `Tasks/TASK_BOARD.yaml`.
6. Regenerate route-convergence views.
7. Run local checks:
   - YAML parse for `Tasks/TASK_BOARD.yaml` and mutation scope;
   - `python scripts\codex\generate_route_convergence_views.py`;
   - `python scripts\codex\verify_route_convergence.py`;
   - `python scripts\codex\verify_repo.py --mode fast`;
   - `git diff --check`;
   - scoped closeout check.
8. Send the boundary card for source-limited review.
9. If accepted, commit locally only.

## Non-Goals

- No dataset download in 015.
- No source cache creation.
- No gated dataset access or terms acceptance.
- No raw local/private text upload.
- No `SOURCE_MANIFEST.json` implementation in 015.
- No desktop capture.
- No same-access baseline execution.
- No scoring, comparison, verdict, or route advancement.
- No default runtime enablement.
- No `PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger update.
- No push, tag, or remote anchor.
