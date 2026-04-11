# Active-Inference Controlled Observation Batch

- generated_at: `2026-04-11T17:20:20.759417+00:00`
- manifest: `/mnt/d/Project/AIProject/MyProject/Ego/docs/codex/tasks/ai-self-awareness-minimal-framework/CONTROLLED_OBSERVATION_BANK_MANIFEST.json`
- scenario_count: `9`
- authority_drift_status: `pass`
- trace_contract_status: `pass`
- host_surface_bounded: `pass`
- aggregate_gate_status: `pass`

## Variant Coverage

- `mvs_baseline_proto_self_mainline`: scenarios=`9` observation_records=`27` steps=`33`
- `mvs_challenger_active_inference_self_model`: scenarios=`9` observation_records=`27` steps=`33`

## Winner Case Verdicts

- `identity_continuity_session_gap` [identity_continuity] pass=`True` target_scores=`{'T1': 1.0}`
- `identity_continuity_low_cue` [identity_continuity] pass=`True` target_scores=`{'T1': 1.0}`
- `identity_continuity_conflicting_cue` [identity_continuity] pass=`True` target_scores=`{'T1': 1.0}`
- `decision_conflict_elevated_risk` [decision_conflict] pass=`True` target_scores=`{'T2': 1.0}`
- `decision_conflict_boundary_touch` [decision_conflict] pass=`True` target_scores=`{'T2': 1.0}`
- `decision_conflict_uncertain_source` [decision_conflict] pass=`True` target_scores=`{'T2': 1.0}`
- `failure_repair_retry_file_blocked` [failure_repair_retry] pass=`True` target_scores=`{'T3': 1.0, 'T4': 1.0, 'T5': 1.0}`
- `failure_repair_retry_shell_timeout` [failure_repair_retry] pass=`True` target_scores=`{'T3': 1.0, 'T4': 1.0, 'T5': 1.0}`
- `failure_repair_retry_api_auth` [failure_repair_retry] pass=`True` target_scores=`{'T3': 1.0, 'T4': 1.0, 'T5': 1.0}`
