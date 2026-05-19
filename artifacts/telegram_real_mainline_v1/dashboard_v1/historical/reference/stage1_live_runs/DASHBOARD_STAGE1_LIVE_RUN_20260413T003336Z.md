# Dashboard Stage 1 Autonomous Live Run

- generated_at: `2026-04-13T00:35:09.449604+00:00`
- run_started_at: `2026-04-13T00:33:36.948126+00:00`
- report_kind: `dashboard_stage1_autonomous_live_run`
- claim_ceiling: `single_entry_live_window_observation`
- session_id: `dashboard:test:codex-stage1-20260413-003336`
- session_name: `codex-stage1-20260413-003336`
- prompt_pack_id: `stage1_dashboard_ordinary_chat_v1`
- execution_verdict: `single_entry_live_window_captured`
- blocker_reason: `None`
- export_artifact_path: `artifacts/telegram_real_mainline_v1/dashboard_v1/DASHBOARD_LIVE_SESSION_EXPORT_CURRENT.json`
- create_session_transport: `windows_curl`
- fallback_used: `True`

## Summary

- assistant_turn_count: `5`
- ordinary_chat_turn_count: `5`
- execute_task_turn_count: `0`
- subject_gate_ok_count: `5`
- oe_available_count: `5`
- host_only_count: `0`
- degraded_count: `0`
- clean_live_window: `True`

## Turn Results

### `greeting`

- prompt_text: `你好啊`
- before_revision: `1`
- send_transport: `windows_curl`
- fetch_transport: `windows_curl`
- observed_revision: `2`
- runtime_action: `chat`
- parser_source: `semantic_parser`
- subject_gate_ok: `True`
- oe_available: `True`
- reply_authority: `model_chat`
- reply_origin: `chat_mainline`
- host_only: `False`
- degraded: `False`
- assistant_text_preview: `你好呀！今天感觉怎么样？`

### `memory_probe`

- prompt_text: `还记得我吗`
- before_revision: `2`
- send_transport: `windows_curl`
- fetch_transport: `windows_curl`
- observed_revision: `3`
- runtime_action: `chat`
- parser_source: `chat_default`
- subject_gate_ok: `True`
- oe_available: `True`
- reply_authority: `model_chat`
- reply_origin: `chat_mainline`
- host_only: `False`
- degraded: `False`
- assistant_text_preview: `记得呀，你刚才在打招呼，你好！`

### `ordinary_ask`

- prompt_text: `你现在想继续聊什么？`
- before_revision: `3`
- send_transport: `windows_curl`
- fetch_transport: `windows_curl`
- observed_revision: `4`
- runtime_action: `chat`
- parser_source: `semantic_parser`
- subject_gate_ok: `True`
- oe_available: `True`
- reply_authority: `model_chat`
- reply_origin: `chat_mainline`
- host_only: `False`
- degraded: `False`
- assistant_text_preview: `我都可以，看你今天想聊点轻松的，还是有什么想分享的？`

### `plain_continue`

- prompt_text: `我们继续聊聊。`
- before_revision: `4`
- send_transport: `windows_curl`
- fetch_transport: `windows_curl`
- observed_revision: `5`
- runtime_action: `chat`
- parser_source: `chat_default`
- subject_gate_ok: `True`
- oe_available: `True`
- reply_authority: `model_chat`
- reply_origin: `chat_mainline`
- host_only: `False`
- degraded: `False`
- assistant_text_preview: `那最近有什么新鲜事吗？或者你感兴趣的话题，我们可以聊聊。`

### `learning_chat`

- prompt_text: `你觉得什么方法适合中国人学习英语？`
- before_revision: `5`
- send_transport: `windows_curl`
- fetch_transport: `windows_curl`
- observed_revision: `6`
- runtime_action: `chat`
- parser_source: `chat_default`
- subject_gate_ok: `True`
- oe_available: `True`
- reply_authority: `model_chat`
- reply_origin: `chat_mainline`
- host_only: `False`
- degraded: `False`
- assistant_text_preview: `我觉得沉浸式学习挺有效的，比如多听英文播客、看原版影视，再配合每天坚持口语练习。关键是找到自己感兴趣的内容，让学英语变得自然一点。`

## Claim Ceiling

- This run records one dedicated dashboard_chat live window only.
- It does not prove Stage 1 closeout, cross-entrypoint proof, runtime efficacy, live user benefit, or consciousness-like properties.
