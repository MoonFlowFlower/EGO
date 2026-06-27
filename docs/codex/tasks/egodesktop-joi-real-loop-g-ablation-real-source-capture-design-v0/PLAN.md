# Plan

1. Recover repo state and current G-ABLATION route state.
2. Inspect local EgoDesktop/EgoOperator artifacts that may contain chat-turn, trace, or conversation data.
3. Perform metadata-only network checks for public dialogue data candidates.
4. Define `real_source_text`, `real_desktop_trigger`, and `replayable_capture_row`.
5. Draft the 014 source/capture design card and mutation scope.
6. Update `Tasks/TASK_BOARD.yaml` and regenerate route-convergence views.
7. Run local checks:
   - YAML parse for `Tasks/TASK_BOARD.yaml` and mutation scope;
   - `python scripts\codex\generate_route_convergence_views.py`;
   - `python scripts\codex\verify_route_convergence.py`;
   - `python scripts\codex\verify_repo.py --mode fast`;
   - `git diff --check`;
   - scoped closeout check.
8. Send the design to Claude for source-limited review.
9. If accepted, commit locally only.

## Non-Goals

- No dataset download in 014.
- No gated dataset access or terms acceptance.
- No `CREATURE_ON` capture.
- No same-access baseline execution.
- No scoring, comparison, verdict, or route advancement.
- No default runtime enablement.
- No `PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger update.
- No push, tag, or remote anchor.
