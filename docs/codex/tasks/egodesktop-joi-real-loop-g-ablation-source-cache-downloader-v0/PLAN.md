# Plan

1. Add failing tests for manifest-driven downloader safety.
2. Implement the downloader with injectable fetcher for tests.
3. Run targeted tests and verify they pass.
4. Add `.gitignore` entry for raw source cache.
5. Run metadata-only smoke against eligible public source pages and write hash-only report.
6. Add 017 task-board entry and regenerate route-convergence views.
7. Run local checks:
   - targeted pytest;
   - YAML parse;
   - route convergence;
   - repo fast verifier;
   - `git diff --check`;
   - scoped closeout check.
8. Send source-limited review.
9. If accepted, commit locally only.

## Non-Goals

- No committed raw dataset text.
- No gated dataset access or terms acceptance.
- No desktop capture.
- No same-access baseline execution.
- No scoring, comparison, verdict, or route advancement.
- No default runtime enablement.
- No `PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger update.
- No push, tag, or remote anchor.
