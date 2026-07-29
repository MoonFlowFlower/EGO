# Implementation plan — EGO-V2-P1-ACQUISITION-BENCHMARK-ADMISSION-001H-R1

1. Read back base commit, allowed scope, source/input hashes, 001F database run IDs, action counts, state schemas, lifecycle helpers, and held-out firewall.
2. TDD RED for read-only first-89 extraction, current-source recovery equality,
   control-derived max-life/respawn bounds, lifecycle/budget accounting, the
   two exact feature dependencies, 13-column reference projection,
   context/action-local rank, and verdict priority; observe the intended
   failure.
3. TDD GREEN for those pure/control-extraction contracts only.
4. TDD RED/GREEN for exact private BFS, strict listed-order support, the
   current-checkpoint-only rank-gain/least-count rule, reducer/metabolism
   receipts, natural death/respawn, no-reset guard, and support witness. Do not
   add a cause ordering or a broader rank checkpoint search in this task.
5. TDD RED/GREEN for explicit independent-reset panel rollout IDs 9..16,
   exact initial_world_state arguments, frozen target order, deep-copy forced
   truth, context-local checkpoint dedupe before action expansion, post-dedupe
   token/cell floors, context/action-local rank, and model-state non-access.
6. TDD RED/GREEN for recursive leakage positive controls, fresh deterministic digest, independent row reduction, and tamper rejection.
7. Run focused tests, relevant existing recovery/predictive tests, compile/import checks, source scan, git diff check, and allowed-path audit. Do not run formal output.
8. Commit PRE_RUN_PROVENANCE.json after implementation/test bytes are final and canonical output is absent/empty.
9. Execute the formal old-context admission exactly once, then fresh recompute, independent reducer, manifest readback, and same-model internal read-only review.
10. Bank every verdict without threshold/budget/panel edits. Only ADMISSION_READY permits drafting a separate privileged evidence-value task card.
