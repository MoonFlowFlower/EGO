# EGO-FS-105 Lifestyle Session Review Apply Helper v0

## Goal

Provide a reversible helper for applying an explicit human review decision to a
lifestyle-trial session JSON without letting Codex or the runtime infer the
verdict automatically.

## Problem Reframe

EGO-FS-104 made evidence easier to inspect, but applying the result still
required manual JSON editing. The next safe step is an apply helper that consumes
a reviewer-authored decision file and writes a reviewed session artifact while
preserving the human gate.

## Authority Source

- `Tasks/TASK_BOARD.yaml`
- `scripts/functional_subject_lifestyle_trial.py`
- `docs/codex/tasks/ego-functional-subject-lifestyle-trial-active-v0/state/functional_subject_lifestyle_trial_observation.json`

## Change Surface

- Add a session-review decision template command.
- Add an apply command that consumes a decision file and session JSON.
- Add tests for signoff-gated clearing, no-signoff guard behavior, and session
  mismatch rejection.
- Update active-trial runbook and pursue-goal records.

## Out Of Scope

- No automatic verdict generation.
- No active state mutation from the apply command.
- No #94 closeout from a reviewed-session artifact alone.
- No EgoOperator runtime, memory, tool, approval, training, program-state,
  evidence-ledger, GitHub truth-source, or legacy behavior changes.

## Acceptance

- `--session-review-template` writes a decision template with all required
  dimensions and hard-gate counts.
- `--apply-session-review` updates verdicts/counts from a decision JSON.
- `requires_human_review` clears only when both `reviewer_signoff=true` and
  `clear_requires_human_review=true`.
- A session-id mismatch is rejected.
- Generated reviewed session metadata records the reviewer, source decision
  path, and that the artifact does not auto-close #94.

## Claim Ceiling

`Functional Subject lifestyle session-review apply local workflow candidate pass`

This does not prove stable real user benefit, runtime efficacy, live autonomy,
durable memory efficacy, independent personhood, real subjective experience, or
consciousness.
