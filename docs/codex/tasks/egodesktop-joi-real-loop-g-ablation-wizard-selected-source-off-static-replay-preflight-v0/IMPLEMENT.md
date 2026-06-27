# Implementation

## Milestone 1 - Wizard OFF_STATIC Replay Preflight

- source row: `artifacts/egodesktop_joi_real_loop_g_ablation_wizard_selected_source_chat_smoke_v0/trace/trace_rows.jsonl`
- builder output: `artifacts/egodesktop_joi_real_loop_g_ablation_wizard_selected_source_off_static_replay_preflight_v0/replay/`
- evaluator output: `artifacts/egodesktop_joi_real_loop_g_ablation_wizard_selected_source_off_static_replay_preflight_v0/eval/`

Commands:

```powershell
node EgoDesktop/scripts/build-joi-g-ablation-off-static-replay-heldout.js `
  --source-rows artifacts/egodesktop_joi_real_loop_g_ablation_wizard_selected_source_chat_smoke_v0/trace/trace_rows.jsonl `
  --out artifacts/egodesktop_joi_real_loop_g_ablation_wizard_selected_source_off_static_replay_preflight_v0/replay `
  --run-id egodesktop_gablation_027_wizard_selected_source_off_static_replay

node EgoDesktop/scripts/evaluate-joi-g-ablation-replay.js `
  --rows artifacts/egodesktop_joi_real_loop_g_ablation_wizard_selected_source_off_static_replay_preflight_v0/replay/trace_rows.jsonl `
  --out artifacts/egodesktop_joi_real_loop_g_ablation_wizard_selected_source_off_static_replay_preflight_v0/eval `
  --run-id egodesktop_gablation_027_wizard_selected_source_off_static_replay_eval `
  --require-007-scoring-precondition `
  --required-condition OFF_STATIC_REPLAY_HELDOUT
```

Acceptance readback must include:

- `source_row_hash == 3a4569e77c39733a4d13034e3ad9cdfc5879e1974b9561760c06703e38d06a76`
- evaluator `status == replay_integrity_preflight_pass_no_verdict`
- evaluator `d_field_replay_precondition_satisfied == true`
- evaluator `scoring_run_authorized == false`
- evaluator `verdict_authorized == false`
- raw selected-source utterance leak count `0`
