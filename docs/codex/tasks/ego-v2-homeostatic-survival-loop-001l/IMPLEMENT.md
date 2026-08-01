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
