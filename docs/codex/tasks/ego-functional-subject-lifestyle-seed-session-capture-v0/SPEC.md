# EGO-FS-102: Lifestyle Trial Seed Session Capture v0

## Summary

Run a short real EgoOperator CLI seed session, capture its transcript and trace
slice, draft a session JSON, append it to the active EGO-FS-100 lifestyle trial
state, and verify that the active trial review remains partial until human
review.

## Structure Risk Self-Check

- This addresses the current real gate: EGO-FS-100 needs real entrypoint
  sessions, not more harness-only preparation.
- This is still a Codex-run seed session, not a human 3-day lifestyle trial.
  Therefore it must not satisfy #94 closeout or default enablement.
- The strongest counterexample is evidence inflation: appending a scripted seed
  session could be mistaken for completed lifestyle evidence. The session stays
  `requires_human_review=true`, all dimension verdicts remain `unknown`, and
  the active review returns partial with `session_review_required`.
- Acceptance validates real-entry capture and gating, not stable real-use
  behavior.

## Change Surface

Allowed:

- run a short EgoOperator CLI session with real provider configuration;
- create temporary transcript/trace evidence under `/tmp`;
- append the review-required session draft to the EGO-FS-100 active state;
- update local task-board and pursue-goal records.

Not allowed:

- claim the 3-day lifestyle trial passed;
- close #94;
- default-enable policy behavior;
- write long-term memory, program state, or evidence ledger;
- execute external side effects, purchases, bookings, third-party contact, or
  unapproved tools;
- alter legacy ownership.

## Acceptance Gate

- A real EgoOperator CLI seed transcript exists under `/tmp`.
- A trace slice exists under `/tmp`.
- `--draft-session` produces a session JSON with `requires_human_review=true`.
- The session is appended to the EGO-FS-100 active state.
- The active observation review returns partial with `session_review_required`.
- Sticky refusal, visible internal leak, and unapproved side-effect counts are
  zero in the structured session/review.
- No program-state/evidence-ledger/legacy/default-policy mutation occurs.

## Rollback

Remove the appended seed session from
`docs/codex/tasks/ego-functional-subject-lifestyle-trial-active-v0/state/functional_subject_lifestyle_trial_state.json`,
regenerate the active observation JSON, remove EGO-FS-102 from
`Tasks/TASK_BOARD.yaml`, and delete the Loop 131 pursue-goal records.

## Claim Ceiling

`Functional Subject lifestyle seed-session capture local/real-entry candidate pass`.

This does not claim a real 3-day lifestyle trial pass, #94 closeout, default
enablement, runtime efficacy, stable real user benefit, live autonomy, durable
memory efficacy, independent personhood, real subjective experience, or
consciousness.
