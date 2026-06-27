# Plan

1. Add failing tests for source manifest builder behavior.
2. Implement the minimal builder under `scripts/codex/`.
3. Run the targeted tests and verify they pass.
4. Generate `SOURCE_MANIFEST.json`, `SOURCE_DOWNLOAD_PLAN.json`, SHA256 sidecars, and a build report.
5. Add 016 task-board entry and regenerate route-convergence views.
6. Run local checks:
   - targeted pytest;
   - YAML parse for `Tasks/TASK_BOARD.yaml` and mutation scope;
   - `python scripts\codex\generate_route_convergence_views.py`;
   - `python scripts\codex\verify_route_convergence.py`;
   - `python scripts\codex\verify_repo.py --mode fast`;
   - `git diff --check`;
   - scoped closeout check.
7. Send source-limited review.
8. If accepted, commit locally only.

## Non-Goals

- No dataset download in 016.
- No source cache creation.
- No gated dataset access or terms acceptance.
- No raw local/private text upload.
- No desktop capture.
- No same-access baseline execution.
- No scoring, comparison, verdict, or route advancement.
- No default runtime enablement.
- No `PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger update.
- No push, tag, or remote anchor.
