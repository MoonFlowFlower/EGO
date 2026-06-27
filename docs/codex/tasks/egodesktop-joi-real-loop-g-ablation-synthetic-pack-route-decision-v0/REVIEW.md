# EgoDesktop Joi Real-Loop G-ABLATION Synthetic-Pack Route Decision v0 Review

## Pending Claude Review

- reviewer: `desktop Claude / source-limited`
- status: `pending`
- requested verdict format:
  - `NO_BLOCKING_FINDINGS`, with next minimal action; or
  - `BLOCKING_FINDINGS`, with numbered blockers, required repairs, and next minimal action.

## Review Scope

Claude should review only the docs-only route decision:

- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- `MUTATION_SCOPE.yaml`
- `Tasks/TASK_BOARD.yaml` entry `EGODESKTOP-GABLATION-012`
- preserved `EGODESKTOP-GABLATION-011` review/status/spec updates

Claude should not treat this as permission to create another synthetic prompt pack, capture `CREATURE_ON`, run same-access
baselines, score, compare, emit a verdict, update program state/evidence ledger, push, tag, or remote-anchor.

## Claude Review 1

- reviewer: `desktop Claude / source-limited`
- verdict: `BLOCKING_FINDINGS`

Accepted review findings:

- 012 closes or downgrades the synthetic prompt-pack route without claiming empirical saturation, attribution failure, or
  mechanism evidence.
- 011 `SPEC.md`, `STATUS.md`, and `REVIEW.md` preserve the blocked state and both Claude review rounds.
- 012 keeps the future real captured desktop-chat-turn option separate as a later task card with explicit capture
  authority.

Blocking finding:

- B-012-1: `Tasks/TASK_BOARD.yaml` still marked `EGODESKTOP-GABLATION-011` as `active` while 011 docs were blocked, and
  its nominal 160-family acceptance line could be misread as validated effective independence despite Claude B-011-5.

Repair:

- The 011 task-board entry now uses `status: blocked`, includes `superseded_by: EGODESKTOP-GABLATION-012`, and rewrites
  the nominal family-count acceptance line to state that effective independence is unproven and blocks 011 acceptance.

## Claude Review 2

- reviewer: `desktop Claude / source-limited`
- verdict: `NO_BLOCKING_FINDINGS`

Reviewer readback after B-012-1 repair:

- `Tasks/TASK_BOARD.yaml` now records `EGODESKTOP-GABLATION-011` as `status: blocked`.
- `EGODESKTOP-GABLATION-011` now includes `superseded_by: EGODESKTOP-GABLATION-012`.
- The 011 acceptance line now states that the 160/160 family count is nominal and that effective independence is
  unproven because Claude v2 found repeated-template collapse.
- Frozen 011 hashes remain unchanged, preserving the failed preregistration artifacts.
- 012 `STATUS.md` and `REVIEW.md` preserve B-012-1 and the repair.

Next minimal action from reviewer: commit locally only. Do not create synthetic prompt-pack v3, capture, score, emit a
verdict, update program state/evidence ledger, push, tag, or remote-anchor.
