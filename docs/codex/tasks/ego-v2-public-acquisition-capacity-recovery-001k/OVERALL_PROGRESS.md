# 001K research campaign progress

- Last updated: 2026-08-01
- Program goal: identify and repair the legal public acquisition bottleneck
  without touching 001J formal evidence or its heldout assignments.
- Current stage goal: freeze the best legal 96-action candidate and all gates,
  then execute the precommitted qualification packet exactly once.
- Stage success criteria: source/config/dependencies/packet hashes and
  thresholds are frozen before execution; qualification rows independently
  reproduce metrics; ablations damage any gain; no packet identity reaches the
  candidate.
- Reviewer verdict: `needs_more_exploration`
- Validated evidence: 001J stored rows show 1,405/1,536 public actions were
  turns, only 64 were successful interactions, and no world identified all
  five tokens within 96 actions. This is diagnostic evidence, not yet a causal
  adjudication.
- Validated call-chain evidence: all 001J hashes match; AST order is
  plan -> transition -> actual outcome -> metabolism -> update; a synthetic
  public state intervention changed the final selected action. The posterior is
  connected, but its use may still be defective.
- S1 observability evidence: full public history learned a mean 58.75% of
  evaluator-scored effect signs but remained worse than random
  (`gain=-0.04666`). No-update and feedback-shuffle were also negative. Giving
  the unchanged legacy planner the correct evaluator-only posterior produced
  only `gain=0.00796`, `recovery=1.51%`, `6/16` positive directions, and an even
  higher `95.70%` turn fraction. Thus correct effects alone do not recover the
  headroom.
- S3 wiring evidence: changing only front-diagonal geometry reduced turns from
  `92.90%` to `48.37%`, raised successful interactions from `4.0` to `20.75`,
  learned all five token signs, and produced `gain=0.16377`,
  `recovery=31.09%`, `14/16` positive directions. Target retention and the
  alternate deficit-ranking rule were weaker. Posterior-ranking ablation fell
  to `recovery=11.28%` and `7/16`, so learned ranking contributes, but S3 did
  not reach the unchanged 50% gate.
- S2 acquisition/budget evidence: the same legal geometry reference recovered
  `25.11%`, `31.09%`, and `43.46%` headroom at 48/96/192 actions respectively.
  More time helps, but does not by itself reach 50%. At the unchanged 96-action
  horizon, changing only unknown-token information value produced
  `gain=0.24011`, `recovery=45.58%`, and `15/16` positive directions. This is
  the best search candidate, but remains below the admission gate and is not a
  success claim.
- Current blocker: none.
- Next frontier: freeze `S2_RISK_INFORMATION_GAIN` without further search-dev
  tuning, commit the freeze, and run qualification once with three action RNG
  seeds plus no-update, feedback-shuffle, and posterior-ranking ablations.
