# EGO-V2-P1-OUTCOME-CONDITIONED-DELTA-REPAIR-001C-R1

## Bounded task card

- **Problem definition:** 001C closed the old-context runtime/replay boundary,
  and its balanced evaluator showed improving outcome Brier/NLL, but learned
  late organism-delta MAE (`0.0064276573`) was worse than learned early
  (`0.0040698868`) and no-update late (`0.0057928571`).  The error was
  concentrated in `interact`: late MAE `0.0267254728` versus early
  `0.0087846607`.  Repair the delta predictor's factorization without tuning
  the frozen thresholds or consuming fresh-effect contexts.
- **Current layer:** Layer 2 engineering plus Layer 4 bounded
  learning/adaptation measurement.  This remains a product capability task
  with `science_weight=0`.
- **Current stage:** clean source boundary
  `6c7b9f029981e80321a4dba9020df2ee8c95e48f` on
  `codex/ego-v2-factored-predictive-control-boundary-gate-001c`.
- **Mainline target:** preserve the sole
  `PlaygroundController.dispatch -> engine.compute_step -> transition_world ->
  compute_metabolism_ledger -> SQLite commit/recovery` path.  The repair may
  change predictor estimates and therefore selected actions, but it may not
  change the atomic action set, world reducer, metabolism, lifecycle, goal
  rules, controller, store, or UI.
- **Enabled-state requirement:** product remains `enabled=true` and
  `default_enabled=false`; `predictive_control_mode=off` remains the default.
- **Real-trigger evidence requirement:** development evaluation uses only
  controller-dispatched, SQLite-committed old contexts worlds 52/54 with
  policy seed 711, four lives each, no injection.
- **Hypothesis:** the current unconditional linear delta head spreads a rare
  large `interact` receipt across `no_object` cases even though outcome and
  resource heads improve.  Predicting one delta vector per
  action-by-outcome, then using the complete predicted outcome distribution to
  compute expected self delta, will isolate rare interaction effects and
  lower balanced late delta MAE.
- **Strongest baseline:** an independently callable legacy unconditional
  linear-delta learner trained on the same visible inputs and actual receipts.
  No-update remains the zero-model control.  Outcome labels or hidden causes
  may not be supplied to prediction-time inputs.
- **Ablation requirement:** collapse the outcome-conditioned rows to an
  outcome-agnostic delta estimate at evaluation time, and verify that the
  conditioning-sensitive metric changes.  `update_mode=frozen` must leave all
  predictor weights unchanged.
- **Trace/replay requirement:** fresh-process recovery must recompute the same
  conditional-delta hashes, expected deltas, plan values, state, and trace from
  initial state plus commands.  Stored predictions or plans are never replay
  inputs.
- **Computed-evidence provenance gate:** every metric records producer
  function, input artifacts, run/context/seed/life/action identifiers,
  aggregation rule, and code-path hash.  Leakage scans retain real positive
  controls.  Baseline and ablation values come from callable computations.
- **Acceptance gate:** first pass numeric/structural RED tests, schema
  fail-closed tests, recovery/tamper tests, and the 001C performance/trace
  boundary.  Then rerun balanced five-action evaluation on the already-used
  development contexts.  Passing development evidence requires late delta MAE
  below both early and no-update late while retaining the frozen Brier/NLL
  conditions.  This task never sets fresh-effect eligibility true.
- **Claim ceiling:** at most a replayable outcome-conditioned delta-head
  implementation and measured improvement or failure on the already-consumed
  worlds 52/54, policy seed 711.  A positive development result is not heldout
  adaptation evidence.
- **Stop condition:** stop after one frozen implementation/evaluation cycle if
  conditioning does not improve the declared delta criterion, the legacy
  baseline matches it, outcome metrics regress below their frozen thresholds,
  runtime/replay boundaries fail, hidden fields enter predictor input, or a
  second product path is required.  Do not tune learning rate, thresholds,
  features, seeds, horizon, beam, or value weights after observing the result.
- **Rollback plan:** reverse only uncommitted R1 hunks.  Do not reset, clean,
  migrate, delete, rewrite earlier commits, or mutate the 001C artifact set.
- **Expected changed files:** this card and collision record;
  `labs/ego_life_playground_v0/predictive_control.py`;
  `labs/ego_life_playground_v0/engine.py`; focused predictor/engine tests; one
  callable R1 verifier and its tests; schema-pin assertions directly affected
  by the version bump; and a new R1 artifact directory.
- **Forbidden changes:** route-state files, `AGENTS.md`, active context,
  `STATUS.md`, `PROGRAM_STATE*`, `**/state.json`, validators, ITL, controller,
  store, UI, world/resource/metabolism/lifecycle/goal rules, network/LLM,
  hidden-object visibility, historical artifacts, and worlds 60--65 or policy
  seeds 721/722.
- **Auto-Remote-Anchor:** forbidden.  Local commits only; no push or tag.

## Fixed implementation contract

1. Replace the serialized delta tensor `[action, state, feature]` with
   `[action, outcome, state, feature]`, using the existing fixed action,
   outcome, state, and feature orders.
2. Each prediction computes conditional deltas for all six outcomes and then:

   ```text
   expected_delta[state]
     = sum_outcome P(outcome | visible_state, action)
                     * conditional_delta[outcome, state]
   ```

3. An update changes only the selected action and actually observed outcome's
   delta row.  It must not copy a resource receipt into `no_object` or any
   unobserved outcome row.
4. The predictor continues to consume only policy observation, organism state,
   and relative belief.  Outcome is an update receipt and evaluator-private
   counterfactual truth, never a prediction-time input.
5. Planner horizon 12, beam width 16, outcome softmax, value formula,
   exploration schedule, and deterministic numeric order remain fixed.
6. Compact product traces store the expected delta plus a hash of the complete
   conditional-delta receipt; they do not copy the full conditional tensor per
   action or beam node.
7. Bump predictive state/model/prediction/plan/update and product
   state/run/trace/code-path schemas.  Command schema remains unchanged.  Old
   databases fail closed; there is no migration or fallback implementation.

## Development evaluation contract

- Inputs: `p0_cross_v1/world=52/policy=711` and
  `p2_vertical_v1/world=54/policy=711`, four lives each, no injection.
- Every action tick in lives 1 and 4 is evaluated for all five atomic actions.
- Outcome Brier/NLL, four-variable delta MAE, equal action counts, leakage,
  frozen-update, and fresh-process replay retain the 001C definitions.
- The archived 001C result is an immutable input baseline, not rewritten
  evidence.  New evidence is written only under
  `artifacts/EGO-V2-P1-OUTCOME-CONDITIONED-DELTA-REPAIR-001C-R1/`.
- `fresh_effect_seeds_consumed=false` and
  `eligible_for_separate_effect_card=false` for every verdict.

## Verdicts

- `OUTCOME_CONDITIONING_REPAIRED_ON_DEVELOPMENT_CONTEXTS`
- `OUTCOME_CONDITIONING_REPAIRED_NO_DELTA_IMPROVEMENT`
- `BLOCKED_BOUNDARY_OR_REPLAY_REGRESSION`
- `BLOCKED_PRECONDITION_DRIFT`
- `BLOCKED_SCOPE_EXPANSION`

No verdict authorizes fresh-effect evaluation or a default-enabled change.
