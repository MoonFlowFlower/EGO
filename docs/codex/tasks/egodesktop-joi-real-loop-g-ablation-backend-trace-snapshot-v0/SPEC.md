# EgoDesktop Joi Real-Loop G-ABLATION Backend Trace Snapshot v0 Spec

- task_id: `EGODESKTOP-GABLATION-006`
- status: `active`
- created_at: `2026-06-26`
- owner: `Codex`
- layer: `engineering implementation / backend trace snapshot wiring`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `false_by_default`
- real_trigger_evidence: `none_yet_for_this_slice`
- claim_ceiling: `egodesktop_real_loop_g_ablation_backend_trace_snapshot_contract_only`
- auto_remote_anchor: `forbidden`

## Problem Definition

`EGODESKTOP-GABLATION-005` correctly blocks 004 rows because they contain placeholder creature state, placeholder adapter
output, collect-only replay policy, and no LLM replay id. The next valid slice is not a baseline or attribution verdict.
The next valid slice is to connect a source-limited snapshot from the real EgoOperator desktop backend turn into the
existing 004 trace row surface, without creating a second chat-turn logic path and without renaming provider metadata or
trace hashes as an LLM replay id.

## Bounded Audit

- real objective: replace placeholder state/adapter row surfaces with a snapshot from the same real desktop backend turn.
- strongest baseline explanation: existing desktop shim plus LLM output still explains the visible behavior; a backend
  snapshot is not replay recomputation or causal attribution.
- strongest invalidity risk: fabricating replay readiness by calling a trace hash an `llm_replay_id`.
- falsifier for this framing: if rows are produced by any runner that bypasses `window.egoDesktop.sendChatTurn` or
  `runtime.handle_user_message`, the slice is invalid.
- insufficient evidence: source-only tests without a real Electron chat-turn smoke row, or a report that removes blockers
  by weakening the evaluator.
- task type: evidence-hygiene integration only, not mechanism validation.
- hard-coding check: snapshot hashes must be derived from the runtime trace record written by the backend turn.
- leakage check: snapshot/adapter fields must avoid runtime-authority keys and future/verdict leakage fields.
- second-logic-path check: driver may invoke the real renderer IPC path; it must not reimplement chat-turn internals.
- stop condition: any need to default-enable flags, mutate runtime authority, update program state/evidence ledger, or
  assert a baseline/attribution verdict.

## Mainline Target

The only mainline-facing target is the already existing default EgoDesktop renderer IPC chat-turn path. Under explicit
`JOI_REAL_LOOP_G_ABLATION=1` flags, the backend script may write a per-turn trace-store record and return a sanitized
snapshot to the main process. The trace runner then records that snapshot through the existing `recordChatTurn` call.

## Enabled-State Requirement

Default behavior must remain inert. With no `JOI_REAL_LOOP_G_ABLATION=1` flag, the backend must not create the G-ABLATION
backend trace file, the trace runner must not write rows, and the normal desktop chat-turn return shape must remain
compatible.

## Real-Trigger Evidence Requirement

Acceptance requires a local Electron smoke that invokes the renderer path:

- `window.egoDesktop.sendChatTurn(...)`
- `ipcMain.handle("ego-desktop:chat-turn", ...)`
- `scripts/ego_operator_desktop_turn.py`
- `runtime.handle_user_message(...)`
- existing `joiTraceRunner.recordChatTurn(...)`

and produces rows under:

- `artifacts/egodesktop_joi_real_loop_g_ablation_backend_trace_snapshot_v0/trace/trace_rows.jsonl`

The new row must have `trace_row_count > 0`, non-placeholder `creature_state.state_source`, non-placeholder
`adapter_output.adapter_status`, and no fabricated `llm_replay_id`. Its evidence label is
`schema_valid_collect_only_snapshot`; it does not satisfy 001C section 12 because replay recomputation from complete
serialized state plus observation is not implemented.

## Hypothesis

If the desktop backend is instrumented only through a flag-gated trace-store tap around the same real
`runtime.handle_user_message` call, then 005-style evaluation over the new rows should remove the placeholder blockers
while preserving replay blockers for collect-only policy and absent LLM replay id.

## Strongest Baseline

Same-access reproducer and static replay baselines still explain any visible behavior. This slice may only improve row
provenance; it must not score, compare, or promote those baselines.

## Ablation Requirement

No condition battery or same-access reproducer run is authorized. The only contrast is evaluator blocker reduction:
placeholder blockers should disappear only when the row is backed by a real backend trace snapshot, while replay verdicts
remain blocked if no true replay contract exists.

## Trace / Replay Requirement

- reuse the 003/004 trace writer and `trace_rows.jsonl` format;
- write backend snapshot fields as row state/adapter inputs, not a second trace format;
- keep `replay_policy: trace_runner_v0_collect_only` unless real replay recomputation exists;
- set `llm_replay_id` only from a true backend replay id field, not from provider metadata, response text, row hash, or
  trace record hash;
- if no true LLM replay id exists, preserve `llm_replay_id: none`.

## Computed-Evidence Provenance Gate

The slice must record:

- producer function for snapshot/evaluator;
- input trace path;
- row count;
- runtime trace record hash;
- source hashes;
- evaluator blocker list after the smoke row is produced.

## Acceptance Gate

- Task card and mutation scope exist before implementation.
- Tests are written first and fail before implementation.
- Backend snapshot helpers hash the real trace-store record and expose a sanitized source-limited state snapshot.
- Main-process trace runner call passes backend snapshot and adapter output at the existing chat-turn result boundary.
- Default-off behavior remains no-op.
- Electron smoke produces at least one `schema_valid_collect_only_snapshot` row with non-placeholder state and adapter
  output; this row does not satisfy 001C section 12 while replay remains collect-only.
- Evaluator over the new rows keeps `blocked_unreplayable_runtime_trace`, removes placeholder blockers, and preserves
  replay blockers such as `collect_only_replay_policy` and `missing_llm_replay_id` when no true replay id exists.
- `npm test` from `EgoDesktop` passes.
- `python scripts/codex/verify_repo.py --mode fast` passes.
- Scoped closeout is run and any mutation-scope configuration limitation is reported instead of being hidden.

## Claim Ceiling

`egodesktop_real_loop_g_ablation_backend_trace_snapshot_contract_only`.

This can prove only that explicit flags can collect `schema_valid_collect_only_snapshot` rows through the existing
chat-turn path. It cannot prove replay readiness, 001C section 12 conformance, baseline superiority, route advancement,
product benefit, stable user benefit, durable memory efficacy, runtime integration safety, agency, real emotion,
subjectivity, consciousness, alive status, or Bar-2 specialness.

## Rollback Plan

Delete this task directory and artifacts, remove `EGODESKTOP-GABLATION-006` from `Tasks/TASK_BOARD.yaml`, remove the
backend snapshot helper/test changes, revert the narrow main-process trace payload additions and evaluator report wording
clarification, and regenerate route-convergence views.

## Expected Changed Files

- `scripts/ego_operator_desktop_turn.py`
- `tests/test_ego_operator_desktop_trace_snapshot.py`
- `EgoDesktop/src/joiRealLoopGAblationReplayEvaluator.js`
- `EgoDesktop/src/joiRealLoopGAblationTraceRunner.js`
- `EgoDesktop/src/main.js`
- `EgoDesktop/tests/joi_real_loop_g_ablation_backend_snapshot.test.js`
- `artifacts/egodesktop_joi_real_loop_g_ablation_backend_trace_snapshot_v0/`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-backend-trace-snapshot-v0/*`
- `docs/codex/tasks/TASK_LANE_INDEX.md`
- `Tasks/TASK_BOARD.yaml`

## Forbidden Changes

- No default runtime enablement.
- No `PROGRAM_STATE_UNIFIED.yaml` update.
- No evidence-ledger claim update.
- No EgoOperator memory, gate, approval, transport, proactive, planner, model-training, or operator-trial mutation.
- No direct creature action, user message send, schedule, memory write, gate decision, approval, or runtime registration.
- No second chat-turn logic path.
- No baseline tournament, same-access verdict, route advancement, or product/readiness wording.
- No fabricated `llm_replay_id`.
- No push, tag, or remote anchor from this card.

## Next Minimal Closed-Loop Action

Write failing tests for sanitized backend trace snapshot helpers, adapter-output construction, main-process payload wiring,
default-off behavior, and evaluator blocker reduction; then implement the smallest backend trace-store tap and rerun a
single explicit Electron chat-turn smoke.
