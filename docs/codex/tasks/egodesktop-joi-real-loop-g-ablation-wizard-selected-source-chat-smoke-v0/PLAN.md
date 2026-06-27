# Plan

1. Predeclare `selection_id=wizard_of_wikipedia_hf:train:0` from the refreshed 025 capture manifest.
2. Materialize one single-chat-turn userText from that selected row using
   `scripts/codex/materialize_egodesktop_selected_source_trigger_input.py`.
3. Write a hash-only `TRIGGER_INPUT_REPORT.json` without raw text to
   `artifacts/egodesktop_joi_real_loop_g_ablation_wizard_selected_source_chat_smoke_v0/`.
4. Run direct `node EgoDesktop/scripts/smoke.js ... --joi-real-loop-chat-smoke-text <materialized userText>` with
   explicit `JOI_REAL_LOOP_*` flags and the artifact-local trace/smoke directories.
5. Verify smoke report status, trace row count, user-text hash alignment, and
   `entrypoint_provenance.status=ipc_event_observed`.
6. Scan committed candidate artifacts for selected-source raw text leakage, using the materialized text only in process
   memory and not writing it to tracked files.
7. Capture Claude blocking-review verdict and repair blockers if any are scope-valid.
8. Regenerate route-convergence views.
9. Run focused tests, repo fast verifier, diff check, scoped closeout-check, and local-only commit if accepted.

## Reviewer repair

Claude review required one repair before implementation could close: hash equality alone was not enough to prove the
real IPC entrypoint. The accepted repair is to record `entrypoint_provenance` from `_event.sender` at
`ipcMain.handle("ego-desktop:chat-turn")`, and to keep direct trace-runner calls distinguishable through an absent
provenance negative control.

## Non-Goals

- No raw text staging.
- No replay, scoring, comparison, verdict, or same-access baseline.
- No `CREATURE_ON` execution.
- No default runtime enablement.
- No program-state/evidence-ledger update.
- No push, tag, or remote anchor.
