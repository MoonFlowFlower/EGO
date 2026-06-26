# EgoDesktop Joi Real-Loop G-ABLATION Replay/Leakage Evaluator v0 Plan

1. Add task card, mutation scope, and status shell for `EGODESKTOP-GABLATION-005`.
2. Add failing Node tests for replay-integrity hash recomputation, leakage positive control, placeholder replay blocking,
   and report underclaiming.
3. Implement `joiRealLoopGAblationReplayEvaluator.js` as a pure artifact evaluator.
4. Add an explicit CLI wrapper that reads 004 `trace_rows.jsonl` and writes evaluator reports.
5. Run the evaluator over 004 artifacts and store reports under
   `artifacts/egodesktop_joi_real_loop_g_ablation_replay_leakage_evaluator_v0/`.
6. Update task board/status and regenerate route-convergence views.
7. Run focused tests, `npm test`, route/repo checks, scoped closeout, and commit locally only.

## Non-Goals

- No baseline score or same-access reproducer execution.
- No route verdict.
- No default EgoDesktop runtime integration.
- No program-state or evidence-ledger update.
