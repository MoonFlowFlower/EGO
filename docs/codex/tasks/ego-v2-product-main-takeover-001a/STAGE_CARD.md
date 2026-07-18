# EGO-V2-PRODUCT-MAIN-TAKEOVER-001A — Phase Main

Status: `OPERATOR_AUTHORIZED__EXECUTING_EXACT_26_PATH_TRANSCRIPTION`

## Problem definition

Make `D:/Project/AIProject/MyProject/Ego` the sole active V2 product-development
worktree without merging or laundering the preserved 19-path non-live checkpoint.

## Current layer

Engineering integration plus product control-plane governance. Repository-main
placement is distinct from runtime-mainline enablement.

## Mainline target and enabled state

- Repository target: Ego `refs/heads/main` and its primary worktree.
- Product runtime: default-off.
- Runtime authority: none.
- Runtime mainline: disconnected.
- Existing EgoOperator default: unchanged.

## Hypothesis and strongest baseline

An exact checkpoint + verified recovery package + CAS fast-forward + field-by-field
authority transcription preserves both the V2 Git lineage and the prior negative
checkpoint. A direct copy is the strongest cheap baseline: it matches folder
appearance but fails exact lineage, reconstruction, tree, and sole-authority checks.

## Ablations

1. Remove or alter one checkpoint byte: manifest/reconstruction verification fails.
2. Add one fast-forward delta path or use a non-ancestor: topology verification fails.
3. Open runtime/default/background/network/LLM state: route validation fails.
4. Change product source after `722a9cd1...`: product-byte comparison fails.

## Trace/replay and real-trigger requirement

No new product logic is permitted. Existing Step/Run evidence must remain callable
from Ego and traverse canonical dispatch -> SQLite commit -> recover -> one
RecoveryFrame -> recovered waypoints; replay must recompute from serialized state
plus observation.

## Computed-evidence provenance gate

Receipts bind producer function, input artifacts, run ID, aggregation rule,
Git/Python versions, hashes, exact refs, exact path sets, and callable test results.

## Acceptance gate

- Checkpoint commit parent/path set and recovery package pass.
- Main fast-forward is exact-old-value CAS to `722a9cd1...` and tree `8da84639...`.
- This commit is a direct child of `722a9cd1...` with exactly 26 paths.
- Product/controller/world/store/replay/UI bytes remain unchanged.
- Dual-repo route validation passes with route count 8 and one authority.
- Existing Step/Run, SQLite, recovery, waypoint, replay, export, leakage, and Tk
  evidence remains callable from Ego.

## Stop condition

Stop on source drift, missing/extra path, second authority, route-count change,
runtime opening, product-source edit, failed independent Red review, or any
reset/clean/stash/rebase/amend/push/tag/remote-anchor attempt.

## Rollback

Before this Phase-Main commit, only the operator-authorized reverse CAS window is
available. After commit, rollback requires a separate operator-authorized Red
transition. The checkpoint branch, bundle, and raw-byte archive remain immutable.

## Expected changed files

Exactly the 26 ordered paths in `MUTATION_SCOPE_MAIN.yaml`.

## Forbidden changes

No product/controller/world/store/replay/UI implementation edits; no EgoOperator
runtime changes; no LLM/network/background execution; no remote publication.

## Claim ceiling

Local repository/product-development-main placement with exact checkpoint
preservation and callable pre-existing product evidence only.

Auto-Remote-Anchor: `forbidden`
