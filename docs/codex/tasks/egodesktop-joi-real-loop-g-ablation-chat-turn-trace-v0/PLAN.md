# EgoDesktop Joi Real-Loop G-ABLATION Chat-Turn Trace v0 Plan

## Goal

Produce at least one default-off chat-turn trace row through the actual EgoDesktop renderer-to-main IPC path.

## Current Layer

Engineering implementation / default-off evidence-hygiene only.

## Files

- Modify `EgoDesktop/src/main.js` to expose the explicit smoke prompt in renderer config.
- Modify `EgoDesktop/viewer/renderer.js` to run the smoke prompt through `window.egoDesktop.sendChatTurn` before
  `reportReady`.
- Add `EgoDesktop/tests/joi_real_loop_g_ablation_chat_turn_trace.test.js`.
- Add artifacts under `artifacts/egodesktop_joi_real_loop_g_ablation_chat_turn_trace_v0/`.
- Update task board and generated lane index.

## Steps

1. Write failing static tests proving:
   - `main.js` exposes `joiRealLoopChatSmokeText` only from an explicit argument.
   - `renderer.js` calls `window.egoDesktop.sendChatTurn` for that explicit smoke text.
   - `renderer.js` includes `joiRealLoopChatSmoke` in the renderer-ready payload.
2. Run the targeted test and confirm failure for missing wiring.
3. Add the smallest main config field and renderer smoke call.
4. Run the targeted test and confirm pass.
5. Run `npm test` in `EgoDesktop`.
6. Run Electron smoke with `JOI_REAL_LOOP_*` flags plus `--joi-real-loop-chat-smoke-text`.
7. Read `trace_runner_report.json` and `trace_rows.jsonl`; require `trace_row_count > 0`.
8. Update `STATUS.md`, task board, route-convergence views, and outbox if GitHub sync is unavailable.
9. Run `git diff --check`, `python scripts/codex/verify_repo.py --mode fast`, and scoped closeout.
10. Send Claude a repair/review packet if needed, then commit only scoped files.

## Stop Conditions

- The Electron path cannot produce `trace_rows.jsonl`.
- The implementation needs a second trace logic path.
- The implementation requires default runtime enablement.
- The implementation requires program-state, evidence-ledger, EgoOperator runtime, gate, approval, memory, transport, or
  proactive changes.

## Claim Ceiling

`egodesktop_real_loop_g_ablation_chat_turn_trace_contract_only`.
