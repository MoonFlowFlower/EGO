# IMPLEMENT — EGO V2 homeostatic survival loop 001L

## Expected mutation surface

See `MUTATION_SCOPE.yaml`. Runtime changes are limited to a new learner module,
the existing reducer/launcher/visual projection, exports, and focused tests.
Research changes are task-local scripts, verifier, docs, and new artifacts.

## Implementation constraints

- Use pinned NumPy environment where campaign tests require it.
- Write tests before runtime integration.
- Never import the 001K campaign runner from product runtime; extract a clean,
  versioned public-state implementation.
- The existing controller must persist commands/traces and recover by calling
  the same reducer.
- Stored selected action/prediction/outcome are evidence only, never replay
  behavior input.
- Each experiment updates `EXPLORE.md`, experiment ledger and scorecard before
  the next experiment.

## Verification floor

Focused unit tests, current V2 microworld/playground tests, 001K frozen tests,
route-state validation, `git diff --check`, task-local scope guard, direct
terminal command, SQLite recovery, verifier, and artifact-manifest readback.

## Closeout readback

- Sole live path remains `launcher -> controller.dispatch -> engine.compute_step
  -> store.append_step`; recovery recomputes the same reducer.
- Default-off `public_bayes` learns legal-public current-world token/action
  consequences and exposes deficits, predictions, uncertainty, action reason,
  actual delta, update receipts and fast/slow/posterior hashes.
- A 48-step direct terminal run learned all five anonymous token effect signs
  (`1.0` evaluator accuracy) and was fully replayed from SQLite; trace JSONL and
  trace-derived HTML are task artifacts.
- The R successor passed both unchanged formal gates (`59.83%` and `55.52%`
  recovery), independent row recomputation and all tamper/leakage controls.
- The minimal slow-prior learner failed both bounded search attempts, so its
  `two_timescale` posterior is non-default and product qualification was not
  consumed. The default experimental posterior remains `canonical`.
- Regression readback: `62 passed`; route convergence: `pass`; scope guard:
  no unexpected path; protected 001J/001K bytes unchanged.
