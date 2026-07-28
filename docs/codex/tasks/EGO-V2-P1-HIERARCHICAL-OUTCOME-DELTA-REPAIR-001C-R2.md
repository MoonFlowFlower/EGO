# EGO-V2-P1-HIERARCHICAL-OUTCOME-DELTA-REPAIR-001C-R2

## Bounded task card

- **Problem definition:** R1 replaced the unconditional organism-delta head
  with a full `[action, outcome, state, feature]` tensor.  It preserved exact
  replay, but fresh-process recovery regressed from the 001C world-52/world-54
  range of `6.23--8.56s` to `12.59--17.66s`; the frozen balanced prediction
  gate therefore did not run.  A read-only profile attributes the dominant
  cost to replaying the horizon-12 planner over the enlarged conditional head.
  Replace the sparse full interaction with a smaller, theory-grounded
  hierarchical additive delta model without changing product/world semantics
  or consuming fresh-effect contexts.
- **Prior negative evidence:**
  `EGO-V2-P1-SURVIVAL-EXPECTED-SARSA-001A` reported
  `PRODUCT_SURVIVAL_LEARNING_NOT_OBSERVED`;
  `EGO-V2-P1-FACTORED-PREDICTIVE-CONTROL-001A` reported
  `PRODUCT_PREDICTIVE_CONTROL_NOT_OBSERVED`; 001C repaired the runtime boundary
  but not organism-delta learning; R1 stopped at
  `BLOCKED_BOUNDARY_OR_REPLAY_REGRESSION`.  None of those artifacts may be
  rewritten or upgraded.
- **Current layer:** Layer 2 engineering plus Layer 4 bounded
  learning/adaptation measurement.  Product capability lane with
  `science_weight=0`.
- **Current stage:** clean successor boundary
  `ca8a33df516f4b35c81cd2c66e9c2f17cb95844b` on
  `codex/ego-v2-hierarchical-delta-repair-001c-r2`.
- **Mainline target:** preserve the sole
  `PlaygroundController.dispatch -> engine.compute_step -> transition_world ->
  compute_metabolism_ledger -> SQLite commit/recovery` path.  No controller,
  store, reducer, action, lifecycle, goal, metabolism, resource, or UI behavior
  may be added or changed.
- **Enabled-state requirement:** product stays `enabled=true` and
  `default_enabled=false`; `predictive_control_mode=off` remains the default.
- **Real-trigger evidence requirement:** development evidence uses only
  controller-dispatched, SQLite-committed worlds 52/54, policy seed 711, four
  lives each, with no injection.  Worlds 60--65 and policy seeds 721/722 are
  forbidden in this task.
- **Hypothesis:** a shared action/state feature slope plus an observed-outcome
  residual intercept is a smaller identified additive representation of
  organism delta than a fully interacted outcome-by-feature tensor. Updating
  the joint feature with normalized LMS and then applying a prediction-
  invariant sum-to-zero reparameterization should retain local outcome-shift
  capacity, reduce sparse conditional computation, restore the frozen replay
  boundary, and lower balanced late delta MAE. This task does not add residual
  shrinkage and therefore does not claim Bayesian partial pooling.
- **Method basis:** normalized least-mean-square adaptation is an established
  low-complexity adaptive linear-filter method; the update is frozen here as an
  augmented-feature NLMS step rather than invented post-result tuning.  See
  Widrow et al., *Least-Mean-Square Adaptive Filters*,
  `https://doi.org/10.1002/0471461288`.
- **Strongest baselines:** independently callable legacy unconditional delta
  learning on the same legal receipts; no-update; and the archived R1 full
  interaction result as a performance/failure boundary.  The development
  report must also disclose base-only/residual-off, residual-only, and a
  deterministically outcome-shuffled residual control.  Token-graph lookup,
  action-only metabolism, and binary front-object controls are mandatory in a
  later fresh-effect card, not claims supplied by this repair task.
- **Ablation requirement:** zero all outcome residual intercepts at evaluation
  while retaining the learned shared base; separately zero the shared base;
  and deterministically permute residual outcome labels. `update_mode=frozen`
  must preserve every predictor byte and hash.  A positive repair verdict
  requires a conditioning-sensitive metric to change and may not be supported
  by an average dominated by `no_object` rows.
- **Trace/replay requirement:** fresh-process recovery recomputes equal
  hierarchical base/residual hashes, conditional deltas, expected deltas,
  plans, state, and trace from initial state plus commands.  Stored predictions,
  parameters, plans, or checkpoints are never replay inputs.
- **Computed-evidence provenance gate:** every metric records producer,
  inputs, run/context/seed/life/action IDs, aggregation rule, and code-path
  hash.  Leakage scans retain real positive controls.  Baselines and ablations
  are callable computations, not literals.
- **Acceptance gate:** first pass numeric/shape RED tests, frozen-update tests,
  observed-outcome residual isolation tests, source-path/leakage tests,
  recovery/tamper tests, and the unchanged 001C performance/trace boundary.
  Worlds 52 and 54 must each complete three exact fresh-process recoveries at
  `<=10s`.  Only then run the frozen balanced five-action evaluation on those
  already-used contexts.  The evaluator must predict first and then force the
  declared action intervention. It must report support and macro metrics over
  every realizable pair: move_forward/moved, move_forward/blocked,
  interact/interacted, interact/no_object, rest/rested, and each turn/turned.
  Every declared stratum requires pre-update training support and evaluation
  support of at least 16 rows, and every action's shared-base feature matrix
  must report its rank against the 15-feature contract. Insufficient support
  yields `INSUFFICIENT_OUTCOME_SUPPORT`, not a positive verdict. An empty cell
  or the historical four interacted rows cannot pass. Positive
  development evidence requires macro late delta MAE below both macro early
  and macro no-update late, retained frozen Brier/NLL conditions, and a
  conditioning-sensitive ablation. Micro averages are disclosure-only.
  Sixteen is only the frozen structural floor of one row beyond the 15-column
  shared design, not a power or precision claim; rank and per-stratum support
  remain separately disclosed.
- **Eligibility output:**
  `fresh_effect_seeds_consumed=false` for every verdict.
  `eligible_for_separate_effect_card=true` only when every development gate
  passes; this task itself has no CLI path that accepts fresh-effect seeds.
- **Claim ceiling:** at most a replayable hierarchical outcome-delta
  implementation and measured improvement or failure on already-consumed
  worlds 52/54 with policy seed 711.  A positive result is not held-out
  adaptation or survival evidence.
- **Stop condition:** stop after one frozen implementation/evaluation cycle if
  the `<=10s` exact-recovery boundary fails, balanced delta does not improve,
  no-update matches, the ablation is insensitive, hidden/private fields enter
  prediction, any product/world semantic changes, a checkpoint/stored-plan
  replay shortcut appears, or a second product path is required.  Do not tune
  learning rate, thresholds, seeds, horizon, beam, features, value weights, or
  NLMS normalization after observing results.
- **Rollback plan:** reverse only uncommitted R2 hunks.  Do not reset, clean,
  migrate, delete, rewrite commits, or mutate historical tasks/artifacts.
- **Expected changed files:** this card and collision record;
  `labs/ego_life_playground_v0/predictive_control.py`; the minimal schema pins
  in `engine.py`; focused predictor/engine tests; one callable R2 verifier and
  its tests; and a new R2 artifact directory.
- **Forbidden changes:** route state, `AGENTS.md`, active context, `STATUS.md`,
  `PROGRAM_STATE*`, `**/state.json`, validators, ITL, controller, store, UI,
  world/resource/metabolism/lifecycle/goal rules, network/LLM, hidden-object
  visibility, historical artifacts, worlds 60--65, and policy seeds 721/722.
- **Auto-Remote-Anchor:** forbidden.  Local commits only; no push or tag.

## Fixed hierarchical model contract

1. Replace R1 `delta_weights[action,outcome,state,feature]` with:
   - `delta_base_weights[action,state,feature]`;
   - `delta_outcome_offsets[action,outcome,state]`.
2. For legal predictor feature vector `x`:

   ```text
   base[a,s] = dot(delta_base_weights[a,s], x)
   conditional[a,o,s] = clip(base[a,s] + delta_outcome_offsets[a,o,s], -0.35, 0.35)
   expected[a,s] = sum_o P(o | visible_state,a) * conditional[a,o,s]
   ```

3. Outcome is update receipt and evaluator-private counterfactual truth only;
   it is never a prediction-time input.
4. For selected action `a`, observed outcome `o`, state variable `s`, error
   `e = actual_delta[s] - conditional[a,o,s]`, use the augmented feature
   `z = concat(x, one_hot(o))` and the frozen joint normalized LMS step,
   followed by a pure sum-to-zero reparameterization:

   ```text
   step = LEARNING_RATE * e / dot(z,z)
   delta_base_weights[a,s] += step * x
   delta_outcome_offsets[a,o,s] += step
   mean_offset = mean(delta_outcome_offsets[a,:,s])
   delta_base_weights[a,s,bias] += mean_offset
   delta_outcome_offsets[a,:,s] -= mean_offset
   ```

   The bias feature guarantees `dot(z,z) > 0`; no epsilon or new learning-rate
   parameter is introduced. The projection leaves every conditional
   `base + offset` prediction unchanged while preserving zero-sum offsets and
   removing the intercept alias between shared bias and offsets. If the joint
   update plus prediction-invariant projection would exceed `[-4,4]`, the
   update fails closed rather than clipping different outcomes unequally.
5. Keep weight bounds `[-4,4]`, prediction clip `[-0.35,0.35]`, NumPy `2.2.6`,
   feature/action/outcome/state order, outcome softmax, horizon 12, beam 16,
   discount, exploration, action costs, and value formula frozen.
6. Compact traces store expected delta and hashes of the complete shared base
   and outcome-residual receipt; they do not serialize full tensors per node.
7. Bump predictive model/state/prediction/plan/update and dependent product
   state/run/trace/code-path schemas.  Old databases fail closed; no migration
   or fallback path is allowed.

## Verdicts

- `HIERARCHICAL_DELTA_REPAIRED_ON_DEVELOPMENT_CONTEXTS`
- `HIERARCHICAL_DELTA_REPAIRED_NO_DELTA_IMPROVEMENT`
- `INSUFFICIENT_OUTCOME_SUPPORT`
- `BLOCKED_BOUNDARY_OR_REPLAY_REGRESSION`
- `BLOCKED_PRECONDITION_DRIFT`
- `BLOCKED_SCOPE_EXPANSION`

No verdict changes the default mode or itself authorizes a fresh-effect run.
