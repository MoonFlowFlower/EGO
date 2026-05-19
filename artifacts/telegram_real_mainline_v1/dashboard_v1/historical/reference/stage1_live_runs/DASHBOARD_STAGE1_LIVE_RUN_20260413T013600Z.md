# Dashboard Stage 1 Autonomous Live Run

- generated_at: `2026-04-13T01:37:18.921452+00:00`
- run_started_at: `2026-04-13T01:36:00.243635+00:00`
- report_kind: `dashboard_stage1_autonomous_live_run`
- claim_ceiling: `single_entry_live_window_observation`
- session_id: `dashboard:test:codex-stage1-20260413-013600`
- session_name: `codex-stage1-20260413-013600`
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
- ordinary_chat_turn_count: `4`
- execute_task_turn_count: `1`
- subject_gate_ok_count: `5`
- oe_available_count: `5`
- host_only_count: `0`
- degraded_count: `0`
- clean_live_window: `True`
- recent_consecutive_clean_runs: `3`
- recent_same_blocker_count: `0`
- dashboard_only_stability_strengthened: `True`
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
- assistant_text_preview: `你好，很高兴见到你！有什么想聊的吗？`

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
- assistant_text_preview: `都可以，你最近有什么新鲜事想分享吗？`

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
- assistant_text_preview: `轻松时我喜欢聊聊生活中的小确幸，比如偶然遇见的好天气或一本有趣的书。你平时会用哪些话题放松聊天呢？`

### `generated_2`

- prompt_text: `如果现在想换个不费劲的话题，你会往哪个方向拐？`
- input_provenance: `{'source_kind': 'generated', 'source_label': 'local generated ordinary-chat template', 'derivation': 'generated', 'source_ref': 'internal:generated_ordinary_chat_v1:4', 'normalization_applied': False}`
- before_revision: `4`
- send_transport: `python`
- fetch_transport: `python`
- observed_revision: `5`
- runtime_action: `execute_task`
- parser_source: `semantic_parser`
- subject_gate_ok: `True`
- oe_available: `True`
- reply_authority: `model_chat`
- reply_origin: `chat_mainline`
- host_only: `False`
- degraded: `False`
- assistant_text_preview: `我会往「可爱动物/自然趣事」方向拐，比如最近看到的松鼠囤坚果视频，或者窗台上突然来访的小鸟。这类话题不需要深度思考，还能带来一点治愈感。你最近有遇到什么让人会心一笑的小瞬间吗？`

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
- assistant_text_preview: `通常我会顺着对话最后的方向自然接上，比如我们刚聊的话题。不过你希望接下来聊点什么呢？`

## Claim Ceiling

- This run records one dedicated dashboard_chat live window only.
- Mixed-source prompts retain parity only inside dashboard-only strengthened evidence.
- It does not prove Stage 1 closeout, cross-entrypoint proof, runtime efficacy, live user benefit, or consciousness-like properties.
