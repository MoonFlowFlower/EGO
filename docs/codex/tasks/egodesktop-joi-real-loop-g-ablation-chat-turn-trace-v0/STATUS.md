# EgoDesktop Joi Real-Loop G-ABLATION Chat-Turn Trace v0 Status

- status: `pass__default_off_chat_turn_trace_row_written_local_smoke`
- task_id: `EGODESKTOP-GABLATION-004`
- claim_ceiling: `egodesktop_real_loop_g_ablation_chat_turn_trace_contract_only`
- mainline_connected: `false`
- enabled: `false_by_default`
- real_trigger_evidence: `electron_smoke_chat_turn_trace_row`
- runtime_authority: `none`
- claude_reviewer_status: `NO_BLOCKING_FINDINGS__framing_only_source_limited`

## Current Result

The default-off chat-turn trace smoke is implemented. It adds a narrow explicit `joi-real-loop-chat-smoke-text` config
surface, has the renderer invoke `window.egoDesktop.sendChatTurn({ userText })` before `renderer-ready`, and lets the
existing main-process `joiTraceRunner.recordChatTurn(...)` hook write `trace_rows.jsonl`.

## Claude Reviewer Readback

External Claude review returned `NO_BLOCKING_FINDINGS` for the 004 framing. The reviewer explicitly noted that their
read was source-limited and anchored on the approved 001C contract plus Codex readback, not direct EGO file access.

Codex local readback after receiving the review confirms the relevant current seams:

- real renderer chat path calls `window.egoDesktop.sendChatTurn({ userText })`;
- the 004 smoke path also calls `window.egoDesktop.sendChatTurn({ userText: config.joiRealLoopChatSmokeText })`;
- main process handles `ipcMain.handle("ego-desktop:chat-turn", ...)`, builds the real `desktopTurn`, then calls
  `joiTraceRunner.recordChatTurn(...)`;
- `joiTraceRunner.recordChatTurn(...)` appends to the existing 003 `trace_rows.jsonl` sink;
- flag-off tests assert the source does not self-enable `JOI_REAL_LOOP_G_ABLATION`.

The reviewer status applies only to 004 rows-only framing and does not authorize baseline/replay verdicts or 005+
attribution claims.

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

The next bounded slice has been executed as `EGODESKTOP-GABLATION-005`: callable replay/leakage preflight over produced
trace rows. It intentionally blocks verdict claims until real CreatureState/adapter snapshots and LLM replay ids are
available.

## What This Does Not Prove

This does not prove real-loop effect, runtime integration safety, product benefit, stable user benefit, durable memory
efficacy, live autonomy, agency, real emotion, subjectivity, consciousness, alive status, route advancement, or Bar-2
specialness.
