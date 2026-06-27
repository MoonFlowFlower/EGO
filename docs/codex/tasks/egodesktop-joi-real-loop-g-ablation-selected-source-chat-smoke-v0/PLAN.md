# Plan

1. Materialize one single-chat-turn userText from the first 021 selected source row using the deterministic source-row
   derivation rule.
2. Write a hash-only `TRIGGER_INPUT_REPORT.json` without raw text via
   `scripts/codex/materialize_egodesktop_selected_source_trigger_input.py`.
3. Run EgoDesktop smoke with explicit `JOI_REAL_LOOP_*` flags and `--joi-real-loop-chat-smoke-text` supplied from memory.
4. Verify smoke report status, trace row count, and user-text hash alignment.
5. Regenerate route-convergence views.
6. Run local checks and source-limited review.
7. If accepted, commit locally only.

## Non-Goals

- No raw text staging.
- No scoring/comparison/verdict.
- No same-access baseline.
- No default runtime enablement.
- No program-state/evidence-ledger update.
- No push, tag, or remote anchor.
