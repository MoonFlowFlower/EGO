# EgoDesktop Joi Real-Loop G-ABLATION Wizard Selected Source Chat Smoke v0

- task_id: `EGODESKTOP-GABLATION-026`
- parent_task_id: `EGODESKTOP-GABLATION-025`
- status: `active`
- created_at: `2026-06-27`
- owner: `Codex`
- layer: `engineering validation / selected source desktop trigger smoke`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `explicit_smoke_flags_only`
- real_trigger_evidence: `valid_electron_ipc_sendChatTurn_trace_hash_match`
- claim_ceiling: `selected_source_desktop_trigger_smoke_only`
- auto_remote_anchor: `forbidden`

## Objective

Run one explicit EgoDesktop smoke using one predeclared `wizard_of_wikipedia_hf` source row from the refreshed 025
capture manifest, through the real `window.egoDesktop.sendChatTurn(...)` path and existing trace writer. Preserve only
hash/provenance reports and trace artifacts; do not score, compare, replay, or claim `CREATURE_ON`.

## Bounded Audit

- real objective: close the post-025 gap between hash-only Wizard row selection and a real Electron IPC desktop
  chat-turn trigger.
- strongest baseline explanation: this can still be ordinary current-shim desktop/backend behavior; there is no candidate
  mechanism comparison in this slice.
- strongest invalidity risk: if the run bypasses `window.egoDesktop.sendChatTurn(...)`, if the selected row is chosen
  post hoc, or if raw text is committed, the evidence claim is invalid.
- falsifier: missing trace row, hash mismatch between `TRIGGER_INPUT_REPORT.user_text_hash` and
  `trace_rows.jsonl.public_inputs.user_text_hash`, smoke status other than `chat_turn_trace_smoke_pass`, or raw selected
  text present in committed artifacts.
- insufficient evidence: a smoke pass alone without trace hash alignment, or a materializer report alone without the
  desktop trigger path.
- mechanism-vs-resemblance: this is only engineering trigger provenance, not mechanism evidence.
- hard-coding/leakage check: selected row is predeclared as `wizard_of_wikipedia_hf:train:0`; reports must remain
  hash-only and the ignored local source cache must not be staged.
- claim ceiling: `selected_source_desktop_trigger_smoke_only`.
- minimal validation: materializer focused tests, smoke report/trace hash alignment, artifact raw-text scan, route
  convergence, repo fast verifier, diff check, and scoped closeout.
- stop condition: smoke failure, absent trace row, hash mismatch, raw text committed, scoring/replay/same-access attempt,
  runtime enablement, program-state/evidence-ledger update, push, tag, or remote anchor.
- rollback plan: delete this task package and artifact directory, remove the task-board entry, regenerate route views, and
  keep 025 as the last accepted boundary.
- acceptance signal: hash-only trigger report for `wizard_of_wikipedia_hf:train:0`, `chat_turn_trace_smoke_pass`,
  `live2d_desktop_smoke_pass`, trace row count `1`, matching user-text hash, and
  `entrypoint_provenance.status=ipc_event_observed`.

## Task Card

- problem definition: 025 refreshed the capture manifest to include Wizard rows, but there is not yet Wizard-specific
  evidence that one predeclared selected row can traverse the real desktop chat-turn seam.
- current stage/layer: `engineering validation / selected source desktop trigger smoke`.
- mainline target: explicit local Electron smoke only, not default runtime.
- enabled-state requirement: explicit `JOI_REAL_LOOP_*` flags only.
- real-trigger evidence requirement: renderer smoke report must show `joiRealLoopChatSmoke.status=chat_turn_trace_smoke_pass`;
  trace row count must be exactly one; trace row `public_inputs.user_text_hash` must match the trigger input report; trace
  row `public_inputs.entrypoint_provenance.status` must be `ipc_event_observed`.
- hypothesis: a Wizard selected row can be materialized into one desktop chat turn and routed through the existing
  EgoDesktop chat-turn seam while preserving hash-only committed provenance.
- strongest baseline: current shim/backend behavior; this run has no same-access comparison and no `CREATURE_ON`
  candidate.
- ablation requirement: none in 026.
- trace/replay requirement: existing `joiRealLoopGAblationTraceRunner` must write `trace_rows.jsonl`; replay is forbidden
  in this slice.
- computed-evidence provenance gate: trigger input report is produced by
  `scripts/codex/materialize_egodesktop_selected_source_trigger_input.py`, and trace row hash/entrypoint provenance is
  produced by the existing EgoDesktop trace writer from the `ipcMain.handle("ego-desktop:chat-turn")` event boundary.
- acceptance gate: smoke exits successfully, trace row hash aligns with source-trigger hash, local checks pass, Claude
  blocking review is no-blocking or any blocker is repaired and re-reviewed, and source-limited self-review finds no raw
  text or scope expansion.
- claim ceiling: selected source desktop trigger smoke only.
- stop condition: smoke failure, trace row absent, hash mismatch, raw text committed, replay/scoring/same-access attempt,
  runtime enablement, program-state/evidence-ledger update, push, tag, or remote anchor.
- rollback plan: delete 026 docs/artifacts/task-board entry and regenerate route-convergence views.
- expected changed files:
  - `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-wizard-selected-source-chat-smoke-v0/`
  - `artifacts/egodesktop_joi_real_loop_g_ablation_wizard_selected_source_chat_smoke_v0/`
  - `EgoDesktop/src/main.js`
  - `EgoDesktop/src/joiRealLoopGAblationTraceRunner.js`
  - `EgoDesktop/viewer/renderer.js`
  - `EgoDesktop/tests/joi_real_loop_g_ablation_chat_turn_trace.test.js`
  - `EgoDesktop/tests/joi_real_loop_g_ablation_trace_runner.test.js`
  - `EgoDesktop/tests/joi_real_loop_g_ablation_backend_snapshot.test.js`
  - `scripts/codex/materialize_egodesktop_selected_source_trigger_input.py`
  - `scripts/tests/test_materialize_egodesktop_selected_source_trigger_input.py`
  - `Tasks/TASK_BOARD.yaml`
  - `docs/codex/tasks/TASK_LANE_INDEX.md`
- forbidden changes:
  - no raw text staging;
  - no same-access baseline execution;
  - no replay, scoring, comparison, verdict, or route advancement;
  - no runtime enablement outside explicit smoke flags;
  - no `PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger update;
  - no push, tag, or remote anchor.
- Auto-Remote-Anchor decision: forbidden.

## What This Can Prove

Only that one predeclared Wizard selected source row can be materialized into userText, sent through the real Electron
`window.egoDesktop.sendChatTurn(...)` IPC path, and serialized by the existing trace writer with matching source-trigger
hash and IPC-boundary provenance.

## What This Does Not Prove

This does not prove `CREATURE_ON` effect, replay validity, D-provenance sufficiency, same-access saturation, baseline
score, candidate attribution, route advancement, product benefit, runtime integration safety, stable user benefit,
durable memory efficacy, agency, emotion, subjectivity, consciousness, alive status, or Bar-2 specialness.

## Authority refs

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-capture-manifest-refresh-v0/`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-selected-source-chat-smoke-v0/`
- `artifacts/egodesktop_joi_real_loop_g_ablation_capture_manifest_v0/CAPTURE_MANIFEST.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_capture_manifest_v0/BUILD_REPORT.json`
