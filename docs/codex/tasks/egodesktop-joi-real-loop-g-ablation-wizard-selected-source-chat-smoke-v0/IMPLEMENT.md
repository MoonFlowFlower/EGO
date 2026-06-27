# Implement

## Current milestone

- name: `Wizard Selected-Source Desktop Trigger Smoke`
- owner: `Codex`
- state: `active`
- type: validation

## Implementation notes

- Reuse the accepted 022 materializer and direct Electron smoke path.
- Record explicit IPC-boundary entrypoint provenance in trace rows so hash alignment cannot be mistaken for entrypoint
  proof by itself.
- Run the explicit chat-turn smoke before Live2D model loading so the IPC trigger evidence is not blocked by model setup;
  the smoke report must still pass before the task can close.
- Do not modify EgoDesktop default runtime behavior; this path is gated by explicit smoke text and `JOI_REAL_LOOP_*`
  flags.
- Keep raw selected-source text out of committed artifacts and final reports.
- Treat Claude output as reviewer evidence, not authority.

## Expected commands

- `python scripts/codex/materialize_egodesktop_selected_source_trigger_input.py --selection-id wizard_of_wikipedia_hf:train:0 --out artifacts/egodesktop_joi_real_loop_g_ablation_wizard_selected_source_chat_smoke_v0`
- direct `node EgoDesktop/scripts/smoke.js` with explicit `JOI_REAL_LOOP_*` environment flags and
  `--joi-real-loop-chat-smoke-text` sourced from the materializer in process memory.
- `python -m pytest -q scripts/tests/test_materialize_egodesktop_selected_source_trigger_input.py`
- `node --test EgoDesktop/tests/joi_real_loop_g_ablation_chat_turn_trace.test.js EgoDesktop/tests/joi_real_loop_g_ablation_trace_runner.test.js EgoDesktop/tests/joi_real_loop_g_ablation_backend_snapshot.test.js`
- `python scripts/codex/verify_route_convergence.py`
- `python scripts/codex/verify_repo.py --mode fast`
- `git diff --check`
