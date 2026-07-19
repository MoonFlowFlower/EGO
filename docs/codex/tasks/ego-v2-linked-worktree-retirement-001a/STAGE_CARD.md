# EGO-V2-LINKED-WORKTREE-RETIREMENT-001A-R2

Status: `OPERATOR_AUTHORIZED__CONTROLLED_RETIREMENT_EXECUTING`

## Problem definition

Retire the clean linked checkout at
`D:/Project/AIProject/MyProject/Ego-v2-product-first-001a` without losing the
rollback commit/tree, leaving stale Git worktree metadata, or changing product
runtime behavior. Preserve recovery through the existing branch ref plus a
verified, freshly reconstructed external Git bundle.

## Current layer

Engineering implementation / repository-maintenance control plane. This task
does not test a functional-subject mechanism.

## Mainline and enabled state

- Repository development remains on Ego `main`.
- V2 remains `enabled=false`, `default_enabled=false`, non-runtime-mainline,
  with `runtime_authority=none`.
- EgoOperator remains the active runtime default and is not modified.

## Hypothesis and strongest baseline

A clean linked checkout can be retired without evidence loss when its exact
branch, commit, tree, bundle, fresh reconstruction, worktree registry, and
branch-only authority are checked by callable code. Raw folder deletion is the
strongest cheap baseline; it cannot prove Git registry cleanup or recovery.

## Ablations and hostile controls

- missing/wrong rollback ref or tree fails;
- wrong bundle bytes/hash fails;
- stale registered worktree fails;
- old live worktree authority fails;
- opened runtime/default/background/network/LLM switch fails;
- case- or separator-varied ITL route path references fail.

## Trace/replay requirement

Git object IDs, worktree porcelain, bundle verification, and a fresh clone must
reconstruct commit `722a9cd1...` and tree `8da84639...`. Product replay is
unchanged and outside this maintenance mutation.

## Acceptance gate

The frozen external card SHA-256 is
`0fef18a8a25483f2ff703dcf7a4a35841449ca4b11cf0ac3c087fdafbc63c043`.
Preflight and bundle receipts must pass before an ordinary, non-force
`git worktree remove`. The branch and checkpoint refs must remain pinned; the
registry must retain only Ego main; the exact 19-path change set must pass
focused, route, staged independent review, and closeout checks before one local
commit.

## Stop and rollback

Stop on pin drift, dirt, bundle/reconstruction failure, force requirement,
scope expansion, runtime change, or independent blocking finding. Before the
final authority commit, restore only with ordinary `git worktree add` if a stop
condition requires physical rollback. After commit, reversal requires a new
operator-authorized Red transition.

## Expected changed files

Exactly the 19 paths in `MUTATION_SCOPE.yaml`; every path has an assigned
purpose. Product/controller/world/store/replay/UI and ITL files are forbidden.

## Claim ceiling

Controlled physical checkout retirement with branch-and-bundle recovery only.
No runtime, readiness, learning, memory-causality, agency, subjectivity,
consciousness, or electronic-life claim.

Auto-Remote-Anchor: `forbidden`
