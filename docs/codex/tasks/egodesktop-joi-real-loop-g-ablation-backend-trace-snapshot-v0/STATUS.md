# EgoDesktop Joi Real-Loop G-ABLATION Backend Trace Snapshot v0 Status

- status: `blocked_expected__backend_trace_snapshot_rows_written`
- task_id: `EGODESKTOP-GABLATION-006`
- claim_ceiling: `egodesktop_real_loop_g_ablation_backend_trace_snapshot_contract_only`
- mainline_connected: `false`
- enabled: `false_by_default`
- real_trigger_evidence: `electron_smoke_backend_trace_snapshot_row`
- runtime_authority: `none`
- claude_reviewer_status: `BLOCKING_FINDINGS_SOURCE_LIMITED__006A_REPAIRS_APPLIED_PENDING_RE_REVIEW`

## Current Result

The backend trace snapshot slice is implemented. Under explicit `JOI_REAL_LOOP_*` flags, the real EgoDesktop renderer IPC
path invokes `window.egoDesktop.sendChatTurn(...)`, main process calls `scripts/ego_operator_desktop_turn.py`, the backend
turn writes a per-turn EgoOperator `JsonlTraceStore` record, and the existing `joiTraceRunner.recordChatTurn(...)` call
writes a row containing:

- `creature_state.state_source: ego_operator_runtime_trace_store`
- `adapter_output.adapter_status: connected_real_backend_trace_snapshot`
- `llm_replay_id: none`
- `replay_inputs.replay_policy: trace_runner_v0_collect_only`

This row is now labeled `schema_valid_collect_only_snapshot`. It does not satisfy 001C section 12 because it cannot yet
recompute `D` from complete serialized state plus observation.

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

## Claude Source-Limited Blocking Findings

Claude returned `BLOCKING_FINDINGS` on the 006-to-007 packet, source-limited because it could not read the Ego repo or
artifacts. The blockers are treated as valid review gates for this lane:

1. The packet used a too-strong "conformant" label for an unreplayable row.
2. Digest / viability state cannot prove `D` replay recomputation.
3. Placeholder blocker disappearance needed a non-wording blocker-delta gate and placeholder positive control.
4. Mutation-scope closeout was called incorrectly, so the packet overstated the closeout tooling limitation.
5. The packet did not attach the previous minimal surface definition.

006A repairs applied:

- Claim label is now `schema_valid_collect_only_snapshot`; the row explicitly does not satisfy 001C section 12.
- `D_FIELD_REPLAY_PRECONDITION_007.md` freezes the 007 precondition and blocks any >=007 scoring run until complete state
  plus observation can be serialized and replayed offline for non-LLM `D`.
- `summarizeReplayBlockerDelta` plus tests provide a non-wording blocker-delta gate.
- `artifacts/egodesktop_joi_real_loop_g_ablation_backend_trace_snapshot_v0/evaluator/blocker_delta_report.json` records
  `placeholder_positive_control_status: pass`, `placeholder_removed_status: pass`, and
  `replay_blockers_preserved_status: pass`.
- `CLOSEOUT_SCOPE_READBACK_006A.md` records the correct mutation-scope command form and the latest loaded-scope readback.
- `MINIMAL_SURFACE_006.md` attaches the minimal surface for re-review.

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
- The initial scoped closeout command was invoked with the wrong argument order. Correct usage is
  `python scripts\codex_session_guard.py --mutation-scope docs\codex\tasks\egodesktop-joi-real-loop-g-ablation-backend-trace-snapshot-v0\MUTATION_SCOPE.yaml closeout-check --format markdown`.
  With the correct form, mutation scope loads and unsafe dirty paths drop to `0`; current blockers are publication-related
  or no-staged-change state, not mutation-scope failure.
- Red 006A review-repair checks:
  - `node --test EgoDesktop\tests\joi_real_loop_g_ablation_backend_snapshot.test.js` failed before implementation because
    `summarizeReplayBlockerDelta` was absent.
  - `python -m pytest -q tests\test_egodesktop_gablation_review_repair.py` failed before docs repair because the
    `conformant` wording remained and precondition/minimal-surface/closeout readback docs were absent.
- Green 006A review-repair checks:
  - `node --test EgoDesktop\tests\joi_real_loop_g_ablation_backend_snapshot.test.js` passed: `5 passed`.
  - `python -m pytest -q tests\test_egodesktop_gablation_review_repair.py` passed: `3 passed`.

## Current Blocker

Rows are still unreplayable for verdict purposes because the row uses `trace_runner_v0_collect_only` replay policy and no
true LLM replay id exists. The backend trace hash and LLM metadata hash are trace identifiers only; they are not replay
contracts.

## Next Minimal Closed-Loop Action

Send `CLAUDE_REVIEW_PACKET_006A_AFTER_BLOCKER_REPAIR.md` for re-review. Do not implement 007 until the source-limited
blockers are either cleared by Claude or narrowed to a specific local repair. If cleared, 007 may only satisfy
`D_FIELD_REPLAY_PRECONDITION_007.md`: freeze non-LLM `D` fields, serialize complete state plus observation, and prove
offline recomputation. Do not add baseline verdict logic while rows remain collect-only or `llm_replay_id: none`.

## What This Does Not Prove

This does not prove replay readiness, baseline superiority, runtime integration safety, product benefit, stable user
benefit, durable memory efficacy, live autonomy, agency, real emotion, subjectivity, consciousness, alive status,
route advancement, or Bar-2 specialness.
