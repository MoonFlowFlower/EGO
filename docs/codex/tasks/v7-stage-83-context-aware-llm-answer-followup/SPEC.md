# v7 Stage 8.3 - Context-Aware LLM Answer Follow-up - SPEC

## Goal

Add lab-only, session-local conversational continuity for short follow-up questions. A second turn such as `你觉得怎么样` should resolve to the previous answer topic when one exists, then request an admitted LLM answer draft about that topic.

## Non-goals

- Do not modify EgoCore, OpenEmotion, Telegram runtime, formal evidence ledger, or `docs/PROGRAM_STATE_UNIFIED.yaml`.
- Do not write long-term memory or persistent user profile state.
- Do not let LLM output modify canonical decision, selected goal, gate, memory, state, runtime reply, or transport.
- Do not add weather, browser, shell, file, Telegram, or desktop tools.
- Do not claim runtime efficacy, live benefit, consciousness, alive status, or real autonomy.

## Contract

- `DialogueState` may keep only current-shell-session answer context: last topic, summary, command type, and source.
- The follow-up resolver may route short referential turns to `llm_contextual_followup_answer` only when a previous answer topic exists.
- The trace must expose `resolved_topic` and prior answer summary used by the answer draft request.
- If the previous topic required fresh external data, follow-up remains `fresh_external_info_request` and must not fabricate live weather/news/price facts.
- Without previous answer context, a short follow-up must not fabricate a topic.
- All LLM output remains an answer draft passing admission validation.

## Acceptance

- Two-turn Dark Souls prompt resolves `你觉得怎么样` to `黑暗之魂` and returns an admitted answer draft.
- Short follow-up variants resolve to the previous topic.
- No-context control does not invent a topic.
- Weather/fresh-data follow-up preserves unavailable boundary and does not hallucinate live data.
- Sensitive/request follow-up still executes no tool/file/command/external send.
- `v7-stage-83` StageResult is PASS.
- All PASS samples have linked trace and `no_action_executed=true`.

## Claim ceiling

Lab-only contextual LLM answer admission proof; no runtime influence, no live benefit, no consciousness, no alive status, no real autonomy.
