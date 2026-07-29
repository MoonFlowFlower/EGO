# Implementation plan — EGO-V2-P1-ACQUISITION-CAPACITY-CERTIFICATE-001H-R2

1. **Docs-only freeze.** Commit this task card, collision record, and plan as the normative interpreter-spec commit. Verify that the delta contains exactly these three paths. Do not write code or run R2 search in this phase.
2. **TDD RED: immutable contract and anti-rescue.** Add failing tests for every frozen context, budget, lifecycle bound, support floor, quotient definition, rank threshold, panel rollout ID, target multiplicity, panel floor, source pin, and stale-seed firewall. Mutating any field must produce `INVALID_POSTRESULT_RESCUE` before scientific adjudication.
3. **TDD GREEN: pure contract and lower bound.** Implement only the R2 frozen contract parser, exact authority checks, verdict dispatcher, 76-action analytic lower bound, and its support/rank-overlap tests. Import the R1 verifier as a pinned dependency instead of copying or modifying its runtime semantics.
4. **TDD RED/GREEN: canonical DFS search node.** Define the complete active-stack evaluator/search-node serialization, fixed child order, exact row/rank payload, same-`g`/lexicographic exact-duplicate rules, lifecycle handling, streamed digest/count receipts, node-level leaf dispositions versus five-action expanded-node dispositions, and the two-million-processed-node cap. Keep only stack-local full state/rows plus a disk-backed binary-digest/packed-prefix duplicate ledger. Test that approximate/support-only/rank-only equivalence is rejected and that a same-key/different-`g` observation is an implementation error.
5. **TDD RED/GREEN: witness candidate and replay.** Implement the optional deterministic macro warm start, including the direct-action sentinel ordering, and primitive depth-first branch-and-bound enumeration. Both advance only through the unchanged R1 evaluator action/respawn functions. A positive candidate must replay from canonical initial state to byte-equal rows, support, ranks, lifecycle, and trajectory hash; a replay-valid warm-start certificate skips DFS only for that context. Warm-start failure has no verdict authority and leaves the DFS root untouched.
6. **TDD RED/GREEN: complete/inconclusive distinction.** Synthetic finite fixtures must prove that completed root traversal yields `complete_search=true`, while an unprocessed legal child at the processed-node cap yields `WITNESS_SEARCH_INCONCLUSIVE`. A separate traversal/checker must recompute every five-action disposition and sound prune; digest equality alone is insufficient. Only independently verified complete DFS exhaustion may route to `FROZEN_BENCHMARK_CAPACITY_REFUTED`.
7. **TDD RED/GREEN: panel certificate search.** Keep rollout IDs `9..16`, target multiset, within-context-only dedupe, forced five-action expansion, floors, ranks, and natural-terminal semantics unchanged. Search only legal navigation order/checkpoints using compact hash/reference/parent-pointer queue records plus a disk-backed content-addressed evaluator-state store; do not copy complete prefixes/rows/state JSON per queue entry. Process rollouts deterministically with the fixed 250,000-node per-context/rollout cap, route cap hits to `PANEL_SEARCH_INCONCLUSIVE`, and replay every accepted checkpoint/row through live callables.
8. **TDD RED/GREEN: evidence integrity.** Add recursive leakage scans with direct/base64/numeric-index positive controls; fresh subprocess search/replay equality; an independent row reducer; exact artifact manifest; and tamper controls for constraints, source hashes, nodes/search digest, candidate rows, panel rows, producer receipts, and verdict.
9. **Focused verification before formal execution.** Run the R2 tests in isolated processes, the complete R1 verifier tests, relevant 001F recovery/predictive tests, compile/import checks, anti-hardcoding/source scans, `git diff --check`, and exact allowed-path audit. Do not run the formal R2 output.
10. **Implementation commit.** Commit exactly the R2 verifier and R2 test file. Re-read HEAD, parent, status, source hashes, runtime receipt, and output absence.
11. **Pre-run provenance commit.** Write only `PRE_RUN_PROVENANCE.json`, binding the normative interpreter-spec commit, implementation commit, exact source/test/input/dependency hashes, Python 3.12.13, NumPy 2.2.6, dtype `<f8`, search cap, and absent/empty output. Commit it separately and require a clean tree.
12. **Single formal execution.** Run R2 exactly once on the two already-consumed contexts. Never modify the frozen search cap, constraints, ordering, or implementation after observing the output.
13. **Independent recomputation and hostile review.** Recompute artifact hashes, raw-row support/rank/lifecycle, search digests, complete/inconclusive flags, panel support/rank/dedupe, leakage controls, and verdict with a separate reducer. Conduct same-model internal hostile review and disclose that it is not external independent replication.
14. **Bank every verdict.** Commit the exact formal packet without threshold repair. `EXISTENTIAL_CAPACITY_CERTIFICATE_FOUND` permits only a separate evidence-value preflight card. `FROZEN_BENCHMARK_CAPACITY_REFUTED` supports closure of this exact frozen benchmark surface. `WITNESS_SEARCH_INCONCLUSIVE`, `PANEL_SEARCH_INCONCLUSIVE`, and `PANEL_CAPACITY_NOT_CERTIFIED` stop R2 with capacity unresolved and do not authorize scientific closure or another same-framing planner patch.

## Planned implementation paths

- `scripts/codex/verify_ego_v2_acquisition_capacity_certificate_001h_r2.py`
- `scripts/codex/tests/test_verify_ego_v2_acquisition_capacity_certificate_001h_r2.py`

## Planned later provenance path

- `docs/codex/tasks/ego-v2-p1-acquisition-capacity-certificate-001h-r2/PRE_RUN_PROVENANCE.json`

## Planned formal output path

- `artifacts/EGO-V2-P1-ACQUISITION-CAPACITY-CERTIFICATE-001H-R2/`

## No-go

Do not modify runtime source, R1 files, banked artifacts, environment/metabolism/action semantics, budgets, floors, contexts, rollout IDs, target multiplicities, or the held-out firewall. Do not install OR-Tools or any new search dependency; use the pinned Python/NumPy dependency set.
