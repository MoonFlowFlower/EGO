# Plan

1. Read current 010, 011, and 012 task docs plus `Tasks/TASK_BOARD.yaml`.
2. Draft a docs-only 013 route reconciliation package.
3. Update 010 task-board/status wording so it no longer points to 011 as the current next action.
4. Preserve 012 as a route decision only and avoid any capture/scoring authority.
5. Regenerate route-convergence views.
6. Run local checks:
   - YAML parse for `Tasks/TASK_BOARD.yaml` and mutation scopes;
   - `python scripts\codex\generate_route_convergence_views.py`;
   - `python scripts\codex\verify_route_convergence.py`;
   - `python scripts\codex\verify_repo.py --mode fast`;
   - `git diff --check`.
7. Send Claude a compact source-limited review packet requesting:
   - `NO_BLOCKING_FINDINGS`, with next minimal action; or
   - `BLOCKING_FINDINGS`, with numbered blockers and required repairs.
8. Repair any blocker, rerun checks, and commit locally if accepted.

## Non-Goals

- No synthetic prompt-pack v3.
- No real-turn capture.
- No same-access baseline execution.
- No scoring, comparison, verdict, or route advancement.
- No default runtime enablement.
- No `PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger update.
- No push, tag, or remote anchor.
