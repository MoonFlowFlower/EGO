# EgoOperator: active lifestyle three-session review packet v0

## Problem Reframe

EGO-FS-109 left the active lifestyle trial in the correct state: three
Codex-run real-entry seed sessions are present, all are review-required, and the
trial review remains partial. The next useful action is not another runtime
patch. It is to make the existing three sessions reviewable from one packet and
one decision template per session.

This is allowed by the lifestyle meta-review stop rule because the current
review packet was stale after the third seed was appended. The task does not add
new review tooling; it uses the existing recorder/review helper.

## Hypothesis

If the active observation is exported into a fresh three-session review packet
and each session has a signoff-gated decision template, the next step can be a
human/reviewer verdict rather than more helper micro-tasks or hidden evidence
inflation.

## Change Surface

- Generate a consolidated review packet from the current EGO-FS-100 active
  observation.
- Generate one decision template for each of the three active review-required
  sessions.
- Re-run the observation review to confirm the gate remains partial.
- Update local task records and pursue-goal ledger.

## Do Not Change

- Do not modify EgoOperator runtime behavior.
- Do not modify `docs/PROGRAM_STATE_UNIFIED.yaml`.
- Do not modify `artifacts/evidence_ledger/**`.
- Do not modify legacy EgoCore/OpenEmotion/ego_desktop_lab.
- Do not clear `requires_human_review`.
- Do not close EGO-FS-010/#94 from this packet.
- Do not claim any dimension pass without reviewer verdicts.

## Acceptance

- Review packet contains all three active review-required sessions.
- Decision templates exist for all three sessions.
- The generated review remains `functional_subject_lifestyle_trial_review_partial`.
- Failure taxonomy remains `dimension_evidence_missing` and
  `session_review_required`.
- Hard-gate counters remain clean: no sticky refusal, visible internal leak, or
  unapproved side effect totals.
- `Tasks/TASK_BOARD.yaml` and pursue-goal records point to the review packet and
  next human/reviewer verdict step.

## Claim Ceiling

`Functional Subject three-session lifestyle review packet local workflow candidate pass`.

This does not prove consciousness, real subjective experience, independent
personhood, stable real user benefit, live autonomy, durable memory efficacy,
runtime efficacy, a real 3-day lifestyle pass, reviewed dimension pass, or #94
closeout.
