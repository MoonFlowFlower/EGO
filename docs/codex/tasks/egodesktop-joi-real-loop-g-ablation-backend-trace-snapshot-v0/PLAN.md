# EgoDesktop Joi Real-Loop G-ABLATION Backend Trace Snapshot v0 Plan

1. Add task card, mutation scope, and status shell for `EGODESKTOP-GABLATION-006`.
2. Add failing tests for backend snapshot sanitization, adapter-output construction, main-process trace payload wiring,
   default-off no-op behavior, and evaluator blocker reduction.
3. Add a flag-gated backend trace-store tap in `scripts/ego_operator_desktop_turn.py` around the existing
   `runtime.handle_user_message` call.
4. Pass the sanitized backend snapshot and adapter output through the existing `joiTraceRunner.recordChatTurn` call in
   `EgoDesktop/src/main.js`.
5. Run a single explicit Electron chat-turn smoke and store rows under
   `artifacts/egodesktop_joi_real_loop_g_ablation_backend_trace_snapshot_v0/`.
6. Run the replay/leakage evaluator over the new rows and record expected blocked replay status with placeholder blockers
   removed.
7. Update task board/status and regenerate route-convergence views.
8. Run focused tests, `npm test`, Python helper tests, route/repo checks, scoped closeout, and commit locally only.

## Non-Goals

- No baseline score or same-access reproducer execution.
- No attribution, route, or readiness verdict.
- No default EgoDesktop runtime enablement.
- No program-state or evidence-ledger update.
- No fabricated LLM replay id.
