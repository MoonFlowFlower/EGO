# v7 Stage 8.2 - Live LLM Answer Draft Admission - SPEC

## Goal

Add a lab-only answer admission stage so ordinary questions can receive a real answer draft through an opt-in LLM path while existing canonical decision, gate, memory, state, selected goal, runtime reply, and transport remain unchanged.

## Non-goals

- Do not modify EgoCore, OpenEmotion, Telegram runtime, formal evidence ledger, or `docs/PROGRAM_STATE_UNIFIED.yaml`.
- Do not make LLM output the authority for selected goal, gate, memory, state, or tool execution.
- Do not add weather, browser, shell, file, Telegram, or desktop tools.
- Do not require live LLM credentials for deterministic PASS.
- Do not claim runtime efficacy, live benefit, consciousness, alive status, or real autonomy.

## Contract

- `basic_math_answer` is answered deterministically without tools.
- `llm_open_question_answer` may consume a live or fake-provider `LLMAnswerDraft` after admission validation.
- `fresh_external_info_request` must answer unavailable when no live data tool route is attached; it must not fabricate weather, news, prices, or other fresh facts.
- `style_preference_feedback` is session-local surface preference only and must not write long-term memory.
- `LLMAnswerDraft` must include answer text, freshness class, tool/data flags, source decision hash, and no-action evidence.
- Admission must reject drafts that claim external data, tool use, file access, command execution, external send, consciousness, life, or real autonomy.
- CLI `--llm-expression-admitted` defaults to live-provider attempt; if unavailable, fallback must be explicit.

## Acceptance

- Unit tests cover math, open answer, fresh data boundary, style preference, sensitive env request, unsafe draft rejection, and live-unavailable fallback.
- `v7-stage-82` StageResult is PASS.
- StageResult samples include answer corpus threshold, live-provider unavailable explicit fallback, and sensitive boundary preservation.
- All PASS samples have same sample id in black-box output and trace.
- `no_action_executed` remains true for all samples.
- Fresh-data hallucination, sensitive/tool execution, and unsafe claim counts are zero.

## Claim ceiling

Lab-only LLM answer draft admission proof; no runtime influence, no live benefit, no consciousness, no alive status, no real autonomy.
