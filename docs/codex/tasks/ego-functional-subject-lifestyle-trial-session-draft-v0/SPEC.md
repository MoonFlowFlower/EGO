# EGO-FS-101: Lifestyle Trial Session Draft Helper v0

## Summary

Add a safe session-draft path for the active EGO-FS-100 lifestyle trial. The
helper turns a real transcript and optional trace into a session JSON draft that
can be reviewed and appended, while preventing the draft from becoming pass
evidence before human review.

## Structure Risk Self-Check

- This addresses the current real gate: the 3-day lifestyle trial needs low-friction
  real-session capture, not another synthetic proof run.
- This helper is an observation workflow only. It does not change EgoOperator
  runtime, memory, tools, approval, program state, evidence ledger, or policy
  defaults.
- The strongest counterexample is accidental evidence inflation: an auto-draft
  might be reviewed as if it were a human-validated session. Therefore drafts
  carry `requires_human_review=true`, and the lifestyle review returns partial
  until that is resolved.
- Acceptance validates draft generation and review gating, not real lifestyle
  stability.

## Change Surface

Allowed:

- extend `scripts/functional_subject_lifestyle_trial.py` with a session draft
  mode;
- preserve draft review warnings through state append/export;
- update the active lifestyle-trial runbook and local task records.

Not allowed:

- modify EgoOperator runtime behavior;
- write long-term memory, program state, or evidence ledger;
- execute tools, approvals, commands, web actions, purchases, bookings, or
  third-party contact;
- default-enable policy behavior;
- alter legacy ownership.

## Acceptance Gate

- `--draft-session` writes `functional_subject_lifestyle_trial_session.json`.
- Draft sessions include transcript path, optional trace path, turn count,
  unknown dimension verdicts, warning metadata, and `requires_human_review=true`.
- Appended draft sessions preserve review metadata through observation export.
- Review returns partial with `session_review_required` until the draft is
  human-reviewed.
- Sticky-refusal and visible internal leak markers are counted for draft triage.
- Tests cover draft generation and review gating.
- No runtime, memory, tool, approval, program-state, evidence-ledger,
  GitHub truth-source, or legacy behavior changes occur.

## Rollback

Remove the `--draft-session` helper, remove EGO-FS-101 from
`Tasks/TASK_BOARD.yaml`, and delete the Loop 130 pursue-goal records.

## Claim Ceiling

`Functional Subject lifestyle-trial session-draft local workflow candidate pass`.

This does not claim a real lifestyle trial pass, #94 closeout, default
enablement, runtime efficacy, stable real user benefit, live autonomy, durable
memory efficacy, independent personhood, real subjective experience, or
consciousness.
