# EGO-FS-104 Lifestyle Review Evidence Excerpts v0

## Goal

Make lifestyle-trial human review faster by embedding bounded transcript and
trace excerpts directly in the review packet for sessions that still require
human review.

## Problem Reframe

EGO-FS-103 made the review packet concrete, but it still required the reviewer
to open every transcript and trace path manually before making verdicts. The
next safe improvement is not another synthetic proof run; it is reducing the
friction of reviewing real evidence while preserving the human gate.

## Authority Source

- `Tasks/TASK_BOARD.yaml`
- `docs/codex/tasks/ego-functional-subject-lifestyle-trial-active-v0/state/functional_subject_lifestyle_trial_observation.json`
- `scripts/functional_subject_lifestyle_trial.py`

## Change Surface

- Add bounded file excerpts to `--review-packet`.
- Add an excerpt-length option for review packets.
- Add tests for existing, missing, and truncated excerpt behavior.
- Update active-trial runbook and pursue-goal records.

## Out Of Scope

- No automatic human verdicts.
- No #94 closeout from excerpts alone.
- No EgoOperator runtime, memory, tool, approval, training, program-state,
  evidence-ledger, GitHub truth-source, or legacy behavior changes.

## Acceptance

- Review packet sessions include `evidence_excerpts` for transcript and trace
  files.
- Missing evidence files are reported as `exists=false` instead of crashing.
- Excerpts are bounded by a configurable character limit.
- Markdown output renders the bounded evidence excerpts for review.
- Tests cover the new excerpt behavior.

## Claim Ceiling

`Functional Subject lifestyle review-excerpt local workflow candidate pass`

This does not prove stable real user benefit, runtime efficacy, live autonomy,
durable memory efficacy, independent personhood, real subjective experience, or
consciousness.
