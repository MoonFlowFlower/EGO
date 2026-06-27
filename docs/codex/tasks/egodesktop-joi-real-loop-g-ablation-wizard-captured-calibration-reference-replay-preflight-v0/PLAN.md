# Plan

## Milestone 1 - Card-Only Boundary

- goal: create the separate 028 task card for Wizard captured calibration reference replay preflight.
- non-goals: do not run calibration builder, heldout builder, evaluator, Electron smoke, same-access baseline, scoring, or
  `CREATURE_ON`.
- affected files:
  - `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-wizard-captured-calibration-reference-replay-preflight-v0/`
  - `Tasks/TASK_BOARD.yaml`
  - `docs/codex/tasks/TASK_LANE_INDEX.md`
- verification:
  - `python scripts\codex\verify_route_convergence.py`
  - `python scripts\codex\verify_repo.py --mode fast`
  - `git diff --check`
  - `python scripts\codex_session_guard.py --mutation-scope docs\codex\tasks\egodesktop-joi-real-loop-g-ablation-wizard-captured-calibration-reference-replay-preflight-v0\MUTATION_SCOPE.yaml closeout-check --format markdown`
- completion standard: task package exists, task board entry exists, route index is regenerated, checks pass, and no
  artifact runner has been executed.
- rollback: delete the task directory, remove the task-board entry, regenerate route views.

## Future Milestone - Captured Reference Replay Preflight

This future milestone is not executed by this card-only slice. If authorized later, use the current callable scripts:

```powershell
node EgoDesktop/scripts/build-joi-g-ablation-calibration-reference.js `
  --calibration-rows artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/capture/calibration_ui_predeclared_single/trace/trace_rows.jsonl `
  --heldout-rows artifacts/egodesktop_joi_real_loop_g_ablation_wizard_selected_source_chat_smoke_v0/trace/trace_rows.jsonl `
  --predeclared-calibration-prompt-pack artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/capture/calibration_ui_predeclared_single/PREDECLARED_CALIBRATION_PROMPT_PACK.json `
  --out artifacts/egodesktop_joi_real_loop_g_ablation_wizard_captured_calibration_reference_replay_preflight_v0/calibration_reference `
  --run-id egodesktop_gablation_028_wizard_captured_calibration_reference

node EgoDesktop/scripts/build-joi-g-ablation-off-static-replay-heldout.js `
  --source-rows artifacts/egodesktop_joi_real_loop_g_ablation_wizard_selected_source_chat_smoke_v0/trace/trace_rows.jsonl `
  --calibration-reference artifacts/egodesktop_joi_real_loop_g_ablation_wizard_captured_calibration_reference_replay_preflight_v0/calibration_reference/calibration_reference.json `
  --out artifacts/egodesktop_joi_real_loop_g_ablation_wizard_captured_calibration_reference_replay_preflight_v0/replay `
  --run-id egodesktop_gablation_028_wizard_captured_reference_off_static_replay

node EgoDesktop/scripts/evaluate-joi-g-ablation-replay.js `
  --rows artifacts/egodesktop_joi_real_loop_g_ablation_wizard_captured_calibration_reference_replay_preflight_v0/replay/trace_rows.jsonl `
  --out artifacts/egodesktop_joi_real_loop_g_ablation_wizard_captured_calibration_reference_replay_preflight_v0/eval `
  --run-id egodesktop_gablation_028_wizard_captured_reference_replay_eval `
  --require-007-scoring-precondition `
  --required-condition OFF_STATIC_REPLAY_HELDOUT
```

Future completion requires a new 028-specific partition/reference report against the 026 Wizard heldout row. The old 009
`calibration_reference.json` may be an input reference but must not be reused as the final Wizard-specific partition
evidence.

## Decision Log

- 2026-06-27: Keep this turn card-only because the user asked for a separate task card. Implementation remains a future
  explicit slice.
- 2026-06-27: Do not claim the existing 009 reference is already Wizard-heldout-specific; require a new 028 partition
  report if implementation is authorized.
