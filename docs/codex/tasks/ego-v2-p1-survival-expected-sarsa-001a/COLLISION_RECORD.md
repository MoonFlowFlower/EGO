# Collision record: EGO-V2-P1-SURVIVAL-EXPECTED-SARSA-001A

## Real objective

Determine whether a policy-visible, multi-step value update carried across
lives changes survival behavior beyond current heuristics, lookup, no-update,
or a cheap death shield, while preserving the existing product execution and
SQLite recomputation path.

## Candidate comparison

### Candidate 1: one-step Q-learning

- Evidence it could produce: replayable one-step action-value updates and a
  survival curve.
- Strongest cheap match: current heuristic plus a one-step danger penalty.
- Leakage/hard-coding risk: high if the max-Q target amortizes a narrow layout
  or if state contains hidden coordinates.
- Smallest falsifier: no-update or shield-only matches its late survival within
  `0.05`.
- Expected failure: bootstrapping over optimistic unvisited actions produces
  unstable or shield-like behavior rather than multi-step credit assignment.

### Candidate 2: Expected SARSA(lambda)

- Evidence it could produce: on-policy expected targets, multi-step eligibility
  propagation, deterministic replay, and cross-life Q persistence.
- Strongest cheap match: empirical cue/action lookup or shield-only under equal
  visible access.
- Leakage/hard-coding risk: exact observation hashes may memorize recurring
  views; life/seed/coordinates in the state key would invalidate the result.
- Smallest falsifier: eligibility ablation/no-update leaves the advantage
  unchanged, lookup matches, or late survival does not exceed early survival.
- Expected failure: sparse exact states and a 16-life budget may provide too
  little repeated experience for the trace to generalize.

### Candidate 3: learned transition model plus planning

- Evidence it could produce: counterfactual multi-step forecasts and planned
  action selection.
- Strongest cheap match: transition-table lookup or hand-coded shortest-path
  planning.
- Leakage/hard-coding risk: very high; a planner could reconstruct hidden world
  geometry or create a second state-transition logic path.
- Smallest falsifier: a same-access transition table matches it, or replay uses
  any transition function other than the existing product world transition.
- Expected failure: added model/planner complexity obscures whether any effect
  comes from learning, planning, or privileged world reconstruction.

## Selection

Candidate 2 is selected because it is the smallest option that tests multi-step
credit assignment while remaining compatible with deterministic event replay.
Candidate 1 is too easily explained by a single-step guard.  Candidate 3 is
premature and risks a second world-model path.

## Strongest reason the framing may be invalid

The exact visual-observation hash plus milli-energy may make experience sparse,
so 16 lives may be insufficient.  Conversely, repeated layouts may let a cheap
lookup match the learner.  Either outcome prevents a product-learning claim;
it is not repaired by threshold or hyperparameter tuning in this task.

## Evidence still insufficient

A greener survival curve alone is insufficient.  Unit-test correctness,
rendered UI output, Q-table growth, or a few longer lives do not distinguish
learning from exploration luck, heuristic tie-breaking, lookup, or shielding.
The callable controls, update ablation, leakage scan, and fresh-process replay
are required.

## Anti-hardcoding and split-path audit

- State key accepts only the policy observation hash and rounded energy.
- The exploration digest may schedule randomness but may not enter the learned
  state.
- Q decides first; current heuristic is used only for exact Q ties.
- Resource causes/tokens, object coordinates, future observations, life ID, and
  seed ID are excluded from learner state.
- `compute_step` is the only caller allowed to select with or update the learner.
- `transition_world`, metabolism, controller, store, and recovery remain the
  existing implementations.
- UI consumes recovered receipts and performs no learning computation.
- The effect runner may inject a policy control only through the same callable
  selection interface; it may not implement another reducer.

## Acceptance signal and downgrade rules

The numerical and replay engineering gates must pass first.  Product default
enablement then requires all eight predeclared effect conditions in the task
card.  Shield equivalence keeps the mode explicit-only.  No-update/lookup
equivalence or a missing learning curve keeps default off and records bounded
negative evidence.

## Claim ceiling

Only adaptation measured in the stated layouts, seeds, 16-life horizon, and
callable product path may be reported.  This record does not support general
reinforcement learning, transfer, subjectivity, agency, consciousness,
autonomy, emotion, or electronic-life claims.
