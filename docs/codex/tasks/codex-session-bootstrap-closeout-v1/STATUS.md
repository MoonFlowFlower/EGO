# Codex Session Bootstrap + Closeout Enforcement v1 STATUS

## Current State

- state: `implemented_pending_verification`
- owner: `codex`
- observation_class: `deterministic_local`
- claim_ceiling: `Codex session bootstrap and closeout gate local workflow candidate pass`

## Goal

Make each new Codex engineering session recover current EGO progress and operating rules from a live, repo-local guard instead of relying on chat memory alone. Make closeout report scoped staging, push state, task-board mirror availability, dirty blockers, and claim ceiling before Codex claims completion.

## Authority Source

- `AGENTS.md`
- `.codex/project_contract.yaml`
- `CODEX_MEMORY.md`
- `scripts/codex_session_guard.py`
- `Tasks/TASK_BOARD.yaml` remains the canonical task board; GitHub Project remains mirror/display only.

## Implementation Notes

- Added `scripts/codex_session_guard.py` with:
  - `bootstrap`: emits a Boot Snapshot with program state, Codex memory, contract, remote, branch, HEAD, dirty buckets, local task-board `plan-next`, and GitHub sync availability.
  - `closeout-check`: emits a Closeout Gate packet with scoped-staging/push/task-board mirror blockers.
- Updated `.codex/project_contract.yaml` to follow `origin` target `MoonFlowFlower/EGO`, keep old `pen364692088/EGO` issue URLs as `legacy_external_refs`, and declare session bootstrap / closeout gate commands.
- Updated Codex-facing docs so new sessions run bootstrap first and closeout runs the guard before completion claims.

## Verification Plan

- `python -m py_compile scripts/codex_session_guard.py scripts/codex_project_autopilot.py scripts/codex_memory.py`
- `python -m pytest -q scripts/tests/test_codex_session_guard.py scripts/tests/test_codex_project_autopilot.py`
- `python scripts/codex_session_guard.py bootstrap --format json --out "$env:TEMP\ego_codex_bootstrap.json"`
- `python scripts/codex_session_guard.py closeout-check --format json --out "$env:TEMP\ego_codex_closeout.json"`
- `python scripts/codex_project_autopilot.py doctor`
- `python scripts/codex_project_autopilot.py plan-next`
- `git diff --check`

## Rollback

Remove `scripts/codex_session_guard.py`, its tests, this task directory, the related `AGENTS.md` / `CODEX_MEMORY.md` notes, and the `session_bootstrap` / `closeout_gate` / `legacy_external_refs` additions in `.codex/project_contract.yaml`. Restore the prior GitHub target only if the repo owner decision is explicitly reversed.

## What This Does Not Prove

- Does not prove EgoOperator stable real user benefit.
- Does not prove live autonomy, proactive messaging capability, durable memory efficacy, or consciousness.
- Does not prove GitHub Project sync is currently available; `gh` availability is checked and reported separately.
