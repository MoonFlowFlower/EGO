# High-Impact Refactor Workflow Optimization v1

## Problem Reframe

The legacy archival purge succeeded, but it exposed a workflow gap: high-impact mutation scope was not declared before closeout, so the closeout gate could only report broad `unsafe_dirty_paths` and the implementer had to reason out the missing scope late.

## One Hypothesis

If high-impact tasks declare an expected mutation surface and closeout can consume a task-scoped mutation allowance with grouped dirty diagnostics, future large deletions or migrations can fail closed with actionable scope evidence without permanently broadening global mutation paths.

## One Change Surface

- Codex session closeout guard diagnostics and tests.
- Archive verifier common helpers and tests.
- Task template / repo workflow docs.
- Repo-local EGO skills for architecture-boundary and milestone implementation workflow.
- Program-state/evidence notes describing the workflow-only improvement.

## Expected Mutation Surface

Task-scoped allowance is declared in `MUTATION_SCOPE.yaml` beside this Stage Card. It permits only this workflow task's guard, tests, docs, skills, program-state derived views, and evidence-ledger update.

## Authority Source

- Closeout authority: `scripts/codex_session_guard.py` and `.codex/project_contract.yaml`.
- Current project authority: `docs/PROGRAM_STATE_UNIFIED.yaml`.
- Archive boundary authority: `artifacts/archive/legacy_pre_operator_mainline_manifest.json` plus `legacy/ego-pre-handmade-mainline/ARCHIVED_POINTER.md`.

## What Can Change

- `closeout-check` may accept an optional `--mutation-scope` YAML file.
- Dirty reporting may add grouped unsafe explanations and task-scoped counts.
- The legacy archival verifier may read tag/commit/removed paths from the manifest instead of hardcoded duplicate constants.
- Workflow skills/docs may require mutation-scope preflight for large deletions, migrations, state/evidence edits, and archive purges.

## What Cannot Be Proven

- EgoOperator runtime efficacy.
- Stable real user benefit.
- Live autonomy.
- Durable memory efficacy.
- Functional selfhood.
- Consciousness, subjective experience, or real emotion.

## Three-Level Verify

1. Unit tests for task-scoped mutation allowance, unsafe dirty grouping, local-only staged blocking, and archival verifier helpers.
2. Repo workflow checks: py_compile, lint, program-state integrity, legacy archival purge verifier, runtime authority boundary, and `verify_repo.py --mode fast`.
3. Closeout with this task's `MUTATION_SCOPE.yaml`, scoped commit, and push.

## Rollback Plan

Revert the workflow optimization commit. This returns closeout to global `allowed_mutation_paths` only and leaves existing legacy archival purge state unchanged.

## Claim Ceiling

This task can prove only local workflow guard hardening for high-impact refactor/archive tasks. It does not prove any EgoOperator runtime, user-benefit, autonomy, memory, selfhood, consciousness, or subjective-experience claim.
