# Collision Record — EGO-V2-P1-ACTIVE-TRANSFER-HEADROOM-PREFLIGHT-001D

## Decision boundary

R7 closed a fixed-two-row, same-information-state universal action contract. It did not test whether a source-aware learner can choose a different second observation. This record compares three mechanisms, one rejected reframe, and one mandatory ceiling control before implementation.

## Candidate 1 — Minimal source-Bayes plus EIG

- **Mechanism:** exact source/scratch/local prior; choose the highest-EIG second token; predict with posterior L1 median.
- **Evidence it could produce:** different query, exact-member endpoint gain, source-deletion sensitivity.
- **Strongest cheap baseline:** `MAX_PUBLIC_OUTCOME_ENTROPY`; deterministic outcomes make it exactly equivalent to EIG. Scratch-EIG also collapses to lexical ties under the uniform permutation posterior.
- **Leakage/hard-coding risk:** selecting or reporting only a favourable source bank; using internal entropy/MDL as the success metric; scoring queried-token zero error as transfer.
- **Smallest falsifier:** independently compute outcome histograms and show byte-identical query ordering; score all 120 targets and the three common-unqueried tokens.
- **Expected failure mode:** raw exact-member upside accompanied by D2--D5 negative-transfer tails.
- **Strongest rebuttal:** EIG is a legitimate known method, but in this deterministic finite grammar its name adds no mechanism beyond an entropy lookup and its objective is not matched to endpoint MAE.

## Candidate 2 — Finite consistency/risk-DP shortcut

- **Mechanism:** eliminate incompatible source mappings, retain duplicate multiplicity, fall back to uniform scratch when empty, use L1 medians, and select the query minimizing exact endpoint risk.
- **Evidence it could produce:** the same apparent active-transfer behavior without three-family Bayes, MDL, or neural machinery.
- **Strongest cheap baseline against it:** source-blind `PUBLIC_L1_RISK_DP` and all fixed query pairs.
- **Leakage/hard-coding risk:** it is an explicit finite algorithm and can exploit the complete 120-state grammar; it is not evidence of learned representation.
- **Smallest falsifier:** find a frozen bank/target where the richer transfer mechanism has strictly better common-unqueried prediction without any member/nonmember regression.
- **Expected failure mode:** it matches the richer method on exact members and is safer after source inconsistency, closing special-mechanism headroom on the bounded suite.
- **Strongest rebuttal:** matching this control does not prove learning impossible; it proves only that this finite benchmark cannot distinguish the proposed mechanism from a cheap equal-access shortcut.

## Candidate 3 — Selected: conservative three-family L1-EVSI factorial

- **Mechanism:** exact scratch/source/local model comparison; loss-matched L1 median; lower-5% fallback to same-history scratch; exact L1-EVSI second query; full inference x acquisition controls.
- **Evidence it could produce:** a public-only query policy, exact-member same-history/common-unqueried forward gain, separately reported strict or bounded D2--D5 safety, source/feedback/active ablation sensitivity, and non-equivalence to consistency/risk-DP as an algorithmic reference.
- **Strongest cheap baseline:** `BANK_CONSISTENCY_L1_RISK_DP`, plus public risk-DP, fixed queries, EIG/entropy alias, no-update, lookup, and sham bank.
- **Leakage/hard-coding risk:** posterior/evaluator class aliases, bank cherry-picking, changing thresholds after a tail failure, own-history comparison without factorial attribution, or using queried-token error reduction as forward learning.
- **Smallest falsifier:** the exact 75 candidate-independent primary roles plus four non-rescuing method-stress roles, all 120 truths, common first row, one second query, queried-loss decomposition, same-history/common-unqueried endpoints, and exact Pareto comparison to consistency/risk-DP.
- **Expected failure mode:** the LCB fallback removes exact-member gain, or the raw arm retains gain but violates the nonmember margin; alternatively consistency DP matches it.
- **Strongest rebuttal:** this design is intentionally hard to pass and may close the preregistered bounded suite before visible product work. That is cheaper and more truthful than implementing a neural selector where the ideal legal reference has no distinguishable headroom.

## Mandatory ceiling control — candidate-rule amortized lookup

- **Mechanism:** enumerate the finite public state domain with the canonical candidate once, store only public-state-to-output bytes, and return those bytes through a separate truth-blind callable.
- **Evidence it could produce:** a required byte match proving the verifier covers the candidate's public domain.
- **Strongest rebuttal:** the match is tautological and makes the bounded static suite unable to distinguish online rule execution from precomputation. It cannot be used as support for learning or representation.
- **Smallest falsifier:** any target/scorer/stratum key in the lookup or any in-suite output mismatch is instrument invalid.
- **Disposition:** mandatory claim-ceiling control outside the 45 learner-arm registry. It does not prevent testing whether a useful algorithmic target exists; it prevents upgrading that result into non-memorization or emergent-learning evidence.

## Candidate 4 — Rejected for this card: change environment/task semantics

- **Mechanism:** add continuous/noisy mechanisms or a larger causal program grammar so finite lookup cannot saturate.
- **Evidence it could produce:** stronger meta-learning/generalization pressure.
- **Strongest rebuttal:** the active goal forbids changing environment, metabolism, and action semantics; doing so now would move the goalposts and confound product effect.
- **Disposition:** only a future explicit reframe after 001D closure may reconsider it. It is not an escape hatch for this card.

## Selection

Select Candidate 3 for a static exact preflight only. Candidate 2 is the structural invalidating baseline, not an omitted alternative. Candidate 1 remains a diagnostic arm. Candidate 4 is forbidden in this lane. The amortized ceiling control is mandatory and permanently caps 001D at algorithmic-reference evidence. A full-MAE gain with zero genuine-forward gain is a failure, not partial support.

## Noncanonical scout boundary

A temporary, seed/world-free exploratory calculation over 64 deterministic hash banks indicated:

- raw transfer had substantial exact-member gain but large nonmember tails;
- the lower-5% fallback lost the frozen member threshold;
- consistency elimination nearly matched raw exact-member gain.

This was not preregistered, produced no repository artifact, and cannot count as evidence. It motivates an adversarial formal gate and makes this bounded suite development-only. No threshold or bank was selected to rescue the scout.

## Independence boundary

Statistical, data-flow, hostile, implementation, and final-review roles are same-model internal role separation unless an external process is explicitly recorded. They are not external independent audits.
