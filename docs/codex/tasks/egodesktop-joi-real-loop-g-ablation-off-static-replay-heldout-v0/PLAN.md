# EgoDesktop Joi Real-Loop G-ABLATION OFF_STATIC_REPLAY_HELDOUT v0 Plan

1. Add task card, mutation scope, and task-board entry.
2. Add failing tests for replayable `OFF_STATIC_REPLAY_HELDOUT` non-LLM `D` row construction and evaluator precondition pass.
3. Add the minimal offline replay module and artifact builder CLI.
4. Extend the precondition evaluator to resolve the registered offline recompute callable by function id.
5. Build the row artifact from current 006 rows and run the evaluator precondition over it.
6. Update status/task board and regenerate route-convergence views.
7. Run focused tests, `npm test`, repo fast verify, scoped closeout, and commit locally only.

## Non-Goals

- No baseline scoring or same-access reproducer execution.
- No route, attribution, readiness, product, or mechanism verdict.
- No default EgoDesktop runtime enablement.
- No program-state or evidence-ledger update.
