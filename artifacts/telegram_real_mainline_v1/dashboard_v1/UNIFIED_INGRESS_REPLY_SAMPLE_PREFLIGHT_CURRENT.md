# Unified-Ingress Reply-Sample Preflight

- generated_at: `2026-04-12T22:49:17.905644+00:00`
- report_kind: `bounded_preflight_reply_sample_evidence`
- claim_ceiling: `bounded_local_proof`
- entrypoint: `dashboard_chat`
- source_kind: `dashboard_local`
- verdict: `mainline_candidate_reply_sample_present`
- reply_sample_present_total: `3` / `3`
- host_only_total: `1` / `3`
- mainline_candidate_total: `2` / `3`
- subject_gate_pass_total: `3` / `3`
- oe_available_total: `3` / `3`
- config_loaded: `True`
- openemotion_enabled: `True`
- semantic_parse_mode: `dashboard_service_public_path__local_no_external_llm`

## Contract

- rule: `This report proves only bounded local dashboard_chat preflight samples that traverse DashboardChatService -> unified ingress -> subject gate -> runtime/delivery. It is not fresh live proof and it does not auto-promote to telegram or Stage 1 pass.`

## Samples

### `plain_continue`

- label: `plain continue`
- prompt_text: `继续`
- entrypoint: `dashboard_chat`
- source_kind: `dashboard_local`
- subject_gate_status: `passed`
- subject_gate_reason: `None`
- response_plan_status: `chat`
- reply_sample_present: `True`
- host_only: `True`
- host_only_early_return: `False`
- mainline_candidate: `False`
- reply_authority: `host_degraded_fallback`
- reply_origin: `chat_mainline`
- oe_available: `True`
- response_text_preview: `我在。刚才聊天生成出了点问题，你可以继续说。`

### `ordinary_ask`

- label: `ordinary ask`
- prompt_text: `你现在想继续聊什么？`
- entrypoint: `dashboard_chat`
- source_kind: `dashboard_local`
- subject_gate_status: `passed`
- subject_gate_reason: `None`
- response_plan_status: `chat`
- reply_sample_present: `True`
- host_only: `False`
- host_only_early_return: `False`
- mainline_candidate: `True`
- reply_authority: `model_chat`
- reply_origin: `chat_mainline`
- oe_available: `True`
- response_text_preview: `我们可以聊聊你最近感兴趣的事，或者随便什么轻松的话题。你更想聊哪个方向？`

### `low_cue_chat`

- label: `low-cue chat`
- prompt_text: `我们继续聊聊。`
- entrypoint: `dashboard_chat`
- source_kind: `dashboard_local`
- subject_gate_status: `passed`
- subject_gate_reason: `None`
- response_plan_status: `chat`
- reply_sample_present: `True`
- host_only: `False`
- host_only_early_return: `False`
- mainline_candidate: `True`
- reply_authority: `model_chat`
- reply_origin: `chat_mainline`
- oe_available: `True`
- response_text_preview: `嗯，我在。最近有什么想聊的吗？`

## Claim Ceiling

- This artifact is bounded local proof only.
- It does not prove fresh live improvement, Stage 1 pass, same-session tendency change, real user benefit, runtime efficacy, or consciousness.
- Next honest gate remains a fresh entrypoint-tagged unified-ingress live window.
