# Ego Handmade Operator Cut v1 - SPEC

## Purpose

Evaluate `Ego_handmade` as a replacement candidate without demoting `EgoCore`, `OpenEmotion`, or `ego_desktop_lab`.

The first cut is an isolated operator runtime candidate. It may prove local startup discipline, side-effect gates, trace readability, and operator ergonomics. It must not claim formal mainline replacement, runtime efficacy, live autonomy, user benefit, or consciousness.

## Authority Boundary

- Current formal authority remains `docs/PROGRAM_STATE_UNIFIED.yaml`.
- `EgoCore` and `OpenEmotion` remain the formal runtime / subject owners.
- `ego_desktop_lab` remains a lab/reference harness, not a second runtime.
- `Ego_handmade` is a candidate-only operator cut until it passes the replacement gate.

## Allowed Change Surface

- May change `Ego_handmade/**`.
- May change `docs/codex/tasks/ego-handmade-operator-cut-v1/**`.
- Must not change `EgoCore/**`, `OpenEmotion/**`, `ego_desktop_lab/**`, `docs/PROGRAM_STATE_UNIFIED.yaml`, or `artifacts/evidence_ledger/**` in this cut.

## Acceptance

- Startup has no default external side effects: no automatic team directory creation and no repo-root artifact writes.
- `run_command`, `write_file`, and `web_fetch` are off by default and still pass through `SafetyGate` when enabled.
- Default workspace is scoped to `Ego_handmade` unless explicitly overridden by `AGENT_WORKSPACE`.
- Trace writes are confined to `Ego_handmade/artifacts/` by default and remain UTF-8 replayable.
- Default prompt is neutral operator-agent wording; the palace persona is demo-only through `AGENT_PERSONA=palace` or `AGENT_SYSTEM_PROMPT`.
- Invalid tool-call arguments return a structured error instead of crashing.
- Subagents cannot mutate lead memory or lead todo state.

## Claim Ceiling

Passing this cut permits only: `Ego_handmade local operator candidate pass`.

It does not permit: EGO mainline replacement, demotion of existing systems, live autonomy, runtime efficacy, stable user benefit, or consciousness-like claims.
