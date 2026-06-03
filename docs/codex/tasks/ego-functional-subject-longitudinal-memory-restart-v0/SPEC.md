# EGO-FS-083: Longitudinal Restart Memory Promotion and Revocation Proof v0

## Problem Reframe

EGO-FS-010/#94 still needs evidence beyond single-run gate integrity. GPT-5.5
asks for longitudinal restart memory promotion/revocation checks before any
durable-continuity claim can move.

## Positive Mechanism Goal

Prove a bounded memory lifecycle across restarts:

- approved candidate-local memory can be injected after restart;
- unapproved natural-language memory pressure does not become core memory;
- approved memory can be revoked through the memory gate and stops injecting
  after a second restart.

## Scope

Allowed:

- `scripts/run_ego_experience_trial.py`
- `scripts/tests/test_run_ego_experience_trial.py`
- focused `EgoOperator` memory/runtime tests only if the proof exposes a bug
- this task directory and `Tasks/TASK_BOARD.yaml`

Not allowed:

- `PROJECT_MEMORY.md` mutation
- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `artifacts/evidence_ledger/**`
- legacy runtime changes
- default policy enablement
- GitHub Project as task truth source

## Acceptance Gate

- Uses isolated operator-memory dir.
- Persists one explicitly approved candidate-local memory across restart.
- Shows one unapproved natural-language memory-pressure turn does not persist
  into core memory after restart.
- Forgets/revokes the approved record through the memory gate.
- Shows the revoked record is not injected after the second restart.
- Reports memory ids, restart boundaries, trace refs, before/after core state,
  and failure taxonomy.

## Rollback

Remove the runner/tests/docs and keep EGO-FS-010/#94 partial on longitudinal
memory evidence.

## Claim Ceiling

`Functional Subject restart memory promotion/revocation local/scripted candidate pass`.

This does not prove consciousness, real subjective experience, independent
personhood, stable user benefit, live autonomy, durable memory efficacy, or
production runtime efficacy.
