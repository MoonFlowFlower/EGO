# EgoDesktop Joi Real-Loop G-ABLATION Synthetic-Pack Route Decision v0 Plan

1. Preserve the 011 Claude v2 `BLOCKING_FINDINGS` in 011 review/status/spec surfaces.
2. Draft a docs-only 012 route-decision card that closes or downgrades the synthetic prompt-pack preregistration path.
3. Make the claim ceiling explicit: no saturation, attribution, route advancement, runtime effect, or mechanism evidence.
4. Add `EGODESKTOP-GABLATION-012` to the task board.
5. Regenerate route-convergence views.
6. Run local checks:
   - YAML parse for `Tasks/TASK_BOARD.yaml` and 012 `MUTATION_SCOPE.yaml`;
   - JSON/SHA check for existing 011 frozen files;
   - `git diff --check`;
   - `python scripts\codex\verify_route_convergence.py`;
   - `python scripts\codex\verify_repo.py --mode fast`;
   - scoped closeout check.
7. Send the route-decision card to Claude asking for exactly:
   - `NO_BLOCKING_FINDINGS`, with next minimal action; or
   - `BLOCKING_FINDINGS`, with numbered blockers, required repairs, and next minimal action.
8. If Claude blocks, repair only docs/wording/scope.
9. If Claude returns no blocking findings, commit locally only.

## Non-Goals

- No synthetic prompt-pack v3.
- No real-turn capture.
- No same-access run.
- No scoring, comparison, verdict, route advancement, program-state update, evidence-ledger update, push, tag, or remote
  anchor.
