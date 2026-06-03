# EGO-FS-103 Lifestyle Trial Human Review Packet v0

## Goal

Create a review packet that turns the active `EGO-FS-100` lifestyle-trial
observation into a human-readable and machine-readable checklist for sessions
that still have `requires_human_review=true`.

## Problem Reframe

The active trial can already append real EgoOperator sessions, but the current
blocker is review friction: the user should not need to inspect raw session JSON
by hand before deciding whether a session can count as lifestyle evidence.

## Authority Source

- `Tasks/TASK_BOARD.yaml`
- `docs/codex/tasks/ego-functional-subject-lifestyle-trial-active-v0/state/functional_subject_lifestyle_trial_observation.json`
- `scripts/functional_subject_lifestyle_trial.py`

## Change Surface

- Add a `--review-packet` mode to `scripts/functional_subject_lifestyle_trial.py`.
- Add focused tests for review-packet generation.
- Add this task directory and pursue-goal loop records.

## Out Of Scope

- No EgoOperator runtime changes.
- No memory, tool, approval, default-policy, program-state, evidence-ledger, or
  legacy changes.
- No #94 closeout from a packet alone.

## Acceptance

- Review packet JSON and Markdown are generated from an observation JSON.
- Review-required sessions are listed with transcript paths, trace paths, draft
  warnings, current dimension verdicts, and hard-gate counts.
- The packet includes allowed verdicts and hard-gate questions.
- The packet explicitly says it does not count as pass evidence by itself.
- Tests cover review-required and no-review-required observations.

## Claim Ceiling

`Functional Subject lifestyle review-packet local workflow candidate pass`

This does not prove stable real user benefit, runtime efficacy, live autonomy,
durable memory efficacy, independent personhood, real subjective experience, or
consciousness.
