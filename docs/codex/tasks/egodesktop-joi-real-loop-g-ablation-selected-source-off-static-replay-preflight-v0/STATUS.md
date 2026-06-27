# EgoDesktop Joi Real-Loop G-ABLATION Selected Source OFF_STATIC Replay Preflight v0 Status

- status: `accepted_local`
- task_id: `EGODESKTOP-GABLATION-023`
- parent_task_id: `EGODESKTOP-GABLATION-022`
- claim_ceiling: `selected_source_off_static_replay_preflight_only`
- mainline_connected: `false`
- enabled: `explicit_offline_artifact_runner_only`
- real_trigger_evidence: `inherits_022_desktop_chat_turn_trace_row`
- runtime_authority: `offline_artifact_runner_only`

## Current Readback

- current branch: `main`
- source HEAD before 023 edits: `6f19bd8e test: add selected source chat smoke evidence`
- 022 status: `accepted_local`
- 022 trace source: `artifacts/egodesktop_joi_real_loop_g_ablation_selected_source_chat_smoke_v0/trace/trace_rows.jsonl`
- builder command:
  `node EgoDesktop/scripts/build-joi-g-ablation-off-static-replay-heldout.js --source-rows artifacts/egodesktop_joi_real_loop_g_ablation_selected_source_chat_smoke_v0/trace/trace_rows.jsonl --out artifacts/egodesktop_joi_real_loop_g_ablation_selected_source_off_static_replay_preflight_v0/replay --run-id egodesktop_gablation_023_selected_source_off_static_replay`
- builder status: `off_static_replay_heldout_row_written`
- builder trace row count: `1`
- builder calibration reference kind: `synthetic_reference`
- builder split contract status: `synthetic_calibration_reference_distinct_from_heldout_observation`
- builder scoring/verdict authority: `scoring_run_authorized=false`, `verdict_authorized=false`
- evaluator command:
  `node EgoDesktop/scripts/evaluate-joi-g-ablation-replay.js --rows artifacts/egodesktop_joi_real_loop_g_ablation_selected_source_off_static_replay_preflight_v0/replay/trace_rows.jsonl --out artifacts/egodesktop_joi_real_loop_g_ablation_selected_source_off_static_replay_preflight_v0/eval --run-id egodesktop_gablation_023_selected_source_off_static_replay_eval --require-007-scoring-precondition --required-condition OFF_STATIC_REPLAY_HELDOUT`
- evaluator status: `replay_integrity_preflight_pass_no_verdict`
- evaluator rows evaluated: `1`
- evaluator leakage positive control status: `pass`
- evaluator D-field replay precondition satisfied: `true`
- evaluator scoring/verdict authority: `scoring_run_authorized=false`, `verdict_authorized=false`
- replay row condition: `OFF_STATIC_REPLAY_HELDOUT`
- replay row policy: `offline_non_llm_adapter_recompute_v0`
- replay row fields: `complete_serialized_state=true`, `complete_observation=true`, `d_fields_frozen=true`,
  `offline_replay_function_id=off_static_replay_heldout_non_llm_adapter_v0`
- 023 artifact raw text scan: `selected_source_utterance_leak_count=0` across `5` files.

## Current Claim Ceiling

This can prove only selected-source OFF_STATIC replay preflight structure. It does not prove `CREATURE_ON`, scoring,
same-access comparison, or mechanism attribution.

## Next Minimal Closed-Loop Action

Use this local-only replay preflight boundary only as input to a future separately carded calibration/reference or
baseline slice; do not treat it as scoring, attribution, or route advancement.
