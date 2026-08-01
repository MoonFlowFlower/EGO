# EGO-V2-CAUSAL-SPROUT-DEMO-001A

## Bounded task contract

- **Task ID:** `EGO-V2-CAUSAL-SPROUT-DEMO-001A`.
- **Status:** implementation authorized; heldout not yet committed or revealed.
- **Layer:** local explicit V2 product/mechanism demo; `science_weight=0`.
- **Repository:** `D:\Project\AIProject\MyProject\Ego`.
- **Branch:** `codex/ego-v2-causal-sprout-demo-001a`.
- **Base HEAD:** `144782376baf74c4e01519b9cf019d949e3d7f2c`.
- **Preflight status:** clean index and worktree; `git diff` and
  `git diff --cached` empty before this card; no overlapping worktree.
- **Auto-Remote-Anchor:** forbidden. No push, tag, or remote anchor.
- **Protected surfaces:** do not modify `intelligence-theory-lab`, `joi-demo`,
  or any 001C--001I task card, artifact, verdict, or reserved science seed.

## Readback and current unique runtime chain

The active product authority permits a local bounded V2 source task while
keeping the runtime explicit/default-off, local-only, network/LLM/background
disabled, and `science_weight=0`.

The current sole V2 chain read back from source is:

```text
scripts/run_ego_life_playground_v0.py
  -> SQLiteEventStore
  -> PlaygroundController.dispatch
  -> engine.make_command + engine.compute_step
  -> SQLiteEventStore.append_step (atomic command + trace readback)
  -> PlaygroundController incremental committed frame
  -> SQLiteEventStore.recover_run
       recomputes engine.compute_step from initial state + commands
       before reading each stored trace
  -> TerminalPlayground / PlaygroundWindow render recovered controller frames
```

The nursery extension must reuse `PlaygroundController` and
`SQLiteEventStore`, with a task-local reducer adapter invoked identically by
live dispatch and store recovery. It may not add a second store, a second
controller, or a render-owned behavior path.

## Problem definition

Build a minimal recurrent neural learner which receives only public
observations and its own action/outcome history, acts in a private
programmatically generated nursery, updates from experience, persists and
replays exactly, and is evaluated under interventions that distinguish a
mechanism-relevant signal from a correlated nuisance signal.

**Prediction becoming more accurate is not, by itself, causal learning.** The
maximum admissible result requires all preregistered intervention, transfer,
ablation, baseline-parity, replay, and leakage gates below.

## Competing candidates and collision decision

### A. Token/outcome lookup

- **Role:** mandatory equal-access surface baseline.
- **Evidence it can produce:** fit on repeated public feature/action tokens.
- **Strongest objection:** it can look excellent while merely caching the
  training correlation and cannot establish mechanism-sensitive transfer.
- **Smallest discriminator:** correlation reversal plus unseen feature/action
  composition and feature/glyph permutation.
- **Decision:** retain as the invalidating baseline C must beat.

### B. Hand-written causal graph / if-else selector

- **Role:** evaluator-only task-solvability reference.
- **Evidence it can produce:** the nursery is solvable when hidden mechanism
  truth is available.
- **Strongest objection:** success is authored into the selector, not learned;
  it is not a candidate and cannot support a learning claim.
- **Smallest discriminator:** scan inputs/code and reject any policy branch on
  hidden channel/mapping, feature names, glyphs, context class, or verdict.
- **Decision:** upper-bound reference only; never used to select candidate
  actions, targets, updates, or thresholds.

### C. Recurrent neural causal learner

- **Role:** sole tested learner.
- **Evidence it can produce:** update- and history-dependent action-conditioned
  predictions that remain stable to nuisance interventions and respond to
  mechanism interventions on frozen unseen compositions.
- **Strongest objection:** an RNN can still memorize surface correlations or
  context order; recurrence and nonlinear weights do not make a causal method.
- **Smallest discriminator:** equal-access lookup/feed-forward/no-update/
  shuffled-feedback controls plus correlation reversal, complete feature/glyph
  permutation, local mechanism shift, update freeze, and history reset.
- **Decision:** selected. If C does not beat A and the strongest equal-access
  invalidating control, the verdict must be
  `SURFACE_FIT_BASELINE_EQUIVALENCE` or `INCONCLUSIVE`, never causal learning.

## Public/private boundary

Learner-visible fields are exactly:

- `feature_a`
- `feature_b`
- `local_state`
- `energy`
- `last_action`
- `last_observed_delta`

Private evaluator/environment fields include mechanism channel and mapping,
context namespace, split, schedule, oracle outcome, and verdict. None may
enter learner or equal-access baseline inputs.

Development contexts use strings `causal_sprout_dev_*`; the single frozen
heldout block uses strings `causal_sprout_heldout_*`. These are a distinct
namespace, not the formal microworld integer world-seed namespace. No formal
seed in 30--150, 60--65, 721/722, or any reserved value above 150 is consumed.

## Frozen learner family and controls

- NumPy-only `TinyCausalRNN`, tanh state, hidden size 24.
- Deterministic initialization and serializable RNG state.
- One-step truncated BPTT online SGD with serialized momentum buffers.
- Public observation + prior action/outcome/history input.
- Per-action predicted organism delta, terminal-risk estimate, and generic
  action-value logits.
- Planner score is predicted survival value plus learned policy/value head;
  label-specific and token-specific if/else policy rules are forbidden.
- Generic exploration is allowed and disclosed. Learned active experiment
  design is explicitly outside this card.

Equal-access controls receive the same public rows in the same order:

1. no-update neural network;
2. feed-forward neural network without recurrent history;
3. feature/action lookup;
4. nearest neighbour;
5. surface-only predictor;
6. shuffled-feedback learner;
7. random policy;
8. simple Bayesian causal reference (solvability upper bound only);
9. hidden ground-truth oracle (evaluator upper bound only);
10. constant/predict-all and predict-none equivalents.

## Preregistered evidence and gates

All eight conditions are required for the maximum claim:

1. nuisance-only paired intervention invariance;
2. mechanism-variable paired intervention sensitivity;
3. correlation-reversal generalization;
4. unseen feature/action composition;
5. update-freeze ablation destroys the gain;
6. recurrent-history reset damages the history-required subset;
7. equal-access surface controls do not reproduce the effect;
8. trace/replay recomputes action, prediction, and update from serialized
   pre-state plus public observation, never stored action/prediction/outcome.

Frozen minimum demo gate before heldout reveal:

- candidate heldout interventional MSE <= `0.75` times the strongest
  surface/no-update invalidating control MSE;
- nuisance-only prediction change <= `0.20` of true causal-effect range;
- mechanism-intervention effect-sign accuracy >= `0.80`;
- the same loss/invariance/sensitivity conditions survive correlation reversal
  and complete feature/glyph permutation;
- update-freeze destroys at least `0.50` of the candidate gain;
- history reset increases loss on the hidden-history subset by at least `0.20`
  relative;
- replay and independent row recomputation match within absolute tolerance
  `1e-10`;
- all leakage positive controls are rejected.

Failure mapping is fixed:

- access/leakage/replay/tamper defect -> `INVALID_EVIDENCE`;
- strongest surface/no-update control matches candidate ->
  `SURFACE_FIT_BASELINE_EQUIVALENCE`;
- valid packet but one or more scientific gates fail -> `INCONCLUSIVE`;
- only all gates passing -> `BOUNDED_CAUSAL_REGULARITY_LEARNED`.

Thresholds, hyperparameters, baselines, generator, sample counts, stopping rule,
and source/test bytes must be committed into a freeze manifest before the
heldout context commitment is derived. The heldout block may be run once; its
result must not be used to retune and rerun the same packet.

## TDD order and acceptance

Required order:

```text
readback -> collision record -> task card -> failing tests -> nursery
-> baseline solvability -> neural learner -> persistence/replay
-> visualization -> dev run -> freeze -> one heldout run
-> row recomputation -> hostile self-review
```

Tests must prove real learner/baseline calls, optimizer mutation, finite-
difference gradient positive control, real rerun ablations, leakage-scanner
positive controls, stored-action independence, trace/weight/context tamper
fail-closed behavior, and HTML data provenance from the trace reducer.

## Expected mutation surface

- this task card, collision record, and task-local mutation scope;
- `labs/ego_life_playground_v0/causal_sprout.py`;
- minimal adapter hooks in `controller.py` and `store.py`, plus package exports;
- `scripts/run_ego_causal_sprout_demo.py`;
- a task-local verifier and its tests;
- task-local product tests;
- only `artifacts/EGO-V2-CAUSAL-SPROUT-DEMO-001A/*` evidence outputs.

No generated authority view, product-axis state, legacy card, or other repo is
in the mutation surface.

## Claim ceiling

If and only if every frozen gate passes, the maximum claim is:

> A small recurrent neural learner learned, from public interaction history in
> a predefined causal nursery, an action-conditioned mechanism regularity that
> was stable to named nuisance interventions and beat specified surface-fitting
> controls on one frozen heldout block.

This cannot establish real-world causal understanding, general causal
reasoning, learned active experiment design, AGI, consciousness, subjectivity,
emotion, agency, autonomy, electronic life, user benefit, or the same capability
in the ordinary Ego runtime.
