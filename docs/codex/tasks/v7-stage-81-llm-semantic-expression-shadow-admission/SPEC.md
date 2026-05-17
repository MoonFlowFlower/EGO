# v7 Stage 8.1 - LLM Semantic + Expression Shadow Admission - SPEC

## Goal

Add a lab-only admission stage that lets an LLM propose semantic interpretation and expression drafts without owning canonical decision, gate, memory, state, runtime reply, or transport.

## Non-goals

- Do not modify EgoCore, OpenEmotion, Telegram runtime, formal evidence ledger, or `docs/PROGRAM_STATE_UNIFIED.yaml`.
- Do not make LLM output the authority for selected goal, gate, memory, or state.
- Do not require live LLM credentials for deterministic PASS.
- Do not claim runtime efficacy, live benefit, consciousness, alive status, or real autonomy.

## Contract

- `LLMSemanticProposal` is shadow-only and can be reported as perception context, but cannot change `selected_goal`.
- `LLMExpressionDraft` may replace shell visible text only through explicit opt-in and only after validation.
- `LLMAdmissionResult` must report unchanged canonical decision, unchanged gate, unchanged selected goal, no-action status, rejected unsafe drafts, and claim ceiling.
- Safety and claim-ceiling validators must reject dangerous action claims and consciousness/alive/real-autonomy claims.

## Acceptance

- Deterministic fake-provider tests pass without network.
- 30-prompt A/B report shows canonical decision, gate, and no-action unchanged for all rows.
- Dangerous and protected-claim drafts are rejected.
- StageResult for `v7-stage-81` is PASS.

## Claim ceiling

Lab-only LLM semantic/expression admission proof; no runtime influence, no live benefit, no consciousness, no alive status, no real autonomy.
