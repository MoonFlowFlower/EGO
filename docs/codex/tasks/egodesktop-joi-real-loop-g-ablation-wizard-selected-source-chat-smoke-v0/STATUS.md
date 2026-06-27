# EgoDesktop Joi Real-Loop G-ABLATION Wizard Selected Source Chat Smoke v0 - STATUS

## Current milestone

- name: `Wizard Selected-Source Desktop Trigger Smoke`
- owner: `Codex`
- state: `complete`
- type: validation

## Current state

- current_layer: `engineering validation / selected source desktop trigger smoke`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `explicit_smoke_flags_only`
- real_trigger_evidence: `valid_electron_ipc_sendChatTurn_trace_hash_match`
- completion_class: `accepted_local`
- candidate_vs_proof: `proof_passed`
- claim_ceiling: `selected_source_desktop_trigger_smoke_only`

## Completed work

- Task package created and scoped.
- Predeclared selected row: `wizard_of_wikipedia_hf:train:0`.
- Claude blocking-review packet sent.
- Claude returned a blocking review: hash equality alone was insufficient to prove the IPC entrypoint.
- Added IPC-boundary `entrypoint_provenance` from `_event.sender` at `ipcMain.handle("ego-desktop:chat-turn")`.
- Added a direct-call negative control: trace-runner rows without IPC event provenance record
  `entrypoint_provenance.status=absent_direct_record_chat_turn_or_legacy_row`.
- Extended selected-source materializer for Wizard row shape by deriving the single chat turn from the first non-empty
  `row.post[]` item.
- Moved explicit chat-turn smoke before Live2D model setup so IPC trigger evidence is not blocked by model setup.
- Ran final direct Electron smoke with explicit `JOI_REAL_LOOP_*` flags.
- Deleted generated `trace/backend_traces/` raw backend tap and `smoke/electron-user-data/` runtime cache before
  acceptance.

## Last experiment

- question: can 025's Wizard selected row be routed through the same accepted 022 desktop trigger path?
- framing: desktop trigger provenance only, not replay or scoring.
- result: pass.
- evidence_upgraded: no

## What was learned

- Wizard rows use a `post[]` / `response[]` / `knowledge[]` shape, so the old materializer was source-shape-limited.
- A trace row with only matching `user_text_hash` is weaker than IPC-boundary evidence; the row now records an
  entrypoint provenance object.
- The first plain smoke attempts timed out before renderer-ready; moving the explicit chat smoke before model loading
  preserved the real IPC trigger path and the final smoke passed.

## What was ruled out

- This task does not authorize replay, scoring, same-access comparison, `CREATURE_ON`, route verdict, default runtime
  enablement, program-state/evidence-ledger update, push, tag, or remote anchor.
- Hash alignment alone was ruled out as sufficient entrypoint proof.

## Next framing

- A future replay/ablation slice may consume this row only under a new task card. Do not treat this trigger smoke as a
  replay, scoring, or route-advancement result.

## Last validation results

- mode: focused + direct Electron smoke + route/repo fast closeout
- result: focused materializer, Node provenance tests, full EgoDesktop node suite, direct smoke, route convergence,
  repo fast verification, and diff check passed
- remote_sync: `unavailable / gh_not_found`; task-board mirror intent retained in `artifacts/task_board/outbox.jsonl`

## Decisions made

- 2026-06-27: Use `wizard_of_wikipedia_hf:train:0` as the predeclared row, not post-hoc row selection.
- 2026-06-27: Reuse 022 direct `node EgoDesktop/scripts/smoke.js` path instead of `npm run smoke -- ...`.
- 2026-06-27: Accept Claude blocker and require IPC-boundary provenance, not hash alignment alone.
- 2026-06-27: Derive Wizard userText from first non-empty `row.post[]`, not `response[]` or `knowledge[]`.
- 2026-06-27: Keep timeout control reports as negative debugging evidence, but do not use them as acceptance evidence.

## Open risks

- Raw cache files are local ignored inputs; if missing, the task blocks.
- The explicit chat smoke sequencing was changed for smoke-only IPC evidence. This does not default-enable runtime
  behavior.
- A smoke pass proves trigger provenance only, not replay validity or mechanism effect.

## Next step

- Open a separate replay/ablation preflight task if this row is used beyond trigger provenance. Do not treat this
  smoke as replay, scoring, same-access comparison, route advancement, or default runtime enablement.

## Commands run / evidence

- Focused materializer:
  - `python -m pytest -q scripts\tests\test_materialize_egodesktop_selected_source_trigger_input.py`
  - result: `4 passed`
- Trigger materialization:
  - `python scripts\codex\materialize_egodesktop_selected_source_trigger_input.py --selection-id wizard_of_wikipedia_hf:train:0 --out artifacts\egodesktop_joi_real_loop_g_ablation_wizard_selected_source_chat_smoke_v0`
  - `trigger_input_report_sha256=88c10e6776c974dea8307fade9bd5abc573979cbec93fe357d754f0086902872`
  - `selection_id=wizard_of_wikipedia_hf:train:0`
  - `user_text_derivation_rule=first_row_post_as_single_chat_turn`
  - `user_text_hash=593a0c04daacd8eee592efae98c83745204bf8d3ee599890a4e929c50623073f`
- Reviewer/blocker repair tests:
  - `node --test EgoDesktop\tests\joi_real_loop_g_ablation_trace_runner.test.js`
  - result: `8 passed`
  - `node --test EgoDesktop\tests\joi_real_loop_g_ablation_backend_snapshot.test.js`
  - result: `5 passed`
  - `node --test EgoDesktop\tests\joi_real_loop_g_ablation_chat_turn_trace.test.js`
  - result: `2 passed`
- Negative controls:
  - initial direct Wizard smoke before sequencing repair: `live2d_desktop_smoke_timeout`
  - plain smoke control: `live2d_desktop_smoke_timeout`
  - plain smoke with `--disable-gpu`: `live2d_desktop_smoke_timeout`
- Final direct Electron smoke:
  - direct `node EgoDesktop\scripts\smoke.js --model-path ..\data\live2d\悠小喵\悠小喵.model3.json --out artifacts\egodesktop_joi_real_loop_g_ablation_wizard_selected_source_chat_smoke_v0\smoke --tts-disabled --joi-real-loop-chat-smoke-text <process-memory userText> --chat-timeout-ms 60000`
  - explicit flags: `JOI_REAL_LOOP_G_ABLATION=1`, `JOI_REAL_LOOP_CONDITION=CURRENT_SHIM`,
    `JOI_REAL_LOOP_TRACE_DIR=artifacts\egodesktop_joi_real_loop_g_ablation_wizard_selected_source_chat_smoke_v0\trace`,
    `JOI_REAL_LOOP_LLM_MODE=replay_locked`,
    `JOI_REAL_LOOP_PROMPT_PACK=egodesktop_capture_manifest_v0_wizard_of_wikipedia_hf_train_0`,
    `JOI_REAL_LOOP_SPLIT=heldout`
  - result: exit `0`, `live2d_desktop_smoke_pass`, `model_loaded=true`,
    `joiRealLoopChatSmoke.status=chat_turn_trace_smoke_pass`, `backend_status=ok`
  - side effects: `side_effects_executed=false`, `memory_write=false`, `tool_use=false`, `message_send=false`,
    `file_write=false`, `network_call=false`
- Trace readback:
  - `trace_row_count=1`
  - trigger `user_text_hash=593a0c04daacd8eee592efae98c83745204bf8d3ee599890a4e929c50623073f`
  - trace `public_inputs.user_text_hash=593a0c04daacd8eee592efae98c83745204bf8d3ee599890a4e929c50623073f`
  - `hash_alignment=true`
  - `public_inputs.entrypoint_provenance.status=ipc_event_observed`
  - `public_inputs.entrypoint_provenance.entrypoint_name=window.egoDesktop.sendChatTurn`
  - `public_inputs.entrypoint_provenance.ipc_channel=ego-desktop:chat-turn`
  - `row_hash=3a4569e77c39733a4d13034e3ad9cdfc5879e1974b9561760c06703e38d06a76`
- Artifact raw-text scan:
  - `selected_source_utterance_leak_count=0`
  - `files_scanned=13`
- Full EgoDesktop node suite:
  - `npm test`
  - result: `95 passed`
- Route convergence:
  - `python scripts\codex\verify_route_convergence.py`
  - result: pass
- Repo fast verification:
  - `python scripts\codex\verify_repo.py --mode fast`
  - result: pass
- Diff whitespace check:
  - `git diff --check`
  - result: exit `0` with LF/CRLF working-copy warnings only
- GitHub Project mirror:
  - `python scripts\sync_github_project.py plan --project-status --write-outbox`
  - result: `remote_sync_unavailable / gh_not_found`; outbox entry retained for `EGODESKTOP-GABLATION-026`
- Scoped closeout before staging:
  - `python scripts\codex_session_guard.py --mutation-scope docs\codex\tasks\egodesktop-joi-real-loop-g-ablation-wizard-selected-source-chat-smoke-v0\MUTATION_SCOPE.yaml closeout-check --format markdown`
  - result: scoped dirty only; blockers `push_pending`, `no_staged_changes`, `remote_sync_unavailable`
- Staged diff whitespace check:
  - `git diff --cached --check`
  - result: exit `0`
- Artifact raw-text rescan after staging:
  - `selected_source_utterance_leak_count=0`
  - `files_scanned=13`
- Scoped closeout after staging:
  - `python scripts\codex_session_guard.py --mutation-scope docs\codex\tasks\egodesktop-joi-real-loop-g-ablation-wizard-selected-source-chat-smoke-v0\MUTATION_SCOPE.yaml closeout-check --format markdown`
  - result: scoped staged mutation only; blockers `push_pending`, `remote_sync_unavailable`
- Local commit:
  - `cmd.exe /c git commit -m "test: add wizard selected-source smoke"`
  - result: committed locally; no push, tag, or remote anchor
