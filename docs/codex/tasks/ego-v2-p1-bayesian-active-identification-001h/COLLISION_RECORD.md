# Collision record — EGO-V2-P1-BAYESIAN-ACTIVE-IDENTIFICATION-001H

## Candidate 1 — another estimator-only repair

- **Evidence produced:** different weights or regularization on the same
  move-forward-dominated history.
- **Strongest cheap match:** ridge/RLS or action/front-token lookup.
- **Leakage/hard-coding risk:** post-result regularization and another formula
  presented as new information.
- **Smallest falsifier:** the new estimator receives the same under-supported
  rows and a cheap predictor matches it.
- **Expected failure:** better aggregate fit without identifiable rare-outcome
  evidence.
- **Decision:** reject; the additive estimator framing is frozen.

## Candidate 2 — public count-deficit acquisition

- **Evidence produced:** better-balanced public cells using a persistent query
  and public BFS.
- **Strongest cheap match:** this is itself the strongest cheap acquisition
  control; lookup/RLS must also be crossed with its rows.
- **Leakage/hard-coding risk:** target cells and BFS encode environment
  affordances. It is a hand-specified reference, not self-learned exploration.
- **Smallest falsifier:** a learner-blind oracle shows the frozen budget cannot
  cover the declared strata, or fixed quota matches it on adequately supported
  prediction.
- **Expected failure:** navigation consumes the budget, or coverage does not
  create prediction headroom.
- **Decision:** retain only as a future reference after a separate headroom
  preflight.

## Candidate 3 — proposed Jeffreys predictive-entropy selector

- **Evidence it would have produced:** posterior-history-sensitive target order,
  coverage, update-sensitive prediction, and full controller/replay traces.
- **Strongest cheap match:** `PUBLIC_COUNT_DEFICIT_COVERAGE` on the identical
  public query/BFS path.
- **Leakage/hard-coding risk:** a hand-written Bayesian explorer could be
  mislabeled as self-learned; mathematical language could hide a count rule.
- **Smallest falsifier:** prove its ordering is the same function of cell count.
- **Observed pre-implementation failure:** exact
  `(action,front_token)` outcomes make every count vector a permutation of
  `(n,0,0,0,0,0)`. The proposed symmetric score is strictly decreasing in
  `n=0..192`, exactly the ordering of `-n`. Shared ties and adapter imply
  identical trajectories by induction.
- **Decision:** reject before implementation as exact control equivalence.

## Candidate 4 — model-uncertainty experimental design

- **Evidence it could produce:** queries selected by expected reduction in
  posterior uncertainty or proper predictive loss for the
  outcome-conditioned organism-delta model.
- **Strongest cheap match:** count deficit crossed with native, lookup, and RLS
  predictors; leverage/variance-only design without outcome values.
- **Leakage/hard-coding risk:** an evaluator panel or hidden transition model
  could leak into selection; a diagonal symmetric design could collapse back to
  counts.
- **Smallest falsifier:** enumerate reachable public states and show the score
  is a monotone transform of cell count, or show no oracle-balanced prediction
  headroom.
- **Expected failure:** extra covariance machinery selects different rows but
  does not improve supported common-panel loss.
- **Decision:** defer. First establish that the environment and budget contain
  acquisition-to-prediction headroom.

## Selected route and hard stop

No implementation candidate is selected in 001H. The proposed Bayesian
selector is closed by exact cheap-control collision.

The next bounded card should be a learner-blind coverage/prediction-headroom
preflight on consumed contexts. It must:

- certify reachability or report an instrument limitation;
- use an adequately supported common panel;
- keep privileged oracle information evaluator-only;
- distinguish reference coverage from learned selection;
- preserve the canonical runtime and held-out firewall;
- stop before a learned/neural candidate if balanced interventions do not
  improve prediction beyond fixed quota and cheap predictors.

The `16` training-support floor is disclosure-only until a reachability
certificate exists. Raw rank 15 remains impossible. The raw `32768B` JSON mean
is not a mechanism gate under 001G-A0, while replay, tamper rejection, row
readback, recovery time, and carrier growth remain engineering constraints.
