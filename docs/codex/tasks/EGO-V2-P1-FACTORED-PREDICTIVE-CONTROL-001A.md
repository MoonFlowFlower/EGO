# EGO-V2-P1-FACTORED-PREDICTIVE-CONTROL-001A

## Bounded task card

- **Problem definition:** the existing product policy combines one-step
  hand-written predictions, goal scoring, memory bias, and an Expected SARSA
  option.  It does not expose a separately testable learned outcome predictor
  and short-horizon value evaluation loop.  Implement an explicit default-off
  factored mode without adding another controller, world transition, store, or
  replay path.
- **Current layer:** Layer 3 mechanism hypothesis implemented under Layer 4
  learning/adaptation measurement.  This is a product capability task with
  `science_weight=0`.
- **Current stage:** Phase A runtime scaling is locally committed at
  `b72467f229475a5c5602de5c4064b5438429846f` and its declared runtime checks
  pass.  Phase B begins from that boundary.
- **Mainline target:** the existing
  `PlaygroundController.dispatch -> engine.compute_step -> transition_world ->
  metabolism -> SQLite commit/recovery` flow.  `compute_step` remains the only
  caller of the new prediction/control module.
- **Enabled-state requirement:** product axis remains `enabled=true` and
  `default_enabled=false`.  Add
  `predictive_control_mode={off,factored_mpc}` with `off` as the run default.
  `factored_mpc` and Expected SARSA may not both control action selection.
- **Real-trigger evidence requirement:** a callable verifier must exercise the
  explicit product controller using `ui_run_button` commands over all declared
  contexts.  UI/terminal may render recovered trace data only.
- **Hypothesis:** a relative observation-derived belief state, a
  goal-independent online outcome predictor, and deterministic bounded
  trajectory evaluation can produce replayable cross-life prediction updates
  and better late-life survival than equal-access controls in the declared
  contexts.
- **Strongest baseline:** empirical lookup with the same visible inputs and
  update history.  Other controls are current heuristic/learner off, existing
  Expected SARSA, predictor no-update, horizon one, no relative map, equal goal
  context, rest-only, uniform-random, and one-step shield-only.
- **Ablation requirement:** every ablation reruns complete episodes through the
  same controller/reducer/store flow.  At least one of no-update, no-map, or
  horizon-one must reduce the declared advantage by at least 0.05.  No-update
  or lookup equivalence blocks a learning claim.
- **Trace/replay requirement:** trace records bounded belief/model hashes,
  five first-action values, three planned actions, prediction errors, and the
  update receipt.  Fresh-process recovery must recompute equal state and trace
  bytes from initial state plus commands.  Stored trace is comparison-only.
- **Computed-evidence provenance gate:** each score records producer function,
  input artifacts, run ID, policy/world/context IDs, aggregation rule, and
  code-path hash.  Baselines are independently callable.  Leakage scanning
  includes a real positive control.  Every declared context must be consumed.
- **Acceptance gate:** use old contexts only for regression and the new 12
  contexts `p0_cross_v1:{52,53}`, `p2_vertical_v1:{54,55}`,
  `p2_offset_v1:{56,57}` crossed with policy seeds `{711,712}` for effects.
  Require all nine effect checks in the operator plan, exact goal
  counterfactual separation, replay equality, and continued Phase A
  performance.  Passing engineering tests alone is insufficient.
- **Claim ceiling:** at most replayable prediction learning and bounded product
  adaptation within the declared 16-life distribution.  A negative result is
  an admissible boundary and must not be tuned into a pass.
- **Stop condition:** stop with a default-off result if no-update/lookup match,
  heldout prediction does not improve, the survival curve fails, a hard shield
  explains the result, predictor inputs require private world fields, Phase A
  performance regresses, a second state-transition path is required, or scope
  would touch route/state authority, network, LLM, UI world visibility, or
  resource/metabolism rules.
- **Rollback plan:** reverse only uncommitted Phase B hunks.  Do not reset,
  clean, migrate, delete, or rewrite prior databases or artifacts.
- **Expected changed files:** this card and its collision record; a focused
  `labs/ego_life_playground_v0/predictive_control.py`; bounded integration in
  `engine.py`, `terminal.py`, and `visual_console.py`; focused tests; one
  callable verifier and one new task artifact directory.
- **Forbidden changes:** route-state artifacts, `AGENTS.md`,
  `docs/ACTIVE_CONTEXT_PACK.md`, `STATUS.md`, `PROGRAM_STATE*`, `**/state.json`,
  validators, ITL, network/LLM code, hidden-object visibility, world RNG,
  resource/metabolism rules, a second controller/reducer/store/replay path,
  historical artifacts, and the old temporary SQLite database.
- **Auto-Remote-Anchor:** forbidden.  Local commits only; no push or tag.

## Fixed implementation contract

The factored mode consumes only the 5x5 policy observation, organism variables,
episode-local relative belief, selected actions, and observed transition/self
receipts.  It must not consume global coordinates, hidden objects, cause/token
mapping, future observations, world seed, life identity, or precomputed answer
labels.

The predictor is goal-independent.  Goal context can change only value weights
and action ranking.  The same belief/action prediction bytes must remain equal
under a goal counterfactual.  Planning uses `horizon=12`, `beam_width=16`, and
`discount=0.97`, expands expected distributions deterministically, and emits
only the existing five atomic actions.

## Post-result routing

If all declared effect checks pass, this task may propose a separate card to
consider changing the run default.  This task itself leaves the new mode off.
If a cheap control matches, preserve the replayable negative result and close
without parameter search.
