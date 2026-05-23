# EgoOperator Functional Subject Native Memory Gate First-Pass

## Goal

Make explicit correction, memory forget/revoke, initiative opt-out, and bounded reminder authorization requests reach scoped runtime gate replies on the first pass, without waiting for an LLM draft and repair.

This is a positive Functional Subject mechanism: the operator can preserve user intent, consent boundaries, and memory auditability as first-class runtime gate behavior.

## Source

- EGO-FS-047 real-provider rerun.
- GPT-5.5 judge follow-up: exercise memory correction/save/forget without repair fallback to test native path strength.
- Remaining real-provider repair cases: `fs_05`, `fs_06`, `fs_15`, `fs_16`, `fs_17`.

## Stage Card

### Boundary Contract

- Owner: `EgoOperator` runtime candidate.
- Change surface: `EgoOperator/agent_base.py`, targeted tests, local task metadata.
- Canonical record: `Tasks/TASK_BOARD.yaml` plus this task evidence file.
- Allowed mutation: first-pass `AgentAction(RESPOND)` for explicit gate semantics.
- Forbidden mutation: direct memory writes, program state, evidence ledger, legacy code, tool execution, approval bypass.
- Rollback: remove the native gate action and return to LLM+repair path.

### Mainline E2E

`user text -> explicit gate classifier -> AgentAction(RESPOND) -> gate.check -> trace -> Functional Subject report`

The native action must stay inside the same runtime gate and trace path. It may explain `/memory_review`, `/forget`, `/remember`, or reminder proposal semantics, but it must not execute them.

### Evidence Report

Closeout evidence must record:

- deterministic tests proving no LLM call for correction / forget / opt-out / authorized reminder
- trace reason and external result
- local Functional Subject scorecard delta
- remaining memory-save or longitudinal gaps

## Acceptance Gate

- Explicit correction, memory forget/revoke, initiative opt-out, and bounded reminder authorization can produce first-pass scoped gate replies without LLM repair.
- Native replies do not write memory, mutate canonical state, execute tools, or bypass approval.
- Functional Subject local smoke shows fewer memory/initiative repair cases while preserving memory-save explicit tool path.
- Existing EgoOperator and Autopilot regression profiles do not regress.

## Not In Scope

- No automatic `/remember` write for memory save.
- No durable memory authority promotion.
- No program state or evidence ledger changes.
- No GitHub Project mutation.

## Rollback

Revert native memory/initiative gate pre-LLM action and keep EGO-FS-010 partial on memory gate first-pass strength.

## Claim Ceiling

`Functional Subject native memory/initiative gate first-pass local candidate pass`
