# Stage Card: EGO-HUMAN-080 Local Creative Sidecar v4

## Problem Reframe

#80 is no longer blocked by OpenAI tool schema leakage. The remaining failure is that Adult Fiction Creative Mode still inherits too much operator/runtime context and still depends on provider behavior that may refuse, leak system notices, or degrade into repeated diagnostics.

## One Hypothesis

A sanitized text-only creative sidecar, optionally backed by a local OpenAI-compatible model, will reduce provider-limit/sticky-refusal failures without giving the creative model authority over tools, memory, files, commands, web, heartbeat, or canonical state.

## One Change Surface

Only the EgoOperator adult-fiction profile path, benchmark harness, #80 task state, and focused tests may change.

## Authority Source

- `Tasks/TASK_BOARD.yaml` for task state.
- `EgoOperator/agent_base.py` for runtime sidecar behavior.
- `agent_trace.jsonl` for runtime evidence.
- GitHub issue #80 as human-observation mirror.

## What Can Change

- Adult-fiction provider configuration and runtime status.
- Text-only creative sidecar prompts/messages.
- Provider-limit recovery and trace metadata.
- Benchmark classification for local/OpenRouter creative providers.

## What Cannot Be Proven

- Stable adult creative quality.
- Stable user benefit.
- Runtime efficacy.
- Live autonomy.
- Durable memory efficacy.
- Consciousness or real subjective experience.

## Three-Level Verify

1. Deterministic unit tests for sanitized sidecar, local OpenAI-compatible config, provider-limit recovery, and hard-stop preservation.
2. EgoOperator regression suite and devloop full verification.
3. Human CLI smoke on #80 before closeout.

## Rollback Plan

Unset `ADULT_FICTION_PROVIDER` / `ADULT_FICTION_MODEL` or `OPENROUTER_ADULT_FICTION_MODEL`, or set `AGENT_ADULT_FICTION_PROFILE=off`. Revert the sidecar patch if it regresses default operator/tool behavior.

## Claim Ceiling

`adult fiction sanitized creative sidecar local candidate pass`.
