# Plan

1. Add failing tests for opt-in public raw-cache sample behavior.
2. Implement minimal downloader functions for:
   - DailyDialog HF rows API bounded sample.
   - EmpatheticDialogues public archive bounded CSV sample.
3. Keep default CLI metadata-only behavior unchanged.
4. Add explicit `--raw-cache-sample`, `--max-rows`, and `--split` CLI options.
5. Run tests and generate `RAW_CACHE_REPORT.json` plus SHA256 sidecar.
6. Verify raw text exists only under ignored `source_cache/` and is not staged.
7. Regenerate route-convergence views.
8. Run local checks and source-limited review.
9. If accepted, commit locally only.

## Non-Goals

- No full-cache completeness claim.
- No desktop capture.
- No scoring, comparison, verdict, or route advancement.
- No runtime enablement.
- No program-state or evidence-ledger update.
- No push, tag, or remote anchor.
