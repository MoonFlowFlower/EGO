# EGO-V2-P1-FACTORED-PREDICTIVE-CONTROL-REPAIR-001B

## Bounded task card

- **Problem definition:** the default-off factored predictive controller in
  001A collapses to `turn_left`.  In the declared world-52/policy-711 context
  it executed 528 action ticks as `turn_left`, ignored a resource directly in
  front 24 times, and produced zero resource interactions.  Its fixed action
  templates and modal successor are not the predeclared expected-distribution
  beam search.
- **Current layer:** Layer 3 mechanism hypothesis implemented under Layer 4
  learning/adaptation measurement; product capability lane with
  `science_weight=0`.
- **Current stage:** clean source boundary
  `db030d8e7536870ffa79a861b16e0e88f5795dcb`; 001A remains a frozen negative
  implementation boundary.
- **Mainline target:** the existing
  `PlaygroundController.dispatch -> engine.compute_step -> transition_world ->
  metabolism -> SQLite commit/recovery` path.  No second selector, reducer,
  controller, store, or replay path is allowed.
- **Enabled-state requirement:** product remains `enabled=true`,
  `default_enabled=false`; `predictive_control_mode=off` remains the default.
- **Real-trigger evidence requirement:** smoke and effect evidence must use the
  real controller/SQLite path with recorded trigger source and no operator
  injection.
- **Hypothesis:** bounded equal-access exploration plus a real deterministic
  expected-distribution beam over an episode-relative belief map can prevent
  one-action collapse, learn visible-token consequences, and turn prediction
  improvement into resource acquisition and survival improvement.
- **Strongest baseline:** visible-token empirical lookup plus map search.  Also
  compare heuristic OFF, predictor no-update, shield-only, and frozen Expected
  SARSA.
- **Ablation requirement:** predictor no-update shares the same exposure
  schedule.  If the candidate is positive, rerun horizon-one, no-map, equal
  goal context, rest-only, and deterministic uniform-random controls.
- **Trace/replay requirement:** record exploration exposure, expected beam
  expansion/retention, root-action coverage, probability-mass checks, value
  decomposition, model/belief/exploration hashes, and update receipts.  Fresh
  process recovery must recompute equal state and trace bytes.
- **Computed-evidence provenance gate:** every metric records producer,
  inputs, run/seed/context IDs, aggregation rule, and code-path hash.  Balanced
  prediction evaluation scores all five counterfactual actions from frozen
  snapshots using canonical evaluator-only transitions.  Leakage scanning has
  positive controls.
- **Acceptance gate:** pass the ten structural/numeric tests, then the two
  consumed-context four-life smoke runs.  Only then consume worlds 60--65
  crossed with policy seeds 721/722.  Apply the operator-provided survival,
  resource, baseline, replay, and Phase-A performance thresholds without
  post-result tuning.
- **Claim ceiling:** at most replayable prediction learning and bounded
  adaptation within the declared 16-life distribution.  Structural repair is
  not adaptation evidence.
- **Stop condition:** stop before fresh seeds if collapse, missing five-action
  coverage, missing learned resource interaction, replay drift, leakage,
  hidden-state dependence, second-path creation, or Phase-A performance
  regression occurs.  Stop default-off on no-update/lookup equivalence.
- **Rollback plan:** reverse only uncommitted 001B hunks.  Do not reset, clean,
  migrate, delete, or rewrite earlier artifacts or databases.
- **Expected changed files:** this card and collision record;
  `labs/ego_life_playground_v0/predictive_control.py`; bounded integration in
  `engine.py`, terminal/UI rendering, focused tests, one callable verifier,
  and `artifacts/EGO-V2-P1-FACTORED-PREDICTIVE-CONTROL-REPAIR-001B/`.
- **Forbidden changes:** route state, `AGENTS.md`, active context, `STATUS.md`,
  `PROGRAM_STATE*`, `**/state.json`, validators, ITL, world/resource/metabolism
  rules, network/LLM, hidden-object visibility, historical artifacts, and any
  second product/replay path.
- **Auto-Remote-Anchor:** forbidden.  Local commits only; no push or tag.

## Fixed repair contract

Exploration uses only action exposure counts, visible front tokens, run seed,
episode/sequence identifiers, and belief hash.  It gives every atomic action
four real exposures and every visible front token two `interact` exposures,
then yields to MPC.  Predictor freezing keeps model parameters unchanged while
retaining the equal-access exposure schedule.

MPC uses horizon 12 and one global width-16 beam.  Each retained node expands
all five actions, propagates the complete predicted outcome distribution over
relative pose/facing, preserves at least one node per root action, and never
samples.  Its extrinsic step value is survival plus goal-weighted homeostatic
improvement; map information value is fixed at 0.20 times newly observable
unknown fraction.  Action cost and resource gain are not double-counted
outside predicted organism deltas.

## Post-result routing

Structural failure closes as `REPAIR_FAILED_POLICY_COLLAPSE`.  A structurally
valid controller without bounded adaptation closes as
`FACTORED_CONTROL_REPAIRED_NO_ADAPTATION`.  Lookup/shield equivalence closes as
`ADAPTATION_OBSERVED_NO_PRODUCT_HEADROOM`.  Even a positive effect result keeps
the mode default-off and may only propose a separate enablement card.
