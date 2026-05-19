# Codex Autopilot L2 Dirty Baseline SPEC

## Goal

Enable the generic Codex autopilot to proceed safely in a repository with large pre-existing dirty state by recording a local baseline and evaluating only new or changed dirty paths against the project contract.

The v1 baseline intentionally uses tracked dirty state by default (`git status --short -uno`). This keeps the control plane usable in repositories with large runtime/artifact untracked noise. Future write-capable L2 slices must add an allowed-path untracked scan before automatic staging; this slice remains dry-run only.

## Non-Goals

- Do not implement full unattended code modification.
- Do not execute #14 while it remains `unknown`.
- Do not modify `EgoOperator/**`, legacy projects, `docs/PROGRAM_STATE_UNIFIED.yaml`, or `artifacts/evidence_ledger/**`.
- Do not treat dirty-baseline artifacts as authority or evidence.

## Acceptance Gate

- #17 is closed as the L0/L1 bootstrap.
- #18 tracks this L2 scoped single-issue executor work.
- `baseline`, `diff-scope`, `run-once --dry-run`, and `normalize-issue --dry-run` are available.
- Tests prove unchanged pre-existing dirty state does not block L2, while new out-of-scope dirty state does.
- Real baseline completes without expanding all untracked runtime/artifact noise.

## Claim Ceiling

`Codex autopilot L2 scoped single-issue local candidate pass`.
