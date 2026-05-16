# v7 Stage 4.5 - Continuity Runtime Scaffold - PLAN

## Task summary

Implement a lab-only continuity scaffold proving that persisted state, event log, elapsed-time pressure dynamics, controlled tick, gate/no-action, and replay can support active intention without runtime authority.

## Execution mode

- mode: implementation
- why this mode: Stage 4 status explicitly points to Stage 4.5 before Stage 5; the contract is narrow and testable.
- proof required after discovery: targeted tests, operator report, full `ego_desktop_lab` regression, scoped diff check.

## Milestones

### Milestone 0: Task Packet

- type: implementation
- question: can Stage 4.5 be represented as a separate lab task without changing formal state?
- scope: `SPEC.md`, `PLAN.md`, `STATUS.md`.
- acceptance: task package declares lab-only continuity proof and keeps Stage 5 locked.
- rollback note: delete `docs/codex/tasks/v7-stage-45-continuity-runtime-scaffold/`.

### Milestone 1: In-Memory Continuity Contract

- type: implementation
- question: does elapsed time deterministically alter continuity pressure and optionally ignite an existing registered option?
- scope: `ego_desktop_lab/continuity_runtime.py`.
- acceptance: low pressure waits; high stagnation ignites existing `repair_or_replan_goal`; all ticks keep `no_action_executed=true`.
- rollback note: remove `continuity_runtime.py` and its tests.

### Milestone 2: tmp_path Persistence + Replay

- type: implementation
- question: can state and tick records survive reload and replay deterministically?
- scope: `ContinuityStateStore`, `ContinuityEventLog`, `replay_tick_log`.
- acceptance: tests use `tmp_path`, reload state, and replay logged ticks to the same transition.
- rollback note: remove persistence helpers and tests.

### Milestone 3: Operator Report

- type: implementation
- question: can an operator inspect why a tick changed behavior without reading internals?
- scope: `--continuity-runtime-report`.
- acceptance: report shows pressure delta, ignition, selected goal, behavior plan, gate, rate limit, replay, action boundary, and claim ceiling.
- rollback note: remove shell CLI hook and report helper.

## Progress

- current_status: local_pass
- current_milestone: Operator Report
- milestone_state: completed
- candidate_vs_proof: proof_passed

## Decision log

- 2026-05-15: Use a single thin `continuity_runtime.py` file instead of adding a full runtime package; this prevents premature ontology split.
- 2026-05-15: Tick owns only ignition and rate limiting; selected behavior remains owned by existing agency kernel, behavior registry, and gate.
- 2026-05-15: Persistence writes only to caller-supplied roots and tests use `tmp_path`.

## Surprises / discoveries

- Existing v7 kernel can select `repair_or_replan_goal` from high stagnation when continuity maps pressure into the existing pressure-bias path.
- A replay record must include rate-limit configuration to make visible-suggestion suppression deterministic.

## Outcomes / retrospective

- This task proves: lab continuity state can evolve, ignite an existing gated proposal, persist/reload, rate-limit, and replay deterministically.
- This task does not prove: real scheduler, runtime bridge, live proactive behavior, long-term memory, computer skills, or subjective experience.
- Next smallest safe step: operator review of the Stage 4.5 report, then decide whether to plan Stage 5 or add a separate continuity operator trial.
