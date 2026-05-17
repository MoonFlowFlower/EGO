# Ego Handmade Operator Comparison v1 - SPEC

## Summary

Run a bounded local comparison gate for `Ego_handmade` as an operator-first
replacement candidate. This task checks whether the candidate preserves
natural-language meaning, gate discipline, trace readability, and recovery
behavior without moving the formal EGO mainline.

## Authority Snapshot

- formal mainline remains `subject_system_v1_governed_proactivity`
- `Ego_handmade` is candidate-only
- `ego_desktop_lab` remains lab/reference harness
- `EgoCore` and `OpenEmotion` remain reference/fallback for this task

## Allowed Paths

- `Ego_handmade/**`
- `docs/codex/tasks/ego-handmade-operator-comparison-v1/**`

## Forbidden Paths

- `EgoCore/**`
- `OpenEmotion/**`
- `ego_desktop_lab/**`
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`

## Contract

- Keep the runtime path as `user text -> LLM understanding -> candidate response/plan -> gate`.
- Do not add keyword routing as the first user-message handler.
- Do not turn eval cases into runtime rule tables.
- Do not allow subagents or subject context to write lead memory/todo/state.
- Old systems may be read as references, but must not be modified or archived.

## Claim Ceiling

At most: `Ego_handmade operator comparison local candidate pass`.

Forbidden claims:

- formal EGO mainline replacement
- EgoCore/OpenEmotion/ego_desktop_lab demotion
- live runtime efficacy
- live user benefit
- stable long-term memory efficacy
- consciousness or autonomy claims
