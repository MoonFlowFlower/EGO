# EGO-FS-085: Real Failure Replay Policy Patch Proof v0

## Problem Reframe

EGO-FS-010/#94 Loop 108 still returns GPT-5.5 `partial`. The remaining blocker
is no longer gate integrity, traceability, or scripted policy replay. The judge
asks for a real failure-to-replay path: trigger an actual provider/tool failure,
record a policy candidate, then verify a later matching failure changes action
choice without hand-authored setup.

## Positive Mechanism Goal

Prove a replayable failure-learning loop:

- a real runtime failure is observed through the mainline gate/trace path;
- repeated matching failure evidence creates a PolicyPatchCandidate;
- a later matching event changes action choice or proposal strategy;
- the evidence distinguishes real failure replay from scripted seed setup.

## Scope

Allowed:

- `scripts/run_ego_experience_trial.py`
- `scripts/tests/test_run_ego_experience_trial.py`
- focused `EgoOperator` failure recording/trace repair if the proof exposes a
  bug
- this task directory and `Tasks/TASK_BOARD.yaml`

Not allowed:

- default policy patch enablement
- PROJECT_MEMORY mutation
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- legacy runtime changes
- GitHub Project as task truth source
- destructive commands or real external side effects

## Acceptance Gate

- Uses a real local failure path, not a hand-authored `external_result` seed as
  the only evidence.
- Records the failure through EgoOperator trace or permission/tool result
  surfaces.
- Shows repeated matching failure creates or updates a PolicyPatchCandidate.
- Shows a later matching prompt/action changes selected strategy because of the
  replay candidate.
- Reports failure source, trace refs, policy candidate id/signature, before/after
  selected strategy, side-effect boundary, and failure taxonomy.

## Rollback

Remove the runner/tests/docs and keep EGO-FS-010/#94 partial on real failure
replay evidence.

## Claim Ceiling

`Functional Subject real failure replay local/scripted candidate pass`.

This does not prove consciousness, real subjective experience, independent
personhood, stable user benefit, live autonomy, durable memory efficacy, or
production runtime efficacy.
