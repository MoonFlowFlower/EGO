# Stage Card: EGO-HUMAN-080 Scene Contract + Output Admission v5

## Problem Reframe

#80 local Cydonia sidecar is connected and used, but it can still generate outputs that contradict the established adult, voluntary, fictional scene. The runtime currently accepts those bad outputs as story turns, which pollutes later continuation.

## One Hypothesis

A sidecar-only scene capsule plus output admission gate will preserve role/relationship continuity and prevent bad local-model outputs from entering story memory.

## One Change Surface

Only the EgoOperator adult-fiction sidecar path, benchmark classification, #80 task state, and focused tests may change.

## Authority Source

- `Tasks/TASK_BOARD.yaml` for canonical task status.
- `EgoOperator/agent_base.py` for runtime sidecar behavior.
- `agent_trace.jsonl` for runtime evidence.
- GitHub issue #80 as human-observation mirror.

## What Can Change

- Scene capsule construction for the adult-fiction sidecar.
- Output classification/admission for adult-fiction creative replies.
- Timeout/provider-limit recovery semantics for `继续`.
- Benchmark failure classification for scene-contract violations.

## What Cannot Be Proven

- Stable adult creative quality.
- Real CLI #80 closeout.
- Stable user benefit.
- Runtime efficacy.
- Live autonomy.
- Durable memory efficacy.
- Consciousness or real subjective experience.

## Three-Level Verify

1. Deterministic tests for scene-contract rewrite, bad-output isolation, timeout continuation replay, and hard-stop preservation.
2. EgoOperator regression suite and devloop full verification.
3. Human CLI smoke with the local Cydonia sidecar before #80 closeout.

## Rollback Plan

Disable the sidecar with `AGENT_ADULT_FICTION_PROFILE=off` or unset `ADULT_FICTION_MODEL`. Revert the v5 scene capsule/admission patch if it regresses default operator/tool behavior.

## Claim Ceiling

`adult fiction scene contract and output admission local candidate pass`.
