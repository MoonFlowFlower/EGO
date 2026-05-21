# Codex Task Board Canonical Store v1 Stage Card

## Boundary Contract

- Owner: Codex project-management control plane.
- Canonical record: `Tasks/TASK_BOARD.yaml`.
- GitHub role: display/sync mirror only.
- Runtime paths: no `EgoOperator/**` runtime behavior change in this stage.
- Protected paths: do not modify `docs/PROGRAM_STATE_UNIFIED.yaml`, `artifacts/evidence_ledger/**`, or legacy runtime code.

## Mainline E2E

Autopilot should be able to read local task state, select the next ready task, and perform dry-run planning without calling GitHub Project APIs.

## Evidence Report

This stage is proven by local board commands, syncer dry-run, unit tests, and diff check. It does not prove unattended development quality or Product/EgoOperator runtime benefit.

## Rollback

Revert `Tasks/TASK_BOARD.yaml`, the syncer, and Autopilot local-board wiring. Existing GitHub issues remain as historical display artifacts.
