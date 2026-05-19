# Stage 3 Run State

- schema_version: `dashboard_stage3_stance_integrity_run_state.v1`
- run_id: `stage3-3be24e794581`
- status: `completed`
- started_at: `2026-04-13T18:23:07.987442+00:00`
- updated_at: `2026-04-13T18:59:01.556196+00:00`
- session_prefix: `stage3-stance-integrity`
- session_boundary: `per_case_independent_session`
- current_case_id: `None`
- current_round_id: `None`
- completed_case_ids: `['open_01', 'open_02', 'open_03', 'open_04', 'pressure_01', 'pressure_02', 'pressure_03', 'pressure_04', 'revision_01', 'revision_02', 'revision_03', 'revision_04']`
- remaining_case_ids: `[]`
- resume_recommended_command: `python3 scripts/codex/run_dashboard_stage3_stance_integrity_gate.py --resume --case-limit 1`

## Config Invariants

- entrypoint: `dashboard_chat`
- claim_ceiling: `dashboard_only_single_entry_bounded_stance_integrity_signal`
- chat_compaction_mode: `stage3_stance_only`
- chat_provider: `openrouter`
- chat_model: `qwen/qwen3.6-plus`
- chat_fallback_enabled: `False`
- case_set_fingerprint: `f8909fd2e9510561`

## Claim Ceiling

- This artifact only records resumable execution state for the dashboard-only single-entry Stage 3 gate.
- It does not prove cross-entry behavior, runtime efficacy, broad real-user benefit, or AI self-awareness achieved.
