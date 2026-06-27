# Plan

1. Use committed 022 `trace/trace_rows.jsonl` as the only source row input.
2. Run `node EgoDesktop/scripts/build-joi-g-ablation-off-static-replay-heldout.js` into the 023 artifact directory.
3. Run `node EgoDesktop/scripts/evaluate-joi-g-ablation-replay.js --require-007-scoring-precondition` on the builder row.
4. Verify builder/evaluator status, scoring/verdict authorization flags, source-row linkage, and raw-text absence.
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
