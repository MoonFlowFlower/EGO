# Dashboard v1 Artifact Manifest

- generated_at: `2026-05-19T07:19:38.178013+00:00`
- report_kind: `dashboard_v1_legacy_inventory_manifest`
- inventory_scope: `legacy_top_level_inventory`
- legacy_file_count: `39`

## Generated Cleanup Artifacts

- `artifacts/telegram_real_mainline_v1/dashboard_v1/ARTIFACT_MANIFEST_CURRENT.json`
- `artifacts/telegram_real_mainline_v1/dashboard_v1/ARTIFACT_MANIFEST_CURRENT.md`
- `artifacts/telegram_real_mainline_v1/dashboard_v1/DASHBOARD_STAGE1_LIVE_RUN_CURRENT.json`
- `artifacts/telegram_real_mainline_v1/dashboard_v1/DASHBOARD_STAGE1_LIVE_RUN_CURRENT.md`
- `artifacts/telegram_real_mainline_v1/dashboard_v1/STAGE1_ENTRYPOINT_COMPARATIVE_AUDIT_CURRENT.json`
- `artifacts/telegram_real_mainline_v1/dashboard_v1/STAGE1_ENTRYPOINT_COMPARATIVE_AUDIT_CURRENT.md`

## Categories

### `baseline_indexes`

- `agency_rollup.json`: Machine-readable rollup derived from agency runs.
- `agency_runs.jsonl`: Baseline index rows for agency run observations.
- `build_meta.json`: Index-generation metadata for dashboard_v1.
- `continuity_observation.jsonl`: Baseline observation index for continuity data.
- `failures.jsonl`: Baseline failure rows for dashboard_v1.
- `failures_rollup.json`: Machine-readable failure rollup for dashboard_v1.
- `gap_summary.json`: Machine-readable gap summary for dashboard_v1.
- `growth_rollup.json`: Machine-readable growth rollup for dashboard_v1.
- `growth_signals.jsonl`: Baseline index rows for growth-signal observations.
- `runs.jsonl`: Primary baseline run index for dashboard_v1.
- `runs_rollup.json`: Machine-readable run rollup for dashboard_v1.

### `current_audits`

- `LIVE_CHAT_SUBJECTIVE_VARIABILITY_CURRENT.json`: Current variability audit artifact; useful but not the Stage 1 owner slice.
- `LIVE_CHAT_SUBJECTIVE_VARIABILITY_CURRENT.md`: Markdown companion for the current subjective variability audit.
- `LIVE_CHAT_VARIABILITY_CURRENT.json`: Current live chat variability audit artifact.
- `LIVE_CHAT_VARIABILITY_CURRENT.md`: Markdown companion for the current live chat variability audit.
- `PROVIDER_RUNTIME_OPENEMOTION_E2E_GATE_CURRENT.json`: Current real-channel provider/runtime/OpenEmotion gate report.
- `PROVIDER_RUNTIME_OPENEMOTION_E2E_GATE_CURRENT.md`: Markdown companion for the current E2E gate report.
- `SUBJECT_MAINLINE_AUDIT_CURRENT.json`: Current Stage 1 subject-mainline audit authority artifact.
- `SUBJECT_MAINLINE_AUDIT_CURRENT.md`: Markdown companion for the current Stage 1 subject-mainline audit.
- `UNIFIED_HOST_CONTRACT_PARITY_CURRENT.json`: Current unified host contract parity audit artifact.
- `UNIFIED_HOST_CONTRACT_PARITY_CURRENT.md`: Markdown companion for the current unified host contract parity audit.

### `bounded_preflight`

- `UNIFIED_INGRESS_REPLY_SAMPLE_PREFLIGHT_CURRENT.json`: Bounded local readiness probe that must stay outside live baseline counts.
- `UNIFIED_INGRESS_REPLY_SAMPLE_PREFLIGHT_CURRENT.md`: Markdown companion for the bounded reply-sample preflight artifact.

### `single_entry_live_windows`

- `DASHBOARD_LIVE_SESSION_EXPORT_CURRENT.json`: Fresh dashboard_chat live-window export for one sampled entrypoint.
- `DASHBOARD_LIVE_SESSION_EXPORT_CURRENT.md`: Markdown companion for the live dashboard entrypoint export.

### `acceptance_reports`

- `CONTINUITY_OBSERVATION_LEDGER.md`: Human-readable continuity observation ledger for acceptance-facing review.
- `DATA_SCHEMA.md`: Schema reference for dashboard_v1 artifact interpretation.
- `GAP_SUMMARY.md`: Human-readable summary of known capture gaps and validation caveats.
- `README.md`: Directory-level guidance for dashboard_v1 usage and claim ceiling.
- `REAL_MAINLINE_CAPTURE_STATUS.md`: Acceptance-facing capture status note for the real mainline lane.

### `historical/reference`

- `PLASTICITY_REFLECTION_EVIDENCE.md`: Historical/reference evidence note; not a current default audit surface.

## Unclassified

- `STAGE3_CHAT_REPLY_ENGINE_PROBE_CURRENT.json`
- `STAGE3_CHAT_REPLY_ENGINE_PROBE_CURRENT.md`
- `STAGE3_STANCE_INTEGRITY_GATE_CURRENT.json`
- `STAGE3_STANCE_INTEGRITY_GATE_CURRENT.md`
- `STAGE3_STANCE_INTEGRITY_LIFECYCLE_CURRENT.json`
- `STAGE3_STANCE_INTEGRITY_LIFECYCLE_CURRENT.md`
- `STAGE3_STANCE_INTEGRITY_RUN_STATE_CURRENT.json`
- `STAGE3_STANCE_INTEGRITY_RUN_STATE_CURRENT.md`

## Contract

- This manifest classifies the pre-cleanup top-level dashboard_v1 inventory into stable buckets before any broader directory reshuffle.
- It does not itself move files or promote any artifact above its original claim ceiling.
