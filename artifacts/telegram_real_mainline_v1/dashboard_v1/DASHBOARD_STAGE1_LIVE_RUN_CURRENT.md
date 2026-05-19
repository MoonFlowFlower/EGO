# Dashboard Stage 1 Autonomous Live Run

- generated_at: `2026-04-13T03:04:05.410780+00:00`
- run_started_at: `2026-04-13T03:02:07.455107+00:00`
- report_kind: `dashboard_stage1_autonomous_live_run`
- claim_ceiling: `single_entry_live_window_observation`
- session_id: `dashboard:test:codex-stage1-20260413-030207`
- session_name: `codex-stage1-20260413-030207`
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
- subject_gate_ok_count: `5`
- oe_available_count: `5`
- host_only_count: `0`
- degraded_count: `0`
- clean_live_window: `True`
- recent_consecutive_clean_runs: `1`
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
- parser_source: `semantic_parser`
- subject_gate_ok: `True`
- oe_available: `True`
- reply_authority: `model_chat`
- reply_origin: `chat_mainline`
- host_only: `False`
- degraded: `False`
- assistant_text_preview: `你好呀！今天过得怎么样？`

### `ordinary_ask`

- prompt_text: `你现在想继续聊什么？`
- input_provenance: `{'source_kind': 'repo_authored_control', 'source_label': 'repo control:ordinary ask', 'derivation': 'native', 'source_ref': 'internal:repo_authored_control:ordinary_ask', 'normalization_applied': False}`
- before_revision: `2`
- send_transport: `python`
- fetch_transport: `python`
- observed_revision: `3`
- runtime_action: `chat`
- parser_source: `semantic_parser`
- subject_gate_ok: `True`
- oe_available: `True`
- reply_authority: `model_chat`
- reply_origin: `chat_mainline`
- host_only: `False`
- degraded: `False`
- assistant_text_preview: `都可以，你最近有遇到什么有趣的事吗？`

### `generated_1`

- prompt_text: `有时候不想太严肃聊天时，你会想聊哪种小话题？`
- input_provenance: `{'source_kind': 'generated', 'source_label': 'local generated ordinary-chat template', 'derivation': 'generated', 'source_ref': 'internal:generated_ordinary_chat_v1:3', 'normalization_applied': False}`
- before_revision: `3`
- send_transport: `python`
- fetch_transport: `python`
- observed_revision: `4`
- runtime_action: `chat`
- parser_source: `chat_default`
- subject_gate_ok: `True`
- oe_available: `True`
- reply_authority: `model_chat`
- reply_origin: `chat_mainline`
- host_only: `False`
- degraded: `False`
- assistant_text_preview: `天气、日常小确幸，或者最近看的电影、听的歌，这些轻松的话题都挺适合的。你最近有遇到什么想分享的小事吗？`

### `generated_2`

- prompt_text: `如果现在想换个不费劲的话题，你会往哪个方向拐？`
- input_provenance: `{'source_kind': 'generated', 'source_label': 'local generated ordinary-chat template', 'derivation': 'generated', 'source_ref': 'internal:generated_ordinary_chat_v1:4', 'normalization_applied': False}`
- before_revision: `4`
- send_transport: `python`
- fetch_transport: `python`
- observed_revision: `5`
- runtime_action: `chat`
- parser_source: `semantic_parser`
- subject_gate_ok: `True`
- oe_available: `True`
- reply_authority: `model_chat`
- reply_origin: `chat_mainline`
- host_only: `False`
- degraded: `False`
- assistant_text_preview: `我可能会聊聊最近发现的有趣小物件，或者小时候的糗事，这些都不费脑。你呢，平时放松时会聊什么？`

### `curated_chatlog`

- prompt_text: `要是隔了一会儿再继续聊天，你通常会从哪里重新接上？`
- input_provenance: `{'source_kind': 'chatlog_curated', 'source_label': 'repo seed: light reconnect', 'derivation': 'rewritten', 'source_ref': 'internal:chatlog_curated_v1:chatlog_seed_light_reconnect', 'normalization_applied': True}`
- before_revision: `5`
- send_transport: `python`
- fetch_transport: `python`
- observed_revision: `6`
- runtime_action: `chat`
- parser_source: `chat_default`
- subject_gate_ok: `True`
- oe_available: `True`
- reply_authority: `model_chat`
- reply_origin: `chat_mainline`
- host_only: `False`
- degraded: `False`
- assistant_text_preview: `我通常会从上回聊到的那件小事接着往下说，比如“你刚提到那个……后来怎么样了？”或者直接分享一个新发现的有趣小物件，让对话自然接上。`

## Claim Ceiling

- This run records one dedicated dashboard_chat live window only.
- Mixed-source prompts retain parity only inside dashboard-only strengthened evidence.
- It does not prove Stage 1 closeout, cross-entrypoint proof, runtime efficacy, live user benefit, or consciousness-like properties.
