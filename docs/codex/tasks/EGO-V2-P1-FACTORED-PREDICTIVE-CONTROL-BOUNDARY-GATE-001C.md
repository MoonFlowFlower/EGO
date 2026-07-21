# EGO-V2-P1-FACTORED-PREDICTIVE-CONTROL-BOUNDARY-GATE-001C

## Bounded task card

- **Problem definition:** the 001B controller removed the all-`turn_left`
  collapse, but its old-context smoke failed two product boundaries: recovery
  took 14.97--18.62 seconds and mean trace size was 33.0--33.1 KiB.  Balanced
  five-action prediction was therefore not evaluated.  Repair these boundaries
  without changing the declared MPC behavior, then measure prediction quality
  over all five actions on the already-consumed smoke contexts.
- **Current layer:** Phase A is Layer 2 engineering/evidence hygiene.  Phase B
  is Layer 4 bounded learning/adaptation measurement.  This is a product
  capability task with `science_weight=0`.
- **Current stage:** clean source boundary
  `7d5744af225f40d541f8960f64e345b7fe657bb6` on
  `codex/ego-v2-factored-predictive-control-repair-001b`.
- **Mainline target:** preserve the existing
  `PlaygroundController.dispatch -> engine.compute_step -> transition_world ->
  metabolism -> SQLite commit/recovery` flow.  No alternate selector, reducer,
  controller, store, checkpoint, or replay implementation is allowed.
- **Enabled-state requirement:** product remains `enabled=true` and
  `default_enabled=false`; `predictive_control_mode=off` remains the default.
- **Real-trigger evidence requirement:** old-smoke evidence must use controller
  dispatch and SQLite with recorded trigger source and no operator injection.
- **Hypothesis:** changing repeated mapping/hash work to one fixed-order numeric
  representation per planning call, plus removing redundant trace payloads,
  can meet recovery and trace limits while preserving actions, transitions,
  metabolism, learning updates, and MPC values.
- **Strongest baseline:** trace-only compression can meet the byte limit but
  cannot repair recovery.  Reading stored plans or checkpoints can appear fast
  only by weakening independent recomputation.  Reduced horizon/beam can appear
  fast only by changing the tested controller.
- **Ablation requirement:** balanced evaluation must compare the learned
  predictor with an independently callable zero-initialized no-update predictor
  on exactly the same pre-action snapshots.  A selected-action-only score is a
  diagnostic and cannot satisfy the gate.
- **Trace/replay requirement:** a fresh process must recompute state, trace,
  five-action predictions, and aggregate metrics from initial state plus stored
  commands.  Tampering with command, trace, model, prediction, or update data
  must be rejected even after recomputing the row trace hash.
- **Computed-evidence provenance gate:** every result records producer function,
  input artifacts, run/context/seed/life/action identifiers, aggregation rule,
  and code-path hash.  The leakage scanner must run real positive controls.
- **Acceptance gate:** first pass old-smoke semantic equivalence, online timing,
  recovery, trace, SQLite, replay, tamper, and single-path checks.  Only then run
  balanced five-action evaluation.  Fresh effect contexts remain unexecuted.
- **Claim ceiling:** at most old-smoke runtime/replay boundary evidence and
  balanced five-action predictor-error change within worlds 52/54 and policy
  seed 711.  It is not fresh-distribution survival evidence.
- **Stop condition:** stop before balanced evaluation if semantics drift, any
  boundary threshold fails, replay diverges, leakage is detected, a second
  path is required, or the existing Tk regression worsens.  Stop before fresh
  effects for every 001C verdict.
- **Rollback plan:** reverse only uncommitted 001C hunks.  Do not reset, clean,
  migrate, delete, or rewrite earlier artifacts or databases.
- **Expected changed files:** this card and its collision record; one V2
  dependency pin; bounded changes in `predictive_control.py` and `engine.py`;
  focused 001C tests; one callable 001C verifier; and only the new 001C artifact
  directory.
- **Forbidden changes:** route-state files, `AGENTS.md`, active context,
  `STATUS.md`, `PROGRAM_STATE*`, `**/state.json`, validators, ITL, UI, controller,
  store, world/resource/metabolism rules, network/LLM, hidden-object visibility,
  historical artifacts, and fresh effect runs.
- **Auto-Remote-Anchor:** forbidden.  Local commits only; no push or tag.

## Fixed engineering contract

- NumPy is pinned to `2.2.6`.  A missing or different version fails explicitly;
  there is no alternate planner backend.
- Planner semantics remain horizon 12, global beam width 16, five root actions,
  complete predicted outcome distributions, existing relative map, existing
  value formula, and existing deterministic tie-breaking.
- Serialized predictor weights use action/outcome/state/feature arrays in fixed
  declared order.  Run metadata records Python, NumPy, dtype, and order hashes.
- Exact action/world/metabolism/lifecycle/goal/exploration equality is required
  against the pre-change fixture.  Public prediction and value numbers may
  differ by at most `1e-12`.

## Old-smoke boundary contract

- Contexts: `p0_cross_v1/world=52/policy=711` and
  `p2_vertical_v1/world=54/policy=711`, four lives each, no injection.
- Online dispatch p95 is at most 250 ms and maximum is at most 500 ms.
- Last-32/first-32 mean duration ratio is below 2.
- Three isolated fresh-process recoveries per context are each at most 10 s.
- Mean trace is at most 32 KiB; maximum trace is at most 64 KiB.
- SQLite is at most 20 MiB.

## Balanced prediction contract

For every action tick in life 1 and life 4 of both contexts, reconstruct the
pre-action decision state and score all five actions.  Evaluator-only truth is
computed through `transition_world`, `compute_metabolism_ledger`, and the same
public actual-delta function used by the product step.  Counterfactual results
never update policy, belief, exploration, or model state.

Scores are macro-averaged across context, phase, and action.  Multiclass Brier
is the sum of squared probability error, NLL is
`-log(max(p_true, 1e-12))`, and organism-delta MAE is the mean absolute error
over four self variables.  Pass requires equal action counts, Brier improvement
of at least 0.02, NLL improvement of at least 0.05, both late metrics better
than no-update, late delta MAE below both early and no-update, clean leakage
scans with positive controls, and exact fresh-process replay.

## Verdicts

- `BOUNDARY_REPAIR_FAILED`
- `BOUNDARY_REPAIRED_PREDICTION_NOT_IMPROVED`
- `BOUNDARY_AND_BALANCED_PREDICTION_VERIFIED`
- `BLOCKED_PRECONDITION_DRIFT`
- `BLOCKED_SEMANTIC_DRIFT`

No verdict changes the default mode or permits this task to run worlds 60--65
or policy seeds 721/722.  A positive result may only set a machine-derived
eligibility flag for a separately bounded future task.
