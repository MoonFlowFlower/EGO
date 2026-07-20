# EGO-V2-P1-SURVIVAL-EXPECTED-SARSA-001A

## Problem definition

Ego V2 currently selects an action from per-step heuristic, model, and memory
scores.  The current product path does not carry a multi-step action-value
estimate across lives.  This task adds a bounded, replayable survival learner
without adding a second controller, reducer, store, transition function, or UI
computation path.

## Current layer and stage

- Layer: 4, learning/adaptation engineering in the product capability lane.
- Stage: local bounded V2 development.
- `science_weight`: `0`.
- This is not a science Gate and does not adjudicate an EGO mechanism theory.

## Mainline target

`PlaygroundController.dispatch -> engine.compute_step -> transition_world ->
compute_metabolism_ledger -> SQLiteEventStore.append/recover_run` remains the
single product execution chain.  The learner may be invoked only by
`compute_step`; UI surfaces may render only recovered state and trace data.

## Enabled-state requirement

- Existing product core: `enabled=true`, `default_enabled=false`.
- Learner mode values: `off` and `expected_sarsa_lambda`.
- Learner default: `off` until the predeclared product-effect checks pass.
- `update_mode=frozen` must prohibit learner state updates.

## Real-trigger evidence requirement

At least one test and the product-effect runner must execute the explicit user
dispatch path, commit commands and transitions to SQLite, recover the run from
initial state plus commands, and compare the independently recomputed learner
state and trace receipts.  Direct unit tests are necessary but insufficient for
mainline-effect claims.

## Hypothesis

Across 16 lives in the predeclared layouts and seeds, Expected SARSA(lambda)
using only policy-visible observations and energy can learn action values whose
late-life survival exceeds early-life survival and the admitted controls.

## Fixed implementation contract

- Algorithm: Expected SARSA(lambda).
- `alpha=0.20`, `gamma=0.99`, `lambda=0.80`.
- Q initialization: zero.
- Reward: `1.0` when `energy_after > 0`, otherwise `0.0`.
- Epsilon: `max(0.05, 0.30 * 0.85 ** (life_index - 1))`.
- State key inputs: `policy_observation_hash` and rounded milli-energy only.
- Q value is the primary selection criterion; existing candidate
  `total_score` breaks Q ties only.
- Exploration is selected by a deterministic digest of run seed, episode,
  command sequence, and state key.
- Terminal death and the tick-256 censor do not bootstrap and clear eligibility.
- Q values and visit counts persist across respawn.
- No user-tunable learning hyperparameters are added.

## Strongest baseline and shortcut explanations

The strongest cheap explanations are the existing heuristic, rest-only,
uniform random, no-update, a one-step death shield, and empirical experience
lookup.  A match by no-update or lookup prevents a learning claim.  A match by
shield-only prevents default enablement of the more complex learner.

## Ablation requirement

The callable product-effect runner must compare:

1. learner off / existing heuristic;
2. learner policy with updates disabled (`no-update`);
3. rest-only;
4. uniform-random;
5. one-step shield-only; and
6. empirical lookup fit on lives 1-8 and held constant on lives 9-16.

Each control must receive the same observation/action access appropriate to its
definition.  Controls must not read hidden object coordinates, causes, token
maps, future observations, or precomputed answers.

## Trace and replay requirement

- State persists `survival_learner` with Q, eligibility, visits, and counters.
- Per-step trace records only the selected action learner receipt, the five
  current Q values, update scalars, and full-state hashes; it does not copy the
  entire Q table.
- Run metadata records algorithm, hyperparameters, `max_lives=16`, and code path
  hash.
- `SQLiteEventStore.recover_run` recomputes from serialized initial state and
  commands; stored learner receipts are not trusted.
- Tampered Q state, TD receipt, or transition trace must be rejected even if a
  caller recomputes the outer trace hash.
- Existing four-life databases are rejected by schema/code-path mismatch; no
  migration or rewrite is permitted.

## Computed-evidence provenance gate

Every reported metric must be emitted by a callable producer and record:
producer function, input artifacts, run ID, layout/world seed, policy seed,
episode/command identifiers, aggregation rule, and code path hash.  Leakage
scanning requires a real positive-control failure.  All twelve predeclared
contexts must be consumed exactly once per candidate/control configuration.

## Product-effect acceptance gate

Contexts are the Cartesian product of:

- `p0_cross_v1`: world seeds 30 and 31;
- `p2_vertical_v1`: world seeds 42 and 43;
- `p2_offset_v1`: world seeds 44 and 45;
- policy seeds 701 and 702.

Each run has 16 lives and forbids operator injection.  Define:

- `early = mean(lives 1..4 survival_ticks) / 256`;
- `late = mean(lives 13..16 survival_ticks) / 256`;
- equivalence band `0.05`.

Default enablement requires every condition below:

1. aggregate `late - early > 0.05`;
2. at least 9/12 contexts have a positive direction;
3. late survival exceeds learner-off and no-update by more than `0.05`;
4. disabling updates reduces the advantage by at least `0.05`;
5. aggregate late survival exceeds 38 ticks;
6. late resource interactions exceed early resource interactions;
7. empirical lookup does not match within the equivalence band; and
8. fresh-process replay is equal with no unused seed/context.

If shield-only matches, retain only explicit learner mode and report
`ADAPTATION_OBSERVED_NO_PRODUCT_HEADROOM`.  If no-update/lookup matches or the
learning curve is absent, keep the learner default off and report
`PRODUCT_SURVIVAL_LEARNING_NOT_OBSERVED`.  No post-result parameter tuning is
permitted in this task.

## Engineering acceptance gate

Tests must cover the numerical update and eligibility decay, deterministic
exploration replay, off/frozen update behavior, cross-respawn persistence,
terminal eligibility clearing, life 15 respawn versus life 16 terminal,
SQLite recomputation and tamper rejection, leakage positive control, unchanged
resource/metabolism fail-closed behavior, and a single action/transition path.
All relevant V2 tests and the repository test suite must be run after focused
tests.

## Claim ceiling

At most, this task may report a replayable product adaptation signal within the
fixed 16-life layouts and seeds.  If the acceptance conditions fail, it may only
report the bounded negative result and engineering availability of an explicit
mode.

## Stop conditions

Stop rather than widen scope if implementation requires route-state changes,
schema authority changes outside the V2 product schema, a second controller or
reducer, hidden-object access, resource-rule changes, weakening existing
assertions, rewriting historical artifacts, discarding user work, or
post-result tuning.  A non-deterministic `transition_world` or a legal resource
interaction regression is also a stop.

## Rollback plan

Reverse only uncommitted hunks introduced by this task.  Do not reset, clean,
rewrite commits, delete databases, or modify historical artifacts.

## Expected changed paths

- `docs/codex/tasks/EGO-V2-P1-SURVIVAL-EXPECTED-SARSA-001A.md`
- `docs/codex/tasks/ego-v2-p1-survival-expected-sarsa-001a/COLLISION_RECORD.md`
- `labs/ego_life_playground_v0/survival_learning.py`
- focused V2 engine/controller/store/UI modules that carry the existing path
- focused V2 tests and current verifier sources
- `artifacts/EGO-V2-P1-SURVIVAL-EXPECTED-SARSA-001A/` generated by callable
  verification

## Forbidden changes

No changes to route-state artifacts, `STATUS.md`, `PROGRAM_STATE*`, any
`state.json`, validators, ITL, historical artifacts, network/LLM integration,
hidden-object visibility, resource rules, goal arbitration, or unrelated UI.

## Git boundary

- Branch: `codex/ego-v2-survival-learning-001a`.
- A scoped local commit is permitted after acceptance/readback.
- Auto-Remote-Anchor: forbidden.
- Push and tag are forbidden.
