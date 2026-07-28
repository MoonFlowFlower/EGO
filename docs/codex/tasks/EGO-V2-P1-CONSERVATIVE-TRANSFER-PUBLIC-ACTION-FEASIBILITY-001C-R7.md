# EGO-V2-P1-CONSERVATIVE-TRANSFER-PUBLIC-ACTION-FEASIBILITY-001C-R7

## Bounded task card

- **Task type:** docs-only freeze for a seed/world-free,
  source-bank-abstracted, static public-information feasibility preflight
  before any producer, product-path, or neural implementation.
- **Layer:** learning/adaptation mechanism-hypothesis preflight plus
  evidence-instrument engineering; `science_weight=0`.
- **Repository:** `D:\Project\AIProject\MyProject\Ego`.
- **Branch:**
  `codex/ego-v2-conservative-transfer-decision-rule-redesign-001c-r7`.
- **Base commit:** `28ac8ce8ea4d751af10b7d77265fadd3e6edbbc8`.
- **Normative predecessor:** R6 commit
  `28ac8ce8ea4d751af10b7d77265fadd3e6edbbc8`, with exact SHA-256:
  - R6 card:
    `7c346dc7823450c9d0e46c34755dd6d5201f49ed25321786197d6c1d1686dfdf`;
  - R6 collision record:
    `09892072532fa9f6aacabc0b78c7a4a40611cc369f34c4416c46529e1e7ae9e3`;
  - R6 producer:
    `342161a515eaeea9e0c1c7f0c9178a23215174b1b12a9009abdc7d7ac6905d9e`;
  - R6 test:
    `100160fdb8c68a1450d17b2433b357cae3a9f6c96de7754e9db8667f764af475`;
  - R6 result file bytes:
    `498225d48a3deb4dd484cbfbace5ef739470a969efbfe300a74b403e2a58477b`.
- **Lineage discontinuity:** R7 does not edit, rescore, repair, or promote R5
  or R6 evidence. It asks whether the public information boundary admits the
  requested two-sided effect after replacing the loss-mismatched posterior
  mean scratch control by the correct equal-access L1 decision.

## Why the problem must be reframed before implementing another gate

R6 proved only that the exact R5 posterior-mean candidate plus lower-5%
benefit gate never leaves scratch at budget two. A less conservative quantile,
an expected-upside/downside ratio, or a neural selector could still move away
from scratch, but component existence would not answer the real question:
whether one learner-visible state permits exact source-member benefit without
harm to every nonmember completion.

The endpoint is MAE. A posterior mean is the Bayes action for squared loss,
not absolute loss. For absolute loss, a componentwise posterior median is the
loss-matched Bayes action. After two distinct successful public rows, each
unobserved token has the same uniform distribution over the three remaining
public prototype increments under zero-source scratch. The equal-access
control is therefore the componentwise median of those three increments, not
the R5 mean.

This is a standard Bayesian decision-theory correction, not a new neural
mechanism. R7 first tests the information-theoretic/action-feasibility boundary
against that stronger control. A neural or amortized implementation is
forbidden unless a later task first establishes headroom beyond this control.

## Problem definition

For each of the ten possible remaining-prototype loss geometries after two
distinct successful observations:

1. enumerate its six compatible target-mapping completions;
2. construct the unique equal-access public L1 action for all three unobserved
   tokens;
3. consider every nonempty membership mask over the six completions, where a
   completion is `TRUE_ANALOGY` iff that exact mapping occurs at least once in
   the anonymous six-source bank and otherwise is a
   `NONMEMBER_COMPLETION`;
4. determine whether any target-truth-blind public action can simultaneously:
   - improve every true-analogy completion by at least `0.021875` MAE; and
   - harm no nonmember completion under the strict rule, or by at most the
     already-frozen R5 practical margin `0.004375` under the bounded rule.

The learner action may depend on the anonymous public source bank, public
prototype table, and the two public rows. It may therefore derive the complete
membership mask over the six compatible completions from the public source
bank. It may not depend on which compatible completion is privately realized
as the target truth or on that realized completion's evaluator class label.
The evaluator selects each possible realized truth outside the learner boundary
to score the same mask-dependent action. A randomized learner has one
truth-independent conditional action distribution for that mask; the same
loss-sum inequality holds after expectation, and equality requires placing
probability one on the unique public median action.

## Hypothesis and falsifier

- **H1-strict:** at least one learner-visible public state admits an action that
  achieves the minimum true-analogy gain for every true completion and has
  zero positive regret for every nonmember completion.
- **H1-bounded:** at least one such state admits the same true-analogy gain
  while every nonmember completion stays within `0.004375` MAE regret.
- **Falsifier:** an exact loss-sum proof shows that neither feasible action set
  can be nonempty for any nonempty true-analogy membership mask.

The primary adjudication is universal over truth completions within one
learner-visible public alias class. Formally it quantifies:

```text
for every public source bank B and legal two-row history H2,
M = exact-member mask derived from (B,H2),
A = f(B,H2),
score the same A against every realized truth pi in Omega(H2).
```

The ten remaining sets are only the quotient of this universal statement by
observed-token order, token relabelling, and source-bank identity at the loss
geometry. Because the proof quantifies over every mask and every action, bank
dependence is absorbed rather than omitted. The future implementation card
must test quotient completeness and relabel invariance explicitly.

Distributional average transfer, R5's designated D2/D3/D4 targets, local-shift
subsets, and a fixed-bank contract are different future hypotheses and cannot
rescue or be adjudicated by this card.

## Baselines and candidate collision

1. **R5 scratch mean:** historical control only; retained to show the loss
   mismatch and never used as the R7 admission baseline.
2. **PUBLIC_PREFIX_L1_MEDIAN_MINIMAX:** primary equal-access control. For each
   unobserved token and component, use the scalar median of the three remaining
   public prototype increments. Under the uniform six-completion scratch model
   this uniquely minimizes posterior expected total L1 loss. It is also the
   unique minimax action because `L(B,pi)=C_R` for every completion and:

   ```text
   max_pi L(A,pi) >= average_pi L(A,pi)
                    >= average_pi L(B,pi) = C_R = max_pi L(B,pi).
   ```
3. **Source-aware posterior L1 median:** standard expected-risk challenger. It
   may improve source-favoured completions but has no pointwise nonmember
   guarantee.
4. **Baseline-regret-constrained Bayes action:** standard robust decision-rule
   target. Its action set is feasible only if the exact completion-wise
   constraints have a nonempty intersection. R7 tests this feasibility before
   implementing an optimizer.

If the unrestricted public action set is empty under the frozen constraints,
all more restricted Bayesian, MDL, lookup, neural, or hard-reuse selectors are
also blocked at this information boundary.

## Exact theorem contract

Let `R` be one remaining set of three public four-component increment vectors,
`Omega(R)` its six permutations across the three unobserved tokens, and
`A=(a0,a1,a2)` an arbitrary public action. Let total endpoint error in integer
micro-units be:

```text
L(A, pi) = sum_{token=0..2} sum_{component=0..3}
           abs(a_token_component - truth(pi,token,component))
```

Observed-token differences are zero, so MAE uses the existing full endpoint
denominator `5 tokens x 4 components = 20`.

For the public L1 action `B`, each `b_token` equals the componentwise median of
the three vectors in `R`. The verifier must derive, not assume:

```text
sum_{pi in Omega(R)} L(A,pi)
  = 2 * sum_{token=0..2} sum_{prototype in R}
        L1(a_token, prototype)
  >= sum_{pi in Omega(R)} L(B,pi)
```

Because each scalar objective contains exactly three values, its median is a
unique minimizer; equality holds only for `A=B`.

The same result covers randomized actions. Taking expectation over a
truth-independent action distribution preserves the loss-sum inequality by
linearity. Equality requires `A=B` almost surely, so the `k=1` equality case
still cannot contain positive true gain.

Convert the frozen effect sizes to exact total-error micro-units:

```text
true_gain_threshold = 0.021875 * 20 * 1,000,000 = 437,500
bounded_regret       = 0.004375 * 20 * 1,000,000 = 87,500
strict_regret        = 0
```

For a membership mask with `k>=1` true completions, the bounded constraints
would require:

```text
sum_pi [L(A,pi)-L(B,pi)]
  <= -k*437,500 + (6-k)*87,500
   = 525,000*(1-k)
```

For `k>=2` this contradicts the lower bound of zero. For `k=1` it can only
equal zero, which requires `A=B`; but `A=B` has zero true gain, contradicting
the required `437,500`. The strict rule is at least as impossible. The
successor producer must verify all ten remaining sets and all `2^6-1=63`
nonempty masks, report
the algebraic bounds by `k=1..6`, and retain two-sided positive/negative
dispatcher tests rather than hard-code the expected verdict.

## Active intervention boundary

This card fixes the same two public rows. An acquisition policy cannot create
information after those rows are already fixed. No EIG, EVSI, entropy, query,
navigation, controller, or primitive action is implemented or scored here.

A future active-diagnosis card is admissible only from an identical pre-budget
checkpoint and must compare its selected second query against passive/EIG
controls. It must show a non-tie query change and computed endpoint effect. That
future card changes the public information state and is not a rescue of R7.

## Frozen trace/replay requirement for the successor implementation card

The future producer writes canonical evidence under the task artifact root. A fresh
CLI process must recompute the proof receipts before reading the prior bundle,
canonicalize outputs, and require exact equality of result content and core
file hashes. Stored verdicts and expected R7 values are never inputs.

The future trace records each remaining-prototype set, six-permutation multiplicity,
unique median action, baseline error, every membership size bound, and the
first decisive contradiction. It contains no world, seed, private mapping,
source row, controller state, or runtime trace.

## Frozen ablations and positive controls for the successor implementation card

- Replace the L1 median by the R5 mean and show at least one geometry loses the
  zero-regret optimality/equality certificate; this is diagnostic only.
- Set true gain to zero and use the exact public median `A=B` in a synthetic
  call; verify zero gain and zero regret for all six completions and reach the
  strict-feasible dispatcher branch through the same loss path.
- Source deletion collapses the membership mask to empty and therefore removes
  the true-analogy question; it is not counted as a positive result.

## Leakage and contamination firewall

- No source/development/held-out world or policy seed is run.
- No world in `30..150` or above `150` is inspected.
- No `_token_mapping`, `objects_by_cause`, cause name, controller, engine,
  transition, scorer, or prior result field is a learner input.
- The five anonymous prototype bytes and hashes are frozen exactly in
  `FROZEN_DESIGN.json`; the future producer reads that committed design path
  directly and must not import the R6 producer or any runtime module.
- The fixed five-prototype/120-mapping grammar is development/design evidence
  because R6 already inspected it exhaustively. Even a positive R7 result could
  not be called fresh confirmation.

## Required evidence artifacts for a separate successor implementation card

Under
`artifacts/EGO-V2-P1-CONSERVATIVE-TRANSFER-PUBLIC-ACTION-FEASIBILITY-001C-R7/`:

- `result.json`;
- `trace.jsonl`;
- `baseline_comparison.json`;
- `ablation_report.json`;
- `replay_report.json`;
- `failure_manifest.json` when the formal hypothesis fails;
- `claim_ceiling.txt`.

Each future score or proof receipt records producer function, exact inputs,
aggregation rule, code-path hash, task/design/test hashes, runtime versions,
and run ID.

## Frozen acceptance gate for a separate successor implementation card

Accept the evidence bundle only if:

1. the exact R6 commit and five predecessor hashes match;
2. the frozen R7 card, collision record, and design hash match the producer;
3. the producer is standard-library-only, imports neither R6 producer nor
   product runtime, and its CLI allowlist contains only `--output-dir` and
   `--replay-expected-dir`; unknown arguments fail closed;
4. all ten loss-geometry quotient classes, six completions, 63 nonempty masks,
   and mask sizes `1..6` are covered by exact Python-integer arithmetic, with
   explicit token/prototype relabel-invariance and quotient-completeness tests;
5. the six-permutation loss-sum identity and unique-median equality condition
   are independently checked by tests;
6. strict and bounded contradiction branches are computed, not literals, and
   the randomized-action extension is checked symbolically from the deterministic
   unique-equality receipt;
7. synthetic tests reach feasible, infeasible, private-input, and
   instrument-invalid dispatcher branches;
8. the mean-baseline ablation and the exact `true_gain=0,A=B` positive control
   exercise genuine computation paths;
9. a fresh-process replay reproduces canonical result and core hashes;
10. no product source, navigation, neural model, seed, pilot, push, or tag is
    used.

## Verdict dispatch

First true condition:

1. `PRIVATE_TRUTH_OR_SEED_INPUT`;
2. `PUBLIC_ACTION_FEASIBILITY_INSTRUMENT_INVALID`;
3. `PUBLIC_INFORMATION_TWO_SIDED_HEADROOM_ABSENT` when strict and bounded
   feasible-mask counts are both zero;
4. `BOUNDED_REGRET_ONLY` when strict is empty but a bounded feasible mask
   exists;
5. `R7_STATIC_REFERENCE_FEASIBLE` only when a strict feasible mask exists.

No verdict automatically authorizes product-path implementation. This
docs-only card does not authorize running the formal producer; a separate
implementation card must bind the committed hashes of all three R7 design
documents.

## Stop conditions

- Any R6 authority byte/hash drifts.
- Any private mapping, seed, source row, runtime trace, or world input is used.
- Any threshold or baseline changes after the formal run.
- The R5 mean is retained as the primary MAE baseline.
- Average or favourable-case performance hides a completion-wise failure.
- An LP/optimizer numerical status replaces the exact loss-sum proof.
- Any producer, evidence generation, neural, controller, navigation,
  acquisition, or product-path implementation begins under this docs-only card.
- Any artifact is hand-authored rather than generated and replayed.

## Rollback

Remove only uncommitted R7 files named below. Never reset, amend, rewrite,
delete, or mutate R5/R6 or unrelated files. A correction is a successor commit.

## Allowed files

- `docs/codex/tasks/EGO-V2-P1-CONSERVATIVE-TRANSFER-PUBLIC-ACTION-FEASIBILITY-001C-R7.md`
- `docs/codex/tasks/ego-v2-p1-conservative-transfer-public-action-feasibility-001c-r7/COLLISION_RECORD.md`
- `docs/codex/tasks/ego-v2-p1-conservative-transfer-public-action-feasibility-001c-r7/FROZEN_DESIGN.json`

All producer, test, artifact, product source, `labs/`, controller, engine,
predictive-control, microworld, store, UI, launcher, route-state, historical
artifact, world/seed/pilot, push, and tag paths are forbidden.

## Future learned-policy firewall

The static evaluator and its proof outputs are verifier-only. No future learned
candidate may receive its action, feasible/infeasible status, membership-size
bound, verdict, artifact hash, or proof receipt as a forward input.

A future learned candidate may receive only the canonical public prototype
table; six anonymous public source mappings; committed legal public history
including its own action and public outcome; public per-token feedback counts;
budget remaining; and its own serialized learner state. It must not receive any
world/seed/run/source/target/class/distance ID, hidden mapping/cause,
`objects_by_cause`, scorer, future observation, checkpoint-selection metric, or
static-oracle output. Any learned or active-query candidate requires a separate
task card.

## Claim ceiling

This card freezes only a future exact seed-free public-action feasibility test
for the fixed R6 five-prototype grammar, two-successful-row information state,
equal-access L1 baseline, and universal exact-member-benefit/nonmember-safety
contract. It does not itself produce evidence and does not adjudicate R5's
designated D2/D3/D4 subset, local-shift targets, a fixed-bank or distributional
contract, active-query feasibility, controller-path effect, transfer learning,
neural emergence, survival benefit, AGI, agency, consciousness, subjectivity,
emotion, companion readiness, or electronic life.

## Auto-Remote-Anchor

`forbidden`
