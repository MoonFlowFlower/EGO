# Plan

1. Add failing tests for `wizard_of_wikipedia_hf` manifest admission and raw-cache action support.
2. Run the focused tests and confirm they fail because the source is not yet implemented.
3. Add the manifest row and downloader HF rows method.
4. Regenerate source manifest/download plan artifacts.
5. Run bounded raw-local cache sample with `--max-rows 25`.
6. Verify reports contain no raw text and raw `source_cache/` remains ignored.
7. Run local checks and source-limited review.
8. If accepted, commit locally only.

## Non-Goals

- No raw text staging.
- No capture/replay/scoring.
- No same-access baseline.
- No default runtime enablement.
- No program-state/evidence-ledger update.
- No push, tag, or remote anchor.
