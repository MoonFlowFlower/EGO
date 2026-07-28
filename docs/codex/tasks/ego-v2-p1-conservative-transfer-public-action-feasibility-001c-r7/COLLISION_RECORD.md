# Collision record — EGO-V2-P1-CONSERVATIVE-TRANSFER-PUBLIC-ACTION-FEASIBILITY-001C-R7

## Candidate approaches

| Candidate | Evidence it could produce | Strongest cheap baseline / objection | Leakage or hard-coding risk | Smallest falsifier | Disposition |
|---|---|---|---|---|---|
| Lower the R5 quantile or use an upside/downside ratio on its posterior mean | More non-scratch uses and possible mean gain | It changes a gate after R6 exposed zero use, retains the MAE/mean mismatch, and may buy true gain with nonmember harm | Threshold tuning to finite geometry | One completion violates the frozen regret margin | Reject |
| Implement a neural transfer selector now | Could learn source/scratch/local weights and abstention | On 18,564 already-exhausted public states it can be an opaque lookup table; no public-information headroom has been established | World/seed/state fingerprint memorization; hidden class proxy | Exact public alias class requires contradictory outputs | Reject before static feasibility |
| Evaluate source-aware posterior L1 median only | Standard posterior expected-MAE challenger | Expected Bayes risk is not a completion-wise safety guarantee | Prior misspecification can masquerade as learning | Any target-absent completion exceeds the margin | Challenger only |
| Solve a baseline-regret-constrained Bayes optimization numerically for every state | Directly expresses the desired loss and safety constraint | An optimizer cannot create a feasible intersection; floating infeasibility is weaker than an exact structural proof | Solver tolerance or status becomes fake evidence | Algebraic loss-sum lower bound contradicts constraints | Reject before theorem check |
| Exact public alias-class loss-sum proof against the L1 median baseline | Outcome-independent existence/nonexistence result for every public action | It tests only fixed two-row information and universal completion-wise safety, not distributional or active-query transfer | Wrong denominator, mean baseline, or hidden truth entering action | Exhibit one mask/action satisfying exact inequalities | **Selected** |

## Strongest hostile argument

With the same anonymous source bank and the same two public rows, the learner
can derive which of the six compatible completions occur in that bank, but it
cannot know which completion is the realized target truth. A deterministic
learner must emit one mask-dependent action for all six possible truths; a
randomized learner has the same mask-dependent conditional action distribution.
Only the realized truth and its resulting exact-member/nonmember label are
evaluator-only.

The strongest equal-access control is not the historical posterior mean. Under
the MAE endpoint, the public componentwise median minimizes the average loss
over the six completions. Requiring positive gain on every source-member truth
and bounded harm on every nonmember can therefore demand a negative total
regret that no public action can attain.

## Frozen distinctions

- `TRUE_ANALOGY`: exact target mapping occurs in the six-source multiset.
- `NONMEMBER_COMPLETION`: exact target mapping does not occur. This is a
  theorem-local superset, not a synonym for R5's designated D2/D3/D4 near-miss
  targets. Distance strata remain separate future hypotheses.
- `strict no worse`: completion regret `<=0` relative to the public L1 median.
- `bounded regret`: completion regret `<=87,500` total-error micro-units,
  exactly `0.004375` MAE.
- `substantive benefit`: completion improvement `>=437,500` total-error
  micro-units, exactly `0.021875` MAE.

`BOUNDED_REGRET_ONLY` must never be described as no worse than scratch.

## Anti-hardcoding checks

1. Prototype vectors are decoded from R6-frozen canonical JSON bytes and hashes
   are recomputed.
2. Remaining sets and six permutations are derived with `itertools`.
3. Membership masks are derived from integers `1..63`; no expected case counts
   are supplied to the producer.
4. The median action is computed from values, not copied from expected output.
5. Loss-sum multiplicity two is cross-checked by explicit permutation
   enumeration on synthetic actions.
6. Verdict dispatch accepts computed feasibility summaries and has an exact
   `true_gain=0,A=B` synthetic positive branch plus the formal negative branch.
7. No source bank, mapping truth, world, seed, result, scorer, or controller is
   accepted by the CLI.
8. Tests include a deliberately weaker threshold/margin contract that reaches
   feasibility; the expected negative cannot be embedded as the only path.

## Kill criteria

- Retaining the R5 mean as the primary MAE control.
- Inspecting any world mapping or running any seed/pilot.
- Using average gain to hide any completion-wise regret failure.
- Changing `437,500`, `87,500`, the denominator 20, budget two, or the public
  information boundary after formal output.
- Treating a solver's floating infeasibility status as the proof.
- Implementing neural weights, acquisition, navigation, or product integration.
- Rewriting R5/R6 evidence or publishing via push/tag.

## What a negative result cannot prove

It cannot show that causal-schema transfer, learned transfer selection, or
active diagnosis is generally impossible. A future negative can close only the
universal exact-member-benefit/nonmember-safety effect at this fixed public
information boundary. It does not adjudicate R5's designated D2/D3/D4 subset,
local-shift targets, a fixed-bank contract, or a distributional/tail-risk
contract. Possible successor framings must change something substantive and
predeclared: the public information state through active query, the evaluation
contract, or the task grammar. They may not merely rename or soften the same
gate after seeing R7.
