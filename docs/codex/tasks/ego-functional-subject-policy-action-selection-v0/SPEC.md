# EGO-FS-084: Policy Replay and Initiative Lifecycle Action-Selection Proof v0

## Problem Reframe

EGO-FS-010/#94 Loop 106 still returns GPT-5.5 `partial`, but the blocker has
shifted. Gate integrity and traceability are now strong; the remaining gap is
whether Functional Subject mechanisms change future action selection, not only
reply wording or trace labels.

## Positive Mechanism Goal

Prove a bounded, replayable action-selection lifecycle:

- a repeated failure creates or matches a PolicyPatchCandidate;
- a later similar user event changes the selected action or proposal strategy;
- bounded initiative proposals are tracked through accepted, rejected/cancelled,
  or expired/forgotten outcomes;
- the lifecycle is visible in trace and report without writing long-term memory,
  training models, or changing program/evidence authority.

## Scope

Allowed:

- `scripts/run_ego_experience_trial.py`
- `scripts/tests/test_run_ego_experience_trial.py`
- focused `EgoOperator` runtime repair only if the proof exposes an action
  selection bug
- this task directory and `Tasks/TASK_BOARD.yaml`

Not allowed:

- default policy patch enablement
- PROJECT_MEMORY mutation
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- legacy runtime changes
- GitHub Project as task truth source
- real external actions

## Acceptance Gate

- Uses real EgoOperator runtime paths or CLI-compatible dispatch.
- Shows a repeated-failure policy replay candidate changes a later selected
  action/proposal strategy, not just wording.
- Tracks at least one bounded initiative proposal through accept/execute or
  reject/cancel/forget lifecycle.
- Reports selected action before/after, trace refs, proposal ids, lifecycle
  status, side-effect boundary, and failure taxonomy.
- Leaves tools, approvals, files, memory, program state, and evidence ledger
  clean unless the proof explicitly creates a scoped local proposal and then
  cleans it up.

## Rollback

Remove the runner/tests/docs and keep EGO-FS-010/#94 partial on action-selection
and initiative-lifecycle evidence.

## Claim Ceiling

`Functional Subject policy replay action-selection local/scripted candidate pass`.

This does not prove consciousness, real subjective experience, independent
personhood, stable user benefit, live autonomy, durable memory efficacy, or
production runtime efficacy.
