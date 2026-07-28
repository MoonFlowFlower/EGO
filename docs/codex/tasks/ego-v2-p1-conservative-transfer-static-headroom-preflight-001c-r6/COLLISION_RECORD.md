# Collision record — EGO-V2-P1-CONSERVATIVE-TRANSFER-STATIC-HEADROOM-PREFLIGHT-001C-R6

## Candidate approaches

| Candidate | Evidence | Strongest objection | Leakage risk | Smallest falsifier | Disposition |
|---|---|---|---|---|---|
| Proceed directly to controller/navigation implementation | Real-path engineering could eventually run | R5 reference may already be mathematically incapable of its primary endpoint | Large code path built around a dead decision rule | Show maximum gated budget-2 improvement is zero | Reject pending preflight |
| Check only the maximally favorable six-identical-source example | Cheap analytic counterexample | One source multiset does not prove all admissible multisets fail | None, but incomplete coverage can overclaim | Find another source multiset with positive gated improvement | Challenger only |
| Monte Carlo source/target sampling | Empirical estimate of rarity | A rare positive state could be missed and thresholds do not need sampling here | Seed choice can become hidden tuning | Change RNG/sample count and find instability | Reject |
| Exact finite enumeration of all attainable posterior weight states | Complete reachability result for the frozen gate | Could still encode the wrong math or symmetry reduction | Wrong prototype/order/prior units could create a fake no-go | Independent full ordered-pair enumeration and fixed-signature tests | **Selected** |

## Hostile checks

1. Recompute public prototype JSON hashes; do not trust literals alone.
2. Assert mapping indices `0`, `24`, and `119` and the ten one-swap grammar.
3. Derive, rather than list, 13 per-source contribution vectors.
4. Derive, rather than list, 18,564 attainable six-source sums.
5. Use integer micro-units and exact half-even rational rounding.
6. Use integer 5% CDF crossing, including exact 1/20 and below-1/20 boundary
   tests.
7. Cover all 120 target mappings by an explicit symmetry argument, separately
   require exact-target membership for the true-analogy positive branch, and
   compare with a structurally separate 20-ordered-pair enumeration.
8. Verify stored verdict/output never enters recomputation.
9. Record both maximum positive-effect count and nontrivial gate-use count.
10. Treat zero headroom as the reference/gate's bounded failure, not causal-
    schema, transfer learning, neural learning, or AGI falsification.

The two enumeration implementations and role reviews remain inside the same
model/tool lineage.  They provide algorithmic cross-checking, not external
independent audit.

## Expected negative mechanism

After two exact observations, six mappings remain.  The scratch family retains
full support.  Even under strong source concentration, any nontrivial
source-biased prediction leaves more than 5% posterior mass on mappings for
which moving away from the scratch centroid increases MAE.  The lower-5% rule
therefore falls back to scratch.  This is a hypothesis until the complete
enumerator and independent replay agree.

## Kill criteria

- Any repo mapping/seed/world/source trace is inspected or supplied.
- Any result-dependent threshold/prior/quantile/budget change.
- Any floating-point verdict arithmetic.
- Any missing source multiset state or target mapping.
- Any hand-authored result/trace/baseline/ablation/replay verdict.
- Any product source change or implementation continuation after no-headroom.
- Any push/tag/remote publication.

## What this cannot prove

It cannot show that all conservative-transfer rules are impossible.  It tests
only the exact R5 family priors, likelihood, six-source grammar, BMA point,
lower-5% gate, budget two, public prototype geometry, scratch baseline, and MAE
endpoint.  A prospective rule could differ, but must be frozen before target
execution and cannot reinterpret this negative result into a pass.
