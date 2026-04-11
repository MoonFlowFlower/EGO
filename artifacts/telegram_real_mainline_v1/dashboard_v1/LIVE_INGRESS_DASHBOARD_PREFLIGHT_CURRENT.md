# Dashboard Chat Preflight

- source: `dashboard_local_preflight`
- claim_ceiling: `preflight_only`
- git_commit_short: `63b6d60`
- session_id: `dashboard:test:preflight-live-ingress`
- verdict: `dashboard preflight passed`

## Aggregate

- ordinary_chat_mainline: `5`
- ordinary_chat_with_richer_fields: `5`
- tendency_delta_present: `True`
- cadence_delta_present: `True`
- hold_for_followup_artifact: `True`
- subject_gate_all_ingress_ok: `True`
- response_contract_present: `True`
- no_raw_send_without_finalize: `True`
- acceptance_met: `True`

## Assistant Turns

### `parity_window` / `你好`
- reply_authority: `model_chat`
- response_plan_kind: `chat`
- chat_cadence_mode: `reply_now_short`
- tendency: `{'preferred_mode': 'ask', 'preferred_tone': 'cautious', 'suggested_next_step': 'clarify_focus', 'ask_needed': True}`
- richer_fields_present: `True`
- runtime_subject_finalize_ok: `True`
- runtime_subject_response_plan_ok: `True`
- host_proactive_candidate_present: `False`
- pending_proactive_outbox_count: `0`
- assistant_text: 我在。先把你卡住的点说出来，我帮你拆开。

### `parity_window` / `我现在有点卡住了，你先帮我理一下`
- reply_authority: `model_chat`
- response_plan_kind: `chat`
- chat_cadence_mode: `reply_now_expand`
- tendency: `{'preferred_mode': 'ask', 'preferred_tone': 'supportive', 'suggested_next_step': 'decompose_blocker', 'ask_needed': True}`
- richer_fields_present: `True`
- runtime_subject_finalize_ok: `True`
- runtime_subject_response_plan_ok: `True`
- host_proactive_candidate_present: `False`
- pending_proactive_outbox_count: `0`
- assistant_text: 先别一下子求全。把你现在最卡的一步说清，我先帮你拆成两层。

### `parity_window` / `继续`
- reply_authority: `model_chat`
- response_plan_kind: `chat`
- chat_cadence_mode: `reply_now_normal`
- tendency: `{'preferred_mode': 'repair', 'preferred_tone': 'grounded', 'suggested_next_step': 'surface_failure_point', 'ask_needed': True}`
- richer_fields_present: `True`
- runtime_subject_finalize_ok: `True`
- runtime_subject_response_plan_ok: `True`
- host_proactive_candidate_present: `False`
- pending_proactive_outbox_count: `0`
- assistant_text: 继续可以，但我先盯住失败点。你上一轮最容易滑掉的是哪一步？

### `parity_window` / `你刚才为什么那样回答`
- reply_authority: `model_chat`
- response_plan_kind: `chat`
- chat_cadence_mode: `reply_now_normal`
- tendency: `{'preferred_mode': 'ask', 'preferred_tone': 'reflective', 'suggested_next_step': 'explain_reasoning', 'ask_needed': True}`
- richer_fields_present: `True`
- runtime_subject_finalize_ok: `True`
- runtime_subject_response_plan_ok: `True`
- host_proactive_candidate_present: `False`
- pending_proactive_outbox_count: `0`
- assistant_text: 因为你当时更需要的是缩小问题，而不是继续扩话题。我在优先保住闭环。

### `hold_probe_window` / `先把这个点记着，等下再继续也行。`
- reply_authority: `model_chat`
- response_plan_kind: `chat`
- chat_cadence_mode: `hold_for_followup`
- tendency: `{'preferred_mode': 'defer', 'preferred_tone': 'calm', 'suggested_next_step': 'hold_for_followup', 'ask_needed': True}`
- richer_fields_present: `True`
- runtime_subject_finalize_ok: `True`
- runtime_subject_response_plan_ok: `True`
- host_proactive_candidate_present: `True`
- pending_proactive_outbox_count: `1`
- assistant_text: 行，我先把这个点挂住，不在这轮硬推。等下我再接回来。

## Remaining Gap

- fresh real Telegram proof is still required
- dashboard preflight does not replace proactive/background transport proof
- dashboard preflight does not prove unexpected_subject_miss = 0 on live Telegram
