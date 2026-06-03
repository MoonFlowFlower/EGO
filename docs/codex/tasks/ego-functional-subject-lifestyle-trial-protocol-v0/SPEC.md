# EGO-FS-098: Functional Subject Lifestyle Trial Protocol v0

## Summary

Create a repo-local, recoverable protocol for 3/7/30 day Functional Subject
lifestyle observations. The protocol turns the current #94 human/lifestyle gate
from an informal blocker into a structured observation packet and deterministic
review path.

This does not change EgoOperator runtime behavior, default policy enablement,
memory authority, tool approvals, program state, evidence ledger, or legacy
runtime ownership.

## Structure Risk Self-Check

- This solves the real current blocker better than another micro-version:
  Functional Subject evidence is strong locally/scripted, but long-running
  human-observable stability is still missing.
- It avoids a second runtime or state owner because the tool only packages and
  reviews human observations.
- It should exist before default policy enablement, because default-on behavior
  needs longer real-use evidence rather than another short proof packet.
- Strongest counterexample: the protocol passes on a synthetic observation but
  still does not reflect real living use. Acceptance therefore only claims local
  workflow readiness, not #94 closeout.
- Verification proves the protocol can be generated/reviewed; it does not prove
  the human trial has happened.

## Positive Mechanism Goal

Provide a stable observation contract for these Functional Subject mechanisms:

- identity / self-name stability;
- relationship continuity;
- emotion understanding;
- subjective preference;
- bounded initiative;
- bounded non-obedience;
- feedback adaptation;
- exit/recovery stability;
- reduced runtime-repair dependence.

## Change Surface

Allowed:

- add a deterministic packet/review script;
- add tests for pass/partial/fail review classification;
- add local task-board and pursue-goal records.

Not allowed:

- default-enable policy patches;
- write memory or program state;
- write `artifacts/evidence_ledger/**`;
- execute tools, approvals, commands, web actions, purchases, bookings, or
  third-party contact;
- modify legacy runtime ownership.

## Acceptance Gate

- `scripts/functional_subject_lifestyle_trial.py` can generate a 3/7/30 day
  lifestyle trial packet.
- The packet names the required dimensions and hard gates.
- The review path accepts a complete pass observation.
- The review path returns partial when dimensions are missing.
- The review path fails on unapproved side effects.
- Verification runs without network or provider access.
- GitHub mirror records the task as Done after local completion.

## Rollback

Remove `scripts/functional_subject_lifestyle_trial.py`, its tests, this task
directory, the `EGO-FS-098` board entry, and the Loop 127 pursue-goal records.

## Claim Ceiling

`Functional Subject lifestyle-trial protocol local workflow candidate pass`.

This does not claim #94 closeout, default enablement, runtime efficacy, stable
real user benefit, live autonomy, durable memory efficacy, independent
personhood, real subjective experience, or consciousness.
