# EgoDesktop Joi Real-Loop G-ABLATION Backend Trace Snapshot v0 Status

- status: `blocked_expected__backend_trace_snapshot_rows_written`
- task_id: `EGODESKTOP-GABLATION-006`
- claim_ceiling: `egodesktop_real_loop_g_ablation_backend_trace_snapshot_contract_only`
- mainline_connected: `false`
- enabled: `false_by_default`
- real_trigger_evidence: `electron_smoke_backend_trace_snapshot_row`
- runtime_authority: `none`
- claude_reviewer_status: `pending`

## Current Result

The backend trace snapshot slice is implemented. Under explicit `JOI_REAL_LOOP_*` flags, the real EgoDesktop renderer IPC
path invokes `window.egoDesktop.sendChatTurn(...)`, main process calls `scripts/ego_operator_desktop_turn.py`, the backend
turn writes a per-turn EgoOperator `JsonlTraceStore` record, and the existing `joiTraceRunner.recordChatTurn(...)` call
writes a row containing:

- `creature_state.state_source: ego_operator_runtime_trace_store`
- `adapter_output.adapter_status: connected_real_backend_trace_snapshot`
- `llm_replay_id: none`
- `replay_inputs.replay_policy: trace_runner_v0_collect_only`

Produced artifacts:

- `artifacts/egodesktop_joi_real_loop_g_ablation_backend_trace_snapshot_v0/trace/trace_rows.jsonl`
- `artifacts/egodesktop_joi_real_loop_g_ablation_backend_trace_snapshot_v0/trace/trace_runner_report.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_backend_trace_snapshot_v0/smoke/live2d_desktop_smoke_report.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_backend_trace_snapshot_v0/evaluator/evaluation_report.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_backend_trace_snapshot_v0/evaluator/EVALUATION_REPORT.md`

The evaluator result is intentionally still blocked:

- `status: blocked_unreplayable_runtime_trace`
- `rows_evaluated: 1`
- `hash_integrity_status: pass`
- `leakage_scan_status: pass`
- `leakage_positive_control_status: pass`
- blockers: `collect_only_replay_policy`, `missing_llm_replay_id`

The 005 placeholder blockers are removed for this 006 row, but no replay, baseline, or attribution verdict is authorized.

## Verification

- Red check: `node --test EgoDesktop\tests\joi_real_loop_g_ablation_backend_snapshot.test.js` failed before
  implementation because `buildJoiRealLoopBackendAdapterOutput` and main-process snapshot wiring were absent.
- Red check: `python -m pytest -q tests\test_ego_operator_desktop_trace_snapshot.py` failed before implementation because
  backend snapshot helper exports were absent.
- Green check: `node --test EgoDesktop\tests\joi_real_loop_g_ablation_backend_snapshot.test.js` passed: `3 passed`.
- Green check: `python -m pytest -q tests\test_ego_operator_desktop_trace_snapshot.py` passed: `3 passed`.
- Electron smoke with explicit `JOI_REAL_LOOP_*` flags and `--model-path ..\data\live2d\悠小喵\悠小喵.model3.json`
  exited `0`, produced `trace_row_count: 1`, and recorded `joiRealLoopChatSmoke.status: chat_turn_trace_smoke_pass`.
- One setup smoke invocation failed before evidence production because npm parsed `--out` as an npm config; a second setup
  invocation failed because `--model-path` was omitted. Both were discarded and rerun with the explicit model path above.
- Evaluator CLI over the 006 row exited `0` and produced the blocked-expected evaluator reports.
- Focused regression:
  `node --test EgoDesktop\tests\joi_real_loop_g_ablation_backend_snapshot.test.js EgoDesktop\tests\joi_real_loop_g_ablation_replay_evaluator.test.js EgoDesktop\tests\joi_real_loop_g_ablation_trace_runner.test.js EgoDesktop\tests\joi_real_loop_g_ablation_chat_turn_trace.test.js`
  passed: `16 passed`.
- Focused Python regression:
  `python -m pytest -q tests\test_ego_operator_desktop_trace_snapshot.py tests\test_ego_operator_desktop_session_context.py tests\test_ego_operator_desktop_recovery_context.py tests\test_ego_operator_desktop_pspc_reply_preview.py`
  passed: `59 passed`.
- `npm test` from `EgoDesktop` passed: `82 passed`.
- `python scripts\codex\verify_route_convergence.py` passed.
- `python scripts\codex\verify_repo.py --mode fast` passed.
- `git diff --check` passed.
- YAML parse check passed for `Tasks/TASK_BOARD.yaml` and the 006 mutation scope.
- Strict secret-pattern scan over the 006 docs/tests/artifacts found no API keys.
- `python scripts\codex_session_guard.py closeout-check --format markdown` was run before staging and correctly reported
  not-eligible due to `no_staged_changes`, `unsafe_dirty_paths`, `push_pending`, and `remote_sync_unavailable`.
- The same closeout check was run after scoped staging. It still reported `unsafe_dirty_paths` because the guard has no
  CLI option to load this task's mutation scope and prints `mutation_scope: not_configured`; the listed unsafe paths are
  the staged 006 docs/tests/artifacts directories and no unstaged paths remain. This is recorded as a closeout tooling
  limitation, not a code/test pass.

## Current Blocker

Rows are still unreplayable for verdict purposes because the row uses `trace_runner_v0_collect_only` replay policy and no
true LLM replay id exists. The backend trace hash and LLM metadata hash are trace identifiers only; they are not replay
contracts.

## Next Minimal Closed-Loop Action

Create the next bounded slice only if it adds real replay recomputation from serialized state plus observation, or a true
LLM replay contract. Do not add baseline verdict logic while rows remain collect-only or `llm_replay_id: none`.

## What This Does Not Prove

This does not prove replay readiness, baseline superiority, runtime integration safety, product benefit, stable user
benefit, durable memory efficacy, live autonomy, agency, real emotion, subjectivity, consciousness, alive status,
route advancement, or Bar-2 specialness.
