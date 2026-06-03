# EGO-FS-088: Delayed Memory Transition Replay v0

## Problem Reframe

EGO-FS-010/#94 still needs delayed/fresh-session evidence for the memory
transition cases surfaced by GPT-5.5: `fs15` correction, `fs16` forget, and
`fs17` save. EGO-FS-083 proved one generic approval/revocation path, but did
not prove the three total-gate memory cases as a single audited transition
chain.

## Positive Mechanism Goal

Prove a bounded memory transition replay across fresh runtime sessions:

- `fs17_save`: explicitly approved candidate-local memory is injected after a
  fresh runtime reload and carries an approval audit id.
- `fs15_correction`: a corrected preference supersedes a stale prior memory,
  quarantines the stale core note, and a fresh runtime sees only the corrected
  instruction.
- `fs16_forget`: an approved memory is visible before forget, then revoked by
  the memory gate and absent after a fresh runtime reload.

## Scope

Allowed:

- `scripts/run_ego_experience_trial.py`
- `scripts/tests/test_run_ego_experience_trial.py`
- focused docs/task-board updates

Not allowed:

- `PROJECT_MEMORY.md`
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- legacy runtime
- default memory/policy enablement
- GitHub Project as task truth source

## Acceptance Gate

- Uses isolated operator-memory dir.
- Produces report with audit ids, trace refs, memory ids, core snapshots, and
  failure taxonomy.
- Proves `fs17` save, `fs15` correction, and `fs16` forget across fresh runtime
  sessions.
- Leaves no tool calls and no pending approvals.
- Does not claim durable memory efficacy or production memory correctness.

## Rollback

Remove the runner/tests/docs and keep #94 partial on delayed memory transition
evidence.

## Claim Ceiling

`Functional Subject delayed memory transition replay local/scripted candidate pass`.

This does not prove consciousness, real subjective experience, independent
personhood, stable real user benefit, live autonomy, durable memory efficacy,
runtime efficacy, or production memory correctness.
