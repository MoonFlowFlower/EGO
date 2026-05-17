# Ego Handmade Operator Cut v1 - PLAN

## Scope

Implement one bounded operator cut for `Ego_handmade` and record the acceptance gate. Do not touch formal runtime, subject-core, desktop-lab, program-state, or evidence-ledger paths.

## Implementation Steps

1. Constrain defaults:
   - default workspace to `Ego_handmade`
   - default trace path to `Ego_handmade/artifacts/agent_trace.jsonl`
   - disable side-effect tools and persistent team by default
   - make trace/team files lazy-created only when the related action runs

2. Make operator behavior neutral:
   - use a neutral default system prompt
   - keep the palace persona available only as an explicit demo mode
   - keep capability and completion claims evidence-bounded

3. Add tests:
   - no-key fallback to `NoLLM`
   - lazy trace creation and UTF-8 replay
   - default side-effect gate blocks
   - workspace containment
   - invalid tool arguments return structured errors
   - subagents do not mutate lead memory/todo

4. Record status:
   - status remains candidate-only until tests pass
   - next step is a five-scenario operator comparison, not demotion

5. Add candidate-local operator memory:
   - store only under `Ego_handmade/memory/`
   - keep CLI default-on while programmatic construction stays no-side-effect by default
   - append raw conversation and token telemetry after each CLI/runtime turn
   - inject bounded core/episodic memory as candidate-local context only
   - allow direct `MEMORY.md` writes only through the explicit `/remember` operator gate
   - write automatic compaction outputs to episodic summaries and candidate core updates, never directly to EGO authority files

6. Add extracted algorithm primitives:
   - record `Ego_handmade/docs/ALGORITHM_INVENTORY.md` with `keep / rewrite / discard / reference-only` decisions for `EgoCore`, `OpenEmotion`, and `ego_desktop_lab`
   - add `Ego_handmade/primitives/subject_context.py` as readonly candidate context only
   - add `Ego_handmade/primitives/runtime_gate.py` as a local gate/claim-ceiling contract
   - add `Ego_handmade/primitives/evals.py` with the 20-case Dark Souls paraphrase suite
   - inject subject context into prompt/trace without making it a router, state writer, or reply owner

## Rollback

Remove or park `Ego_handmade/**` and this task directory. For memory-system rollback specifically, remove `Ego_handmade/memory_system.py`, its `agent_base.py` wiring, `Ego_handmade/tests/test_memory_system.py`, and any local ignored `Ego_handmade/memory/` artifacts. For extracted-primitive rollback, remove `Ego_handmade/primitives/**`, `Ego_handmade/docs/ALGORITHM_INVENTORY.md`, `Ego_handmade/tests/test_extracted_primitives.py`, and the subject-context wiring in `agent_base.py`. No formal authority or evidence-ledger rollback is needed for this cut.
