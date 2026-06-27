# Plan

1. Use committed 026 `trace/trace_rows.jsonl` as the only source row input.
2. Run `node EgoDesktop/scripts/build-joi-g-ablation-off-static-replay-heldout.js` into the 027 artifact directory.
3. Run `node EgoDesktop/scripts/evaluate-joi-g-ablation-replay.js --require-007-scoring-precondition` on the builder
   row.
4. Verify builder/evaluator status, scoring/verdict authorization flags, source-row linkage to the 026 row hash, and
   raw-text absence.
5. Verify the OFF_STATIC row does not falsely claim direct IPC provenance carry-forward; source provenance is only via
   source row path and source row hash.
6. Regenerate route-convergence views.
7. Run local checks and source-limited review.
8. If accepted, commit locally only.

## Non-Goals

- No raw text staging.
- No scoring/comparison/verdict.
- No same-access baseline.
- No default runtime enablement.
- No program-state/evidence-ledger update.
- No push, tag, or remote anchor.

## Decision Log

- 2026-06-27: Claude returned `BLOCKING_FINDINGS` on the draft 027 plan because the OFF_STATIC builder rebuilds
  `public_inputs`, so the task card must not claim direct preservation of 026 IPC provenance inside the rebuilt replay
  row. The accepted carry-forward rule is source artifact path plus `source_row_hash == 026 row_hash`.
