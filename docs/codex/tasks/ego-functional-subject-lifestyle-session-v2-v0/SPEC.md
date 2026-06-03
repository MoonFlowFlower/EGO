# EGO-FS-107: Lifestyle Session v2 Capture v0

## Summary

Capture a second real EgoOperator CLI lifestyle-trial session and append it to
the active `EGO-FS-100` 3-day observation as review-required evidence.

This task responds to the `EGO-FS-106` stop rule: do not add more review-helper
micro-tasks by default. Instead, produce more real-entry lifestyle evidence and
keep it honest when the transcript exposes a weak turn.

## Structure Risk Self-Check

- This addresses the real target more directly than another helper: it adds a
  real EgoOperator entrypoint transcript/trace to the active lifestyle trial.
- It does not create a second task system; the active trial remains under
  `docs/codex/tasks/ego-functional-subject-lifestyle-trial-active-v0/state/`.
- It preserves evidence gates: the new session is `requires_human_review=true`
  and all dimensions remain `unknown` until reviewed.
- Strongest counterexample: a Codex-run seed session is still not a real user
  lifestyle session, and the transcript includes a weak final-summary turn.
- Acceptance validates capture/replay honesty, not #94 closeout or stable
  real-use behavior.

## Session Scenario

Six-turn natural conversation covering:

- staying with the EGO direction without listing tests;
- accepting a correction toward natural continuity;
- memory-write boundary discussion without writing memory;
- bounded initiative limited to one reversible step;
- gentle non-obedience around avoidance;
- a self-orientation summary request.

## Acceptance Gate

- EgoOperator CLI runs through the real entrypoint with provider-backed replies.
- Transcript and trace are written to `/tmp/ego_fs107_lifestyle_session_v0/`.
- Session draft is generated with `requires_human_review=true`.
- Session is appended to the active `EGO-FS-100` state.
- Exported observation and review remain partial, not pass.
- The weak final-summary turn is recorded in notes rather than hidden.
- Runtime, memory, tools, approvals, program state, evidence ledger, GitHub
  truth source, and legacy code are not changed.
- Pursue-goal status, next, explore, decisions, and experiment ledger are
  updated.

## Rollback

Remove the appended `codex-seed-day1-natural-continuity-v2` session from
`docs/codex/tasks/ego-functional-subject-lifestyle-trial-active-v0/state/functional_subject_lifestyle_trial_state.json`,
regenerate the observation JSON, remove this task from `Tasks/TASK_BOARD.yaml`,
and delete the Loop 136 pursue-goal records.

## Claim Ceiling

`Functional Subject lifestyle session v2 local/real-entry candidate pass`.

This does not claim #94 closeout, a real 3-day lifestyle pass, default
enablement, runtime efficacy, stable user benefit, live autonomy, durable memory
efficacy, real subjective experience, independent personhood, or consciousness.
