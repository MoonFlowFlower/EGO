# Plan

1. Add failing test asserting `dailydialog_hf` uses the repaired reachable source URL.
2. Update source manifest builder.
3. Rerun source manifest tests.
4. Regenerate manifest/download-plan artifacts.
5. Rerun metadata-only source cache smoke.
6. Add 018 task-board entry and regenerate route-convergence views.
7. Run local checks.
8. Send source-limited review.
9. If accepted, commit locally only.

## Non-Goals

- No raw dataset row download.
- No source cache creation.
- No gated dataset access or terms acceptance.
- No desktop capture.
- No same-access baseline execution.
- No scoring, comparison, verdict, or route advancement.
- No default runtime enablement.
- No `PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger update.
- No push, tag, or remote anchor.
