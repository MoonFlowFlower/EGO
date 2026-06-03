# EGO-FS-099: Functional Subject Lifestyle Trial Recorder v0

## Summary

Extend the lifestyle-trial protocol into a recoverable local trial state:
initialize a 3/7/30 day trial, append session observations over time, export a
reviewable observation JSON, and keep the whole path outside EgoOperator
runtime behavior.

## Structure Risk Self-Check

- This addresses the real current gate: long-running human/lifestyle evidence is
  missing, and a packet alone is not enough to survive interruptions.
- It does not create a second runtime, memory owner, or policy authority. The
  state file is an observation artifact only.
- It should precede any default policy enablement or #94 closeout discussion,
  because those need recoverable real-use evidence.
- Strongest counterexample: a synthetic state can pass while real conversation
  still fails. This task therefore only claims recorder workflow readiness.
- Acceptance proves init/append/export/review mechanics, not real lifestyle
  success.

## Positive Mechanism Goal

Make long-running observation practical for these Functional Subject mechanisms:

- stable self-name / identity continuity;
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

- extend `scripts/functional_subject_lifestyle_trial.py`;
- add tests for state init, append, export, and review;
- update task-board and pursue-goal records.

Not allowed:

- modify EgoOperator runtime behavior;
- write memory, program state, or evidence ledger;
- execute tools or approvals;
- train a model;
- default-enable policy behavior;
- alter legacy ownership.

## Acceptance Gate

- A trial state can be initialized with `--init-trial`.
- A session JSON can be appended to the state with `--append-session`.
- A reviewable observation JSON can be exported with `--export-observation`.
- The exported observation can be reviewed by the existing review path.
- Tests cover init/append/export and existing pass/partial/fail review behavior.
- No runtime, memory, tool, approval, program-state, evidence-ledger, GitHub
  truth-source, or legacy behavior changes occur.

## Rollback

Revert the state/append/export additions to
`scripts/functional_subject_lifestyle_trial.py`, remove the added tests, remove
this task directory, remove `EGO-FS-099` from `Tasks/TASK_BOARD.yaml`, and
delete the Loop 128 pursue-goal records.

## Claim Ceiling

`Functional Subject lifestyle-trial recorder local workflow candidate pass`.

This does not claim #94 closeout, default enablement, runtime efficacy, stable
real user benefit, live autonomy, durable memory efficacy, independent
personhood, real subjective experience, or consciousness.
