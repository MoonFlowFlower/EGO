# EgoDesktop PSPC Semantic Interaction Extractor v0 Stage Card

## Problem Reframe

The PSPC Reply Preview overlay showed neutral proxy state for natural companion interactions such as gift, touch, affinity, and trust probes. The issue was not a renderer defect; the preview state updater depended on narrow text-pattern classification.

## One Hypothesis

If EgoDesktop extracts typed semantic interaction events with an LLM helper, then applies only deterministic state deltas from validated event packets, PSPC Reply Preview can observe natural interaction signals without keyword-hardcoded category routing or runtime authority.

## Change Surface

- EgoDesktop reply-preview state and debug overlay
- isolated PSPC signal extraction helper script
- EgoDesktop main/preload event wiring for async preview updates
- targeted tests, docs, artifacts, and state/ledger/generated-view updates

## Authority Source

- Repo authority remains `docs/PROGRAM_STATE_UNIFIED.yaml`.
- PSPC Reply Preview remains local desktop preview-only.
- LLM extraction output is audit/debug data only; deterministic updater owns proxy state changes.

## Boundaries

- claim ceiling: `local_reply_preview_semantic_signal_extractor_only`
- runtime authority: `none`
- persistence: window-lifetime preview state only
- mainline connected: `false`
- enabled as runtime authority: `false`

## Forbidden

- Do not modify EgoOperator runtime, gate, memory, approval, transport, proactive behavior, or human-trial harness.
- Do not create an adapter.
- Do not write real memory.
- Do not let extractor output action, user message, tool call, gate decision, transport, schedule, `enabled=true`, or `mainline_connected=true`.
- Do not claim PSPC true learning, durable memory, runtime integration safety, consciousness, subjective experience, or real emotion.

## Three-Level Verify

1. Unit tests prove semantic event packets update proxy state and forbidden/unavailable packets do not.
2. Integration/static tests prove EgoDesktop wires an async local extractor without hiding chat, registering PSPC, or reintroducing keyword classification in `pspcReplyPreview.js`.
3. Repo checks prove state/route/lint/closeout remain scoped.

## Rollback

Delete the semantic extractor script, EgoDesktop semantic preview updates, tests, this task directory, artifact directory, and matching state/ledger/generated-view entries.

## What This Proves

This proves local EgoDesktop PSPC Reply Preview can consume validated semantic interaction event packets and display traceable proxy state changes for natural companion interactions.

## What This Does Not Prove

It does not prove PSPC mainline integration, true learning, durable memory, EgoOperator runtime integration safety, stable real user benefit, live autonomy, consciousness, subjective experience, or real emotion.
