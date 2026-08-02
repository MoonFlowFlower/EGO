# Preregistration

## Frozen data layers

- `training_dev`: 16 worlds; only public histories may train the hierarchical
  global prior.
- `search_dev`: 16 worlds; may diagnose implementation and benchmark capacity.
- `qualification`: 16 new task-local worlds, consumed once only after search
  passes and candidate freeze exists.
- `replication`: 16 further new task-local worlds, also consumed once.
- The four feature-combination pools are disjoint. Qualification and replication
  combinations never occur in either dev layer.

## Frozen physical and Bayesian constants

- Five public binary factors and three simultaneously visible slots.
- Forty shared mechanism hypotheses; evaluator mechanism index 17.
- Local modes: normal with probability 0.75, full reversal with probability
  0.25.
- Candidate 1 public feedback noise values were `[-0.01, 0.0, +0.01]` with
  probabilities `[0.25, 0.50, 0.25]`; its failed grammar and rows are retained.
- Candidate 2, the last permitted search candidate, changed only noise-support
  overlap: energy values `[-0.14,-0.07,0,+0.07,+0.14]`, safety values
  `[-0.12,-0.06,0,+0.06,+0.12]`, and probabilities
  `[0.10,0.20,0.40,0.20,0.10]` on both axes.
- Initial energy/safety `0.50/0.50`; target `0.72`.
- Passive energy decay `0.008`; interact cost `0.004`; rest cost `0.002` and
  safety delta `+0.015`.
- Evaluation budget 48; early window 1-24; late window 25-48.
- Planner minimizes posterior expected next deficit plus terminal risk minus
  finite-horizon information value. It marginalizes all live hypotheses and
  never MAP-selects evaluator truth.

## Fixed feature-combination split

- training-dev indices: `0,1,2,3,4,5,8,9,16,17,30,31`
- search-dev indices: `6,10,18,29`
- qualification indices: `7,12,14,19,21,24,26,28`
- replication indices: `11,13,15,20,22,23,25,27`

Every index is the five-bit public feature vector encoded as an integer. The
integer index is evaluator metadata and never candidate input.

## Budget and stop rule

At most two search-dev grammar candidates are allowed. The second may exist only
to repair a demonstrated capacity or wiring defect before any candidate freeze;
the first result must remain in the trial registry. Qualification and
replication cannot be tuned or rerun. Failure leaves the learner unauthorized.
