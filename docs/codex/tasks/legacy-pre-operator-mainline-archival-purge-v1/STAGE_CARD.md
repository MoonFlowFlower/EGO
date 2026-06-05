# Legacy Pre-Operator Mainline Archival Purge v1

## Problem Reframe

The current default runtime owner is `EgoOperator`, but the working tree still contains bulky pre-operator runtime code under `legacy/ego-pre-handmade-mainline/`. Several repo-level governance checks also still require subrepo mirrors and legacy code paths to exist. That makes the legacy code look more active than it is and increases future agent/Codex route pollution.

## One Hypothesis

If current governance checks stop depending on legacy code directories and the old code is preserved through a git archive pointer plus a bounded manifest/inventory, the main working tree can remove the bulky legacy code without changing `EgoOperator` runtime authority or evidence ceilings.

## One Change Surface

- Program-state generated views and integrity checks.
- Route-convergence / mainline-clarity verifier references.
- Archive pointer, manifest, and reusable algorithm inventory.
- Removal of only:
  - `legacy/ego-pre-handmade-mainline/EgoCore/`
  - `legacy/ego-pre-handmade-mainline/OpenEmotion/`
  - `legacy/ego-pre-handmade-mainline/ego_desktop_lab/`

## Authority Source

- Current runtime authority: `docs/PROGRAM_STATE_UNIFIED.yaml` and `EgoOperator/`.
- Archive pointer: `legacy-pre-operator-mainline-before-purge`.
- Working-tree tombstone: `legacy/ego-pre-handmade-mainline/ARCHIVED_POINTER.md`.
- Archive manifest: `artifacts/archive/legacy_pre_operator_mainline_manifest.json`.
- Algorithm reference boundary: `docs/archive/LEGACY_ALGORITHM_INVENTORY.md`.

## What Can Change

- Legacy code directories may be removed from the current main working tree.
- Program-state and route governance may be updated so generated views no longer require legacy mirrors.
- Active verifier scripts may reject legacy imports/default routing while permitting archive/historical references.
- Documentation may redirect from legacy code paths to the archive pointer and algorithm inventory.

## What Cannot Be Proven

- EgoOperator runtime efficacy.
- Stable real user benefit.
- Live autonomy.
- Durable memory efficacy.
- Functional selfhood.
- Consciousness, subjective experience, or alive status.

## Three-Level Verify

1. Dependency proof: search active code, tests, scripts, docs, project contract, and program state for `EgoCore`, `OpenEmotion`, `ego_desktop_lab`, and `legacy/ego-pre-handmade-mainline`, then classify references as active dependencies, historical references, archive pointers, or forbidden active authority.
2. Governance/runtime checks: run EgoOperator tests, program-state integrity, route convergence, mainline clarity, lint, the archival-purge anti-regression verifier, and `git diff --check`.
3. Closeout/publish checks: run `closeout-check`, create/preserve the archive pointer, scoped stage/commit, and push `origin main` plus the archive tag.

## Rollback Plan

- Restore by reverting the purge commit, or by checking out the removed paths from `legacy-pre-operator-mainline-before-purge`:

```bash
git checkout legacy-pre-operator-mainline-before-purge -- legacy/ego-pre-handmade-mainline/EgoCore legacy/ego-pre-handmade-mainline/OpenEmotion legacy/ego-pre-handmade-mainline/ego_desktop_lab
```

- Any reuse after rollback still requires a new Stage Card and evidence gate before runtime authority can change.

## Claim Ceiling

This purge can prove only that the current main working tree no longer carries bulky pre-operator legacy runtime code as default-route context. It does not prove any runtime, user-benefit, autonomy, memory, selfhood, consciousness, or subjective-experience claim.
