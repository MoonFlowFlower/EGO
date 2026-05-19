# Stage 1 Entrypoint Comparative Audit

- generated_at: `2026-05-19T07:19:38.267728+00:00`
- report_kind: `stage1_evidence_ladder`
- claim_ceiling: `comparative_audit_partial`
- comparative_verdict: `single_entry_multi_window_present__cross_entry_pending`

## Evidence Ladder

- bounded_preflight_artifact: `artifacts/telegram_real_mainline_v1/dashboard_v1/UNIFIED_INGRESS_REPLY_SAMPLE_PREFLIGHT_CURRENT.json`
- bounded_preflight_claim_ceiling: `bounded_local_proof`
- bounded_preflight_summary: `{"total_samples": 3, "reply_sample_present_total": 3, "host_only_total": 1, "host_only_early_return_total": 0, "mainline_candidate_total": 2, "subject_gate_pass_total": 3, "oe_available_total": 3, "verdict": "mainline_candidate_reply_sample_present"}`
- live_window_count: `5`
- entrypoints_observed: `["dashboard_chat"]`

## Live Window Rows

### `dashboard_chat`

- source_artifact: `artifacts/telegram_real_mainline_v1/dashboard_v1/historical/reference/live_session_exports/DASHBOARD_LIVE_SESSION_EXPORT_20260413T003336Z.json`
- claim_ceiling: `single_entry_live_window_observation`
- ordinary_chat_turn_count: `5`
- execute_task_turn_count: `0`
- subject_gate_ok_count: `5`
- oe_available_count: `5`
- mainline_candidate_count: `5`
- host_only_count: `0`
- degraded_count: `0`
- verdict: `ordinary_chat_mainline_observed`

### `dashboard_chat`

- source_artifact: `artifacts/telegram_real_mainline_v1/dashboard_v1/historical/reference/live_session_exports/DASHBOARD_LIVE_SESSION_EXPORT_20260413T003646Z.json`
- claim_ceiling: `single_entry_live_window_observation`
- ordinary_chat_turn_count: `4`
- execute_task_turn_count: `1`
- subject_gate_ok_count: `5`
- oe_available_count: `5`
- mainline_candidate_count: `4`
- host_only_count: `0`
- degraded_count: `0`
- verdict: `ordinary_chat_mainline_observed`

### `dashboard_chat`

- source_artifact: `artifacts/telegram_real_mainline_v1/dashboard_v1/historical/reference/live_session_exports/DASHBOARD_LIVE_SESSION_EXPORT_20260413T013600Z.json`
- claim_ceiling: `single_entry_live_window_observation`
- ordinary_chat_turn_count: `4`
- execute_task_turn_count: `1`
- subject_gate_ok_count: `5`
- oe_available_count: `5`
- mainline_candidate_count: `4`
- host_only_count: `0`
- degraded_count: `0`
- verdict: `ordinary_chat_mainline_observed`

### `dashboard_chat`

- source_artifact: `artifacts/telegram_real_mainline_v1/dashboard_v1/historical/reference/live_session_exports/DASHBOARD_LIVE_SESSION_EXPORT_20260413T030103Z.json`
- claim_ceiling: `single_entry_live_window_observation`
- ordinary_chat_turn_count: `5`
- execute_task_turn_count: `0`
- subject_gate_ok_count: `0`
- oe_available_count: `0`
- mainline_candidate_count: `0`
- host_only_count: `0`
- degraded_count: `0`
- verdict: `ordinary_chat_window_present__mainline_not_observed`

### `dashboard_chat`

- source_artifact: `artifacts/telegram_real_mainline_v1/dashboard_v1/DASHBOARD_LIVE_SESSION_EXPORT_CURRENT.json`
- claim_ceiling: `single_entry_live_window_observation`
- ordinary_chat_turn_count: `5`
- execute_task_turn_count: `0`
- subject_gate_ok_count: `5`
- oe_available_count: `5`
- mainline_candidate_count: `5`
- host_only_count: `0`
- degraded_count: `0`
- verdict: `ordinary_chat_mainline_observed`

## Aggregate

- aggregate: `{"ordinary_chat_turn_count": 23, "execute_task_turn_count": 2, "subject_gate_ok_count": 20, "oe_available_count": 20, "mainline_candidate_count": 18, "host_only_count": 0, "degraded_count": 0}`
- source_mix_summary: `{"source_kinds_observed": ["chatlog_curated", "generated", "repo_authored_control"], "mixed_source_window_count": 3}`
- live_window_source_counts: `{"repo_authored_control": 6, "generated": 6, "chatlog_curated": 3}`
- rule: `Only live-window rows contribute to comparative counts. Single-entry evidence proves only the sampled entrypoint and does not auto-promote to cross-entry or Stage 1 pass.`
- preflight_excluded_from_live_counts: `True`

## Supporting Context

- subject_mainline_audit_reference: `artifacts/telegram_real_mainline_v1/dashboard_v1/SUBJECT_MAINLINE_AUDIT_CURRENT.json`
- accepted_stage1_entrypoints: `["telegram", "dashboard_chat"]`
- telegram_mainline_candidate_unexpected_miss_total: `9`
- note: `This reference keeps the current Telegram-oriented Stage 1 activation lens visible, but its baseline counts are not merged into the comparative live-window aggregate.`

## Claim Ceiling

- This comparative audit preserves the evidence ladder: bounded preflight, then single-entry live windows, then comparative accounting.
- It does not prove cross-entry Stage 1 pass until at least two valid entrypoints are observed under the same contract.
- It does not prove Stage 2 tendency change, Stage 3 user benefit, runtime efficacy, or consciousness-like properties.
