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

## Milestone 2 - Captured Reference Replay Preflight

Executed on 2026-06-27 after user authorization. The current callable scripts were run exactly for the accepted 009
calibration trace row and accepted 026 Wizard heldout trace row:

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

Completion required a new 028-specific partition/reference report against the 026 Wizard heldout row. The old 009
`calibration_reference.json` may be an input reference but must not be reused as the final Wizard-specific partition
evidence.

### Completion Readback

- calibration builder status: `captured_calibration_reference_written`
- 028 calibration reference hash: `0c3c4ea74a06efd9a1f66136f5e06febf10affbf1553c38cc6bfadd2068aea27`
- 028 partition manifest hash: `8d743ba6921272634dde4d3b0e229035dbd83f885efe6d1bdc4dfbff40202cb4`
- calibration source row hash: `aebbdbedaca71d8955e470ffc6977d1bb9816e49f8af5878abd20eebbc5a4b28`
- Wizard heldout source row hash: `3a4569e77c39733a4d13034e3ad9cdfc5879e1974b9561760c06703e38d06a76`
- partition checks: `partition_disjointness_status=pass`, `content_disjointness_status=pass`,
  `provenance_distinctness_status=pass`, `overlap_positive_control_status=pass`,
  `synthetic_fallback_positive_control_status=pass`
- replay builder status: `off_static_replay_heldout_row_written`
- 028 replay row hash: `06df994805f6c8b6413e203929acb0e3d9cc2fa75237957a21d342de7161b4fd`
- replay split contract: `captured_calibration_reference_distinct_from_heldout_observation`
- evaluator status: `replay_integrity_preflight_pass_no_verdict`
- D-field precondition: `d_field_replay_precondition_satisfied=true`
- scoring/verdict: `scoring_run_authorized=false`, `verdict_authorized=false`
- raw text field scan: `raw_text_field_scan_status=pass`

## Decision Log

- 2026-06-27: Initial card turn stayed card-only because the user asked for a separate task card. Implementation
  remained a later explicit slice.
- 2026-06-27: Do not claim the existing 009 reference is already Wizard-heldout-specific; require a new 028 partition
  report if implementation is authorized.
- 2026-06-27: User authorized continued execution. Ran the 028 future milestone as an offline artifact-only preflight,
  with no code changes, no raw text staging, no scoring/verdict, no `CREATURE_ON`, no same-access baseline, no runtime
  enablement, no program-state/evidence-ledger update, and no remote anchor.
