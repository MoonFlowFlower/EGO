# 001K research campaign progress

- Last updated: 2026-08-01
- Program goal: identify and repair the legal public acquisition bottleneck
  without touching 001J formal evidence or its heldout assignments.
- Current stage goal: campaign closed under the frozen three-stage budget.
- Stage success criteria: trial registry, qualification, replication,
  recomputation, leakage/tamper controls, failure manifest, and bounded verdict
  are all complete and independently readable.
- Reviewer verdict: `success_reached`
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
- Qualification evidence: after source/config/threshold freeze, the single-use
  qualification packet produced `gain=0.28717`, `recovery=54.29%`, `47/48`
  positive trajectory directions, and `16/16` positive world aggregates.
  Effect-sign accuracy was `1.0`; no-update, feedback-shuffle, and posterior
  ablation all exceeded the frozen material-damage threshold. Independent
  recomputation of 27,648 rows returned no findings. Verdict remains
  `QUALIFICATION_CAPACITY_ESTABLISHED_PENDING_REPLICATION`.
- Replication evidence: the unchanged candidate produced `gain=0.24223`,
  `recovery=40.95%`, `44/48` positive trajectories, `15/16` positive world
  aggregates, and `0.9625` effect-sign accuracy. All three ablations materially
  damaged gain and independent recomputation found no mismatch. Positive gain
  reproduced, but the 50% recovery gate did not.
- Integrity evidence: 55,296 formal rows independently recomputed; row,
  aggregate, assignment, and candidate-receipt tamper controls all rejected;
  all declared private input fields rejected.
- Current blocker: the unchanged M1 recovery gate was not reproduced.
- Final verdict: `POSITIVE_SIGNAL_BUT_M1_NOT_AUTHORIZED`.
- Next frontier: stop this Task ID. Use a new successor and new dev-only data to
  study packet-to-packet recovery variance; do not rerun these formal packets.
