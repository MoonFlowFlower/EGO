# EgoDesktop Joi Real-Loop G-ABLATION Chat-Turn Trace v0 Spec

- task_id: `EGODESKTOP-GABLATION-004`
- status: `active`
- created_at: `2026-06-26`
- owner: `Codex`
- layer: `engineering implementation / default-off chat-turn trace evidence`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `false_by_default`
- real_trigger_evidence: `none_yet_for_this_slice`
- claim_ceiling: `egodesktop_real_loop_g_ablation_chat_turn_trace_contract_only`
- auto_remote_anchor: `forbidden`

## Problem Definition

`EGODESKTOP-GABLATION-003` proved only that a default-off trace runner can collect renderer-ready metadata through the
Electron smoke path. It did not run a user chat turn and did not produce `trace_rows.jsonl`. The next valid slice is a
default-off chat-turn trace smoke that uses the actual EgoDesktop renderer-to-main IPC path:

`renderer -> window.egoDesktop.sendChatTurn({ userText }) -> ipcMain ego-desktop:chat-turn -> joiTraceRunner.recordChatTurn(...) -> trace_rows.jsonl`.

This task does not authorize baseline evaluation, route-B verdicts, default product enablement, program-state updates,
or evidence-ledger updates.

## Bounded Audit

- real objective: produce at least one replay-oriented chat-turn trace row from the actual EgoDesktop IPC path.
- strongest baseline explanation: current shim/backend behavior, renderer idle, static replay, or same-access
  reproducer can explain any row; this slice only produces rows for later evaluation.
- strongest invalidity risk: accidentally adding a second trace path that bypasses the real renderer IPC, or treating a
  smoke row as a causal verdict.
- falsifier for this framing: if Electron cannot honestly invoke `window.egoDesktop.sendChatTurn` under explicit flags,
  the slice must stop as `blocked_missing_real_loop_entrypoint`.
- insufficient evidence: a unit test calling `recordChatTurn()` directly is not enough for this slice; it must produce a
  local artifact from Electron or a narrow equivalent around the renderer IPC seam.
- task type: tests trace collection only, not mechanism validity or behavioral specialness.
- hard-coding check: prompt text may be deterministic and replay-locked, but verdict/scoring must not be hard-coded.
- leakage check: no runtime authority fields, no memory writes, no transport, no gate/approval, no proactive channel.
- stop condition: no `trace_rows.jsonl`, no `trace_row_count > 0`, or any need to weaken the 002/003 contracts.

## Mainline Target

The target is an explicit experiment-only local smoke path. Default user behavior must remain unchanged unless a
runner-specific explicit flag/argument is present together with the existing `JOI_REAL_LOOP_*` contract flags.

## Enabled-State Requirement

The chat-turn smoke must remain inert unless:

- the existing `JOI_REAL_LOOP_G_ABLATION=1` contract is valid;
- `JOI_REAL_LOOP_LLM_MODE=replay_locked`;
- `JOI_REAL_LOOP_TRACE_DIR`, `JOI_REAL_LOOP_CONDITION`, `JOI_REAL_LOOP_PROMPT_PACK`, and `JOI_REAL_LOOP_SPLIT` are set;
- a local runner prompt input such as `--joi-real-loop-chat-smoke-text` is explicitly supplied.

## Real-Trigger Evidence Requirement

Acceptance requires a local Electron run that writes:

- `trace_rows.jsonl` with at least one row;
- `trace_runner_report.json` with `trace_row_count > 0`;
- a smoke report that records the chat-turn trace smoke status;
- no default runtime enablement, no authority fields, and no side-effect claims.

## Hypothesis

If the renderer invokes `window.egoDesktop.sendChatTurn` during an explicit smoke run before `renderer-ready`, then the
already-wired main-process trace runner can write a real chat-turn trace row without a second logic path.

## Strongest Baseline

The strongest expected explanation for any output is current EgoDesktop/EgoOperator behavior under the same public
inputs. This slice must keep the row baseline-ready but must not evaluate same-access, static replay, or causal
attribution.

## Ablation Requirement

This slice may run only one condition such as `CURRENT_SHIM`, but it must preserve all condition labels inherited from
`EGODESKTOP-GABLATION-002`/003 and must not remove or weaken later `CREATURE_ON`, static replay, heldout replay,
same-access, or diagnostic controls.

## Trace / Replay Requirement

The row must be produced by `EgoDesktop/src/joiRealLoopGAblationTraceRunner.js`, which in turn must call
`buildJoiRealLoopTraceRow`. The new smoke path must not duplicate trace-row construction or verdict logic.

## Computed-Evidence Provenance Gate

The report must record callable producer paths and source hashes through the existing trace runner. Hand-written scores,
static verdict dictionaries, and unconditional clean reports are forbidden.

## Acceptance Gate

- Task card and mutation scope exist before runtime edits.
- Tests are written first and fail before implementation.
- Default behavior stays unchanged when the new smoke argument is absent.
- The renderer path calls `window.egoDesktop.sendChatTurn`, not `recordChatTurn` directly.
- The main process still routes chat-turn trace rows through the existing trace runner.
- Electron smoke with explicit chat-turn trace flags produces `trace_rows.jsonl` and `trace_row_count > 0`.
- `npm test` from `EgoDesktop` passes.
- `python scripts/codex/verify_repo.py --mode fast` passes.
- Scoped closeout reports no unsafe dirty paths.

## Claim Ceiling

`egodesktop_real_loop_g_ablation_chat_turn_trace_contract_only`.

This can prove only that a default-off local smoke path can produce at least one bounded chat-turn trace row through the
actual EgoDesktop IPC path. It cannot prove real-loop effect, route-B pass/reopen/close, product benefit, stable user
benefit, durable memory efficacy, runtime integration safety, agency, real emotion, subjectivity, consciousness, alive
status, or Bar-2 specialness.

## Rollback Plan

Delete this task directory and artifacts, remove `EGODESKTOP-GABLATION-004` from `Tasks/TASK_BOARD.yaml`, revert the
narrow smoke/config/renderer/test changes, and regenerate route-convergence views.

## Expected Changed Files

- `EgoDesktop/src/main.js`
- `EgoDesktop/viewer/renderer.js`
- `EgoDesktop/tests/joi_real_loop_g_ablation_chat_turn_trace.test.js`
- `artifacts/egodesktop_joi_real_loop_g_ablation_chat_turn_trace_v0/`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-chat-turn-trace-v0/*`
- `docs/codex/tasks/TASK_LANE_INDEX.md`
- `Tasks/TASK_BOARD.yaml`
- `artifacts/task_board/outbox.jsonl` if GitHub Project sync is unavailable

## Forbidden Changes

- No default runtime enablement.
- No `PROGRAM_STATE_UNIFIED.yaml` update.
- No evidence-ledger claim update.
- No EgoOperator memory, gate, approval, transport, proactive, planner, model-training, or operator-trial mutation.
- No direct creature action, user message send, schedule, memory write, gate decision, approval, or runtime registration.
- No baseline/replay verdict evaluation in this slice.
- No route-B pass/reopen/close wording.
- No push, tag, or remote anchor from this card.

## Next Minimal Closed-Loop Action

Write failing tests for the explicit chat-turn trace smoke wiring, then implement the smallest config/renderer smoke
path that drives `window.egoDesktop.sendChatTurn` and lets the existing trace runner write rows.
