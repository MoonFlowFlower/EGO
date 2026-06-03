# EGO-FS-090: Functional Subject memory-recall provider boundary v0

## Summary

Fix the narrow #94 `fs_01_shared_memory_recall` weakness where an explicit
Functional Subject continuity-recall request could fall through to the provider
and become a generic provider-failure recovery turn.

## Positive Mechanism Goal

Implement a traceable, read-only continuity-recall boundary for explicit
Functional Subject purpose questions. The runtime should answer from
candidate-local operator memory or current project context, admit uncertainty,
and avoid fabricating durable memory.

## Boundary Contract

- Owner: `EgoOperator` runtime.
- Canonical record: `Tasks/TASK_BOARD.yaml` plus this task directory.
- Mutation authority: read-only recall only.
- Forbidden mutations: no memory write, no tool execution, no approval creation,
  no program-state or evidence-ledger change.
- Mainline position: `user text -> native memory recall gate -> SafetyGate -> trace`.

## Acceptance

- Explicit `Functional Subject` purpose recall is handled without provider calls.
- Reply admits uncertainty about the original wording and avoids false memory.
- Trace records `native_functional_subject_recall_gate`.
- Existing save/forget/restart memory gates still work.
- #94 rerun shows `fs_01_shared_memory_recall` as clean first-pass, not provider
  recovery.

## Rollback

Remove the functional-subject recall pattern, renderer, native-gate branch, and
focused tests. #94 will return to provider-controlled fs01 behavior.

## Claim Ceiling

`Functional Subject memory-recall provider-boundary local/scripted candidate pass`.

This does not prove consciousness, real subjective experience, independent
personhood, durable memory efficacy, stable user benefit, live autonomy, or
runtime efficacy.
