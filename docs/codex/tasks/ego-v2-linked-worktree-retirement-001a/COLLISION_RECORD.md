# Collision Record — EGO-V2-LINKED-WORKTREE-RETIREMENT-001A-R2

## Candidate 1 — raw directory deletion

- Evidence: directory absent.
- Cheap baseline: any filesystem deletion.
- Leakage/hard-coding risk: high; ignores Git registry and authority truth.
- Smallest falsifier: `git worktree list` still contains the path.
- Expected failure: stale metadata and no independent recovery proof.
- Disposition: rejected.

## Candidate 2 — keep linked checkout

- Evidence: clean rollback worktree remains immediately usable.
- Cheap baseline: do nothing.
- Leakage/hard-coding risk: low.
- Smallest falsifier: none for preservation; cleanup objective remains open.
- Expected failure: redundant checkout persists.
- Disposition: safe baseline, not selected.

## Candidate 3 — branch/bundle-backed controlled retirement

- Evidence: callable preflight, verified bundle, clean fresh reconstruction,
  ordinary Git worktree removal, retained ref/tree, branch-only authority, and
  hostile controls.
- Cheap baseline: raw deletion cannot match registry and recovery checks.
- Leakage/hard-coding risk: bounded by object/ref/hash and route checks.
- Smallest falsifier: wrong bundle, missing ref/tree, registered retired path,
  stale authority, or opened runtime switch.
- Expected failure: fail before removal or restore before commit.
- Disposition: selected.

## R2 collision — immutable takeover envelope versus active local disposition

### Keep stale active authority

- Evidence: historical source-envelope comparison remains green.
- Cheap baseline: leave the removed path in active machine readback.
- Risk: machine authority becomes false after physical removal.
- Smallest falsifier: registry has no linked checkout while authority says it does.
- Disposition: rejected.

### Mutate or reinterpret the historical envelope

- Evidence: canonical bytes can be made to match the new disposition.
- Cheap baseline: parser overlay or temporary rewrite.
- Risk: provenance loss or a hidden second validation path.
- Smallest falsifier: committed envelope bytes no longer reproduce their original projection.
- Disposition: rejected.

### Separate source provenance from the active retirement overlay

- Evidence: the immutable envelope still validates byte-for-byte while the active
  local worktree authority is independently required to equal the exact
  branch/bundle-only projection.
- Cheap baseline: exclude the worktree field without replacing it with an active assertion.
- Risk: overly broad exclusion; bounded by a single-field replacement plus hostile tests.
- Smallest falsifier: restore the stale worktree path or alter branch/head/tree/bundle;
  route convergence must fail.
- Disposition: selected R2 repair.
