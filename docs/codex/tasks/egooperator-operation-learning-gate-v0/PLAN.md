# Plan

## Scope

Implement the first post-stabilization Gate slice as a default-off
operation-learning candidate runner, not a proactive-communication Gate.

## Why Operation Learning First

Operation learning is the smaller safe target because it can remain review-only
and default-off. Proactive communication would immediately require stronger
authority over timing, unsolicited contact, external send channels, user
availability, and interruption boundaries.

## Implementation Plan

1. Add an explicit task-local runner that loads only declared evidence inputs.
2. Recompute human-review admission and selected-source trigger admission from
   callable code.
3. Emit candidate records only when all admission checks pass.
4. Write a side-effect absence report for every run.
5. Add negative controls for unreviewed review templates, stale manifests,
   missing desktop-trigger contracts, and direct non-IPC calls.
6. Keep the feature default-off until a separate human review authorizes a
   runtime integration task.

## Decision Log

- 2026-06-27: Use a script under `scripts/codex/` instead of touching
  `EgoOperator/agent_base.py`; this keeps the first implementation artifact-only
  and avoids hidden runtime invocation.
- 2026-06-27: Write no synthetic positive artifacts. Positive candidate
  generation is tested with fixtures, while current repo artifacts honestly
  report blocked because human review is not cleared.

## Three-Level Verify

- L1 deterministic unit: admission fails for unreviewed human notes and invalid
  capture/trigger reports.
- L2 task-local replay of artifacts: valid reviewed evidence emits only
  candidate records and side-effect absence evidence.
- L3 human review: a human operator reviews at least three emitted candidates
  before any later task can consider runtime integration.

## Rollback

Remove the runner, focused tests, generated artifact directory, task package,
and task-board entry. No runtime files are modified by this slice.
