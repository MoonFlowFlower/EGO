# Assignment Guide

## Default Step Contract

Before mutating any step:

1. Re-read `01_GLOBAL_RULES.md`
2. Re-read `04_STOP_RULES.md`
3. Re-read `runtime/RUN_STATE.json`
4. Re-read the previous step report

## Review / Verify Requirements

- Required on every mutating step:
  - `Spec -> Author -> Self-Reviewer -> Verifier`
- Required `Independent Reviewer` steps:
  - `STAGE2-01`
  - `STAGE2-04`
  - `STAGE2-05`
  - `STAGE2-07`
  - `STAGE2-08`

## Checkpoint Rules

- After any `verified` step, create a checkpoint commit/push if the worktree can be cleanly scoped.
- Do not include unrelated logs, state, or foreign artifacts in the checkpoint.
