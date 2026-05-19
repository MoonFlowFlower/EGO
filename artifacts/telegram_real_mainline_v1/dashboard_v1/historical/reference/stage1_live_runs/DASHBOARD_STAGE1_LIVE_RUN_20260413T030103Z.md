# Dashboard Stage 1 Autonomous Live Run

- generated_at: `2026-04-13T03:01:04.537550+00:00`
- run_started_at: `2026-04-13T03:01:03.978120+00:00`
- report_kind: `dashboard_stage1_autonomous_live_run`
- claim_ceiling: `single_entry_live_window_observation`
- session_id: `dashboard:test:codex-stage1-20260413-030103`
- session_name: `codex-stage1-20260413-030103`
- prompt_pack_id: `stage1_dashboard_ordinary_chat_hybrid_v1`
- prompt_source_strategy: `hybrid`
- execution_verdict: `single_entry_live_window_captured`
- blocker_reason: `None`
- export_artifact_path: `artifacts/telegram_real_mainline_v1/dashboard_v1/DASHBOARD_LIVE_SESSION_EXPORT_CURRENT.json`
- create_session_transport: `python`
- fallback_used: `False`

## Summary

- prompt_source_counts: `{'repo_authored_control': 2, 'generated': 2, 'chatlog_curated': 1}`
- prompt_pack_degraded: `False`
- assistant_turn_count: `5`
- ordinary_chat_turn_count: `5`
- execute_task_turn_count: `0`
- subject_gate_ok_count: `0`
- oe_available_count: `0`
- host_only_count: `5`
- degraded_count: `0`
- clean_live_window: `False`
- recent_consecutive_clean_runs: `0`
- recent_same_blocker_count: `0`
- dashboard_only_stability_strengthened: `False`
- stop_requested_by_same_blocker_rule: `False`

## Turn Results

### `greeting`

- prompt_text: `你好啊`
- input_provenance: `{'source_kind': 'repo_authored_control', 'source_label': 'repo control:greeting', 'derivation': 'native', 'source_ref': 'internal:repo_authored_control:greeting', 'normalization_applied': False}`
- before_revision: `1`
- send_transport: `python`
- fetch_transport: `python`
- observed_revision: `2`
- runtime_action: `chat`
- parser_source: `chat_default`
- subject_gate_ok: `False`
- oe_available: `False`
- reply_authority: `None`
- reply_origin: `None`
- host_only: `True`
- degraded: `False`
- assistant_text_preview: `subject_gate_failed：主体暂时不可用，这一步已阻断，请稍后重试。`

### `ordinary_ask`

- prompt_text: `你现在想继续聊什么？`
- input_provenance: `{'source_kind': 'repo_authored_control', 'source_label': 'repo control:ordinary ask', 'derivation': 'native', 'source_ref': 'internal:repo_authored_control:ordinary_ask', 'normalization_applied': False}`
- before_revision: `2`
- send_transport: `python`
- fetch_transport: `python`
- observed_revision: `3`
- runtime_action: `chat`
- parser_source: `chat_default`
- subject_gate_ok: `False`
- oe_available: `False`
- reply_authority: `None`
- reply_origin: `None`
- host_only: `True`
- degraded: `False`
- assistant_text_preview: `subject_gate_failed：主体暂时不可用，这一步已阻断，请稍后重试。`

### `generated_1`

- prompt_text: `有时候不想太严肃聊天时，你会想聊哪种小话题？`
- input_provenance: `{'source_kind': 'generated', 'source_label': 'local generated ordinary-chat template', 'derivation': 'generated', 'source_ref': 'internal:generated_ordinary_chat_v1:3', 'normalization_applied': False}`
- before_revision: `3`
- send_transport: `python`
- fetch_transport: `python`
- observed_revision: `4`
- runtime_action: `chat`
- parser_source: `chat_default`
- subject_gate_ok: `False`
- oe_available: `False`
- reply_authority: `None`
- reply_origin: `None`
- host_only: `True`
- degraded: `False`
- assistant_text_preview: `subject_gate_failed：主体暂时不可用，这一步已阻断，请稍后重试。`

### `generated_2`

- prompt_text: `如果现在想换个不费劲的话题，你会往哪个方向拐？`
- input_provenance: `{'source_kind': 'generated', 'source_label': 'local generated ordinary-chat template', 'derivation': 'generated', 'source_ref': 'internal:generated_ordinary_chat_v1:4', 'normalization_applied': False}`
- before_revision: `4`
- send_transport: `python`
- fetch_transport: `python`
- observed_revision: `5`
- runtime_action: `chat`
- parser_source: `chat_default`
- subject_gate_ok: `False`
- oe_available: `False`
- reply_authority: `None`
- reply_origin: `None`
- host_only: `True`
- degraded: `False`
- assistant_text_preview: `subject_gate_failed：主体暂时不可用，这一步已阻断，请稍后重试。`

### `curated_chatlog`

- prompt_text: `要是隔了一会儿再继续聊天，你通常会从哪里重新接上？`
- input_provenance: `{'source_kind': 'chatlog_curated', 'source_label': 'repo seed: light reconnect', 'derivation': 'rewritten', 'source_ref': 'internal:chatlog_curated_v1:chatlog_seed_light_reconnect', 'normalization_applied': True}`
- before_revision: `5`
- send_transport: `python`
- fetch_transport: `python`
- observed_revision: `6`
- runtime_action: `chat`
- parser_source: `chat_default`
- subject_gate_ok: `False`
- oe_available: `False`
- reply_authority: `None`
- reply_origin: `None`
- host_only: `True`
- degraded: `False`
- assistant_text_preview: `subject_gate_failed：主体暂时不可用，这一步已阻断，请稍后重试。`

## Claim Ceiling

- This run records one dedicated dashboard_chat live window only.
- Mixed-source prompts retain parity only inside dashboard-only strengthened evidence.
- It does not prove Stage 1 closeout, cross-entrypoint proof, runtime efficacy, live user benefit, or consciousness-like properties.
