# EGO-FS-100: Active 3-Day Functional Subject Lifestyle Trial v0

## Summary

Start the first repo-local active 3-day lifestyle trial state for #94 human / lifestyle evidence. This consumes the EGO-FS-099 recorder and creates a recoverable state path that can be appended over time.

## Structure Risk Self-Check

- This addresses the current real gate: actual lifestyle observation needs a concrete active state, not more short scripted proof.
- This state is an observation artifact only; it is not a second memory/state owner and does not affect EgoOperator runtime.
- The strongest counterexample is that no real sessions have been appended yet. Therefore this task only claims active-trial bootstrap, not trial pass.
- Acceptance validates state initialization and runbook readiness, not real-use stability.

## Change Surface

Allowed:

- create the active trial directory and state JSON;
- create a runbook for appending/exporting/reviewing sessions;
- update local task-board and pursue-goal records.

Not allowed:

- modify EgoOperator runtime behavior;
- write long-term memory, program state, or evidence ledger;
- execute tools, approvals, commands, web actions, purchases, bookings, or third-party contact;
- default-enable policy behavior;
- alter legacy ownership.

## Acceptance Gate

- Active state exists at `state/functional_subject_lifestyle_trial_state.json`.
- Export observation exists at `state/functional_subject_lifestyle_trial_observation.json`.
- State schema is `ego_operator.functional_subject_lifestyle_trial_state.v0`.
- State task id is `EGO-FS-100`.
- Planned days is `3`.
- Sessions list is empty at bootstrap and ready for append.
- Runbook explains append, export, review, hard gates, and claim boundary.
- No runtime, memory, tool, approval, program-state, evidence-ledger, GitHub truth-source, or legacy behavior changes occur.

## Rollback

Remove `docs/codex/tasks/ego-functional-subject-lifestyle-trial-active-v0`, remove `EGO-FS-100` from `Tasks/TASK_BOARD.yaml`, and delete the Loop 129 pursue-goal records.

## Claim Ceiling

`Functional Subject active lifestyle-trial bootstrap local workflow candidate pass`.

This does not claim a real lifestyle trial pass, #94 closeout, default enablement, runtime efficacy, stable real user benefit, live autonomy, durable memory efficacy, independent personhood, real subjective experience, or consciousness.
