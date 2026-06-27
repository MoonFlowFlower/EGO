# Plan

1. Add failing tests for hash-only capture manifest generation and cache-hash mismatch rejection.
2. Implement `scripts/codex/build_egodesktop_gablation_capture_manifest.py`.
3. Generate `CAPTURE_MANIFEST.json`, `CAPTURE_MANIFEST.sha256`, and `BUILD_REPORT.json`.
4. Verify committed manifest contains no raw text and raw cache remains ignored.
5. Regenerate route-convergence views.
6. Run local checks and source-limited review.
7. If accepted, commit locally only.

## Non-Goals

- No raw text staging.
- No EgoDesktop run or row capture.
- No scoring/comparison/verdict.
- No runtime enablement.
- No program-state/evidence-ledger update.
- No push, tag, or remote anchor.
