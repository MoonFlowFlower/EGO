# Preregistration

## Frozen symbolic model

- Anonymous public tokens: `v0..v4`.
- Latent causes: `resource`, `social`, `novelty`, `threat`, `shelter`.
- Legal mappings: all 5! bijections, uniform prior.
- Likelihood uses only public action, front token, public outcome type and
  realized energy/safety delta.
- Passive observation has zero alignment likelihood ratio under the public,
  exchangeable nuisance-generation family.
- Named mapping error and behaviorally actionable effect-class error are
  reported separately.

## Frozen experiment

- `search_dev`: 16 new worlds beginning at seed 470003, stride 173.
- `replication_dev`: 16 new worlds beginning at seed 480003, stride 173.
- Layouts cycle through the three already-frozen layouts.
- No qualification split exists in this task.
- Budget: 96 public actions/world.
- Early AUC: steps 1-48; late AUC: steps 49-96.
- Gap checkpoints: 8, 16, 24, 32, 48, 64, 80, 96.
- Reliable behavioral alignment: posterior behavioral Bayes error <= 0.05.
- Candidate and thresholds freeze before either packet result is inspected.

## Arms

- `EXACT_BAYES_ADAPTIVE`: exact public mapping posterior with fixed
  risk-constrained information-aware planning.
- `SCRATCH`: existing canonical within-world public Bayesian planner.
- `EXISTING_PUBLIC_BAYES`: explicit equal-access repeat of the current public
  reference.
- `NO_POSTERIOR_UPDATE`: exact state remains at its prior.
- `FEEDBACK_SHUFFLE`: update pairing is deterministically shifted to the next
  public token.
- `NO_INFORMATION_GAIN`: posterior updates, but acquisition ranking omits
  information value.
- `PRIVATE_ALIGNED_REFERENCE`: evaluator-only diagnostic upper bound.
- `UNIFORM_RANDOM` and `PRIVATE_ORACLE_NAVIGATOR`: diagnostic bounds.

## Frozen decision rule

The exact-reference gain must be positive, recover at least 5% of the
scratch-to-private-aligned headroom, and be positive in at least 12/16 worlds on
both packets. At least one relevant public ablation must remove half the
observed gain and reduce alignment quality. Any failure yields
`PUBLIC_LATENT_ALIGNMENT_NOT_IDENTIFIABLE_OR_NOT_ECONOMIC_UNDER_CURRENT_GRAMMAR`.
No threshold is changed after packet execution.
