# EgoDesktop Joi Real-Loop G-ABLATION Chat-Turn Trace v0 Status

- status: `pass__default_off_chat_turn_trace_row_written_local_smoke`
- task_id: `EGODESKTOP-GABLATION-004`
- claim_ceiling: `egodesktop_real_loop_g_ablation_chat_turn_trace_contract_only`
- mainline_connected: `false`
- enabled: `false_by_default`
- real_trigger_evidence: `electron_smoke_chat_turn_trace_row`
- runtime_authority: `none`
- claude_reviewer_status: `pending`

## Current Result

The default-off chat-turn trace smoke is implemented. It adds a narrow explicit `joi-real-loop-chat-smoke-text` config
surface, has the renderer invoke `window.egoDesktop.sendChatTurn({ userText })` before `renderer-ready`, and lets the
existing main-process `joiTraceRunner.recordChatTurn(...)` hook write `trace_rows.jsonl`.

The local Electron smoke with explicit `JOI_REAL_LOOP_*` flags produced:

- `artifacts/egodesktop_joi_real_loop_g_ablation_chat_turn_trace_v0/trace/trace_rows.jsonl`
- `artifacts/egodesktop_joi_real_loop_g_ablation_chat_turn_trace_v0/trace/trace_runner_report.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_chat_turn_trace_v0/smoke/live2d_desktop_smoke_report.json`

The trace report records `trace_row_count: 1`. The smoke report records `live2d_desktop_smoke_pass` and
`joiRealLoopChatSmoke.status: chat_turn_trace_smoke_pass`.

## Verification

- Red check: `node --test EgoDesktop\tests\joi_real_loop_g_ablation_chat_turn_trace.test.js` failed before
  implementation because main/renderer smoke wiring was absent.
- Green check: `node --test EgoDesktop\tests\joi_real_loop_g_ablation_chat_turn_trace.test.js` passed: `2 passed`.
- `npm test` from `EgoDesktop` passed: `75 passed`.
- Electron smoke with explicit `JOI_REAL_LOOP_*` flags and `--joi-real-loop-chat-smoke-text` exited `0` and produced one
  chat-turn trace row.

## Current Blocker

No callable baseline/replay verdict evaluation exists in this slice. The trace row still uses the placeholder creature
state/adapter output from the trace runner, so this is trace-row production only, not causal-path attribution.

## Next Minimal Closed-Loop Action

Create the next bounded slice for callable replay/baseline evaluation over produced trace rows. Start with replay
integrity and positive-control leakage checks before any same-access or route-B verdict logic.

## What This Does Not Prove

This does not prove real-loop effect, runtime integration safety, product benefit, stable user benefit, durable memory
efficacy, live autonomy, agency, real emotion, subjectivity, consciousness, alive status, route-B pass/reopen/close, or
Bar-2 specialness.
