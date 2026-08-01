# Preregistration

## Competing explanations

1. **Only permutation-invariant grammar transfers.** The reusable fact is the
   multiset of sign families, not which anonymous token realizes one. Strongest
   rebuttal: without latent alignment the grammar cannot rank two unseen tokens,
   so it may add no actionable information. Cheapest test: transfer the sign
   multiset while forcing every cross-world effect mean to zero; compare with
   no-transfer and the evaluator-only aligned upper bound.
2. **Only confidence calibration transfers.** Cross-world histories may inform
   how quickly to trust current-world feedback even when the prior mean is
   neutral. Strongest rebuttal: concentration without a mean changes only the
   exploration schedule and can just suppress necessary acquisition. Cheapest
   test: transfer one scalar pseudo-count, then cap it while holding the neutral
   mean and planner fixed.
3. **Only acquisition policy transfers.** A safe order of public probing can be
   reusable even when all outcome predictions reset. Strongest rebuttal: the
   existing canonical planner may already encode the useful invariant, leaving
   no learned policy headroom. Cheapest test: transfer only public harm-rate and
   safe-margin policy statistics; delete all result-prediction state.

## Fixed experiment

- Training/search/qualification assignments are committed before results in
  `packet_assignments.json`; all are new dev-only worlds.
- Candidate order is M1, M2, M3. No fourth candidate is allowed.
- Training budget: 96 public actions/world. Evaluation budget: 96.
- Early AUC: steps 1-48; late AUC: steps 49-96.
- Gap curve checkpoints: 8, 16, 24, 32, 48, 64, 80, 96.
- Confidence cap: 2.0 equivalent observations; uncapped is a fixed comparison.
- Search gate and qualification gate are identical to the task-card gate.
- Qualification is single-use and is not run unless search passes.
- The latent-alignment arm can read evaluator mapping only to bound
  representation; its rows are labelled private and excluded from every gate.

## Decision rule

Select among passing candidates by: larger early headroom recovery, then more
positive worlds, then smaller worst-world early loss. Freeze source, packet,
thresholds and selected slow-state bytes before one qualification run. If no
candidate passes, stop with the exact bounded negative verdict and retain the
within-world Bayesian product default.
