# EgoDesktop Joi Real-Loop G-ABLATION Source Manifest Download Boundary v0 Status

- status: `accepted_local_fallback_reviewed`
- task_id: `EGODESKTOP-GABLATION-015`
- parent_task_id: `EGODESKTOP-GABLATION-014`
- claim_ceiling: `source_manifest_download_boundary_only`
- mainline_connected: `false`
- enabled: `false`
- real_trigger_evidence: `none_for_015_boundary_card`
- runtime_authority: `none`

## Current Readback

- current branch: `main`
- source HEAD before 015 edits: `6dbe9d5ad3b25878a548fe3d1ae333dce2a50e9d`
- source worktree before 015 edits: clean
- 014 status: `accepted`
- 014 commit: `6dbe9d5a docs: define egodesktop gablation real source capture design`
- Claude re-review availability in 014: unavailable; fallback reviewer returned `NO_BLOCKING_FINDINGS`

## Decision

015 is a docs-only boundary card. It turns 014's source/capture semantics into a source-manifest and download-boundary
contract before any local source cache or public dataset download.

This task does not create `SOURCE_MANIFEST.json`, download datasets, create a source cache, capture rows, run baselines,
score, compare, emit a verdict, update program state, update the evidence ledger, push, tag, or remote-anchor.

## Evidence Produced

- 015 task card: `SPEC.md`
- 015 plan: `PLAN.md`
- 015 review record: `REVIEW.md`
- 015 mutation scope: `MUTATION_SCOPE.yaml`
- task-board entry: `EGODESKTOP-GABLATION-015`

## Fallback Reviewer Readback

Source-limited fallback reviewer returned `NO_BLOCKING_FINDINGS`. The reviewer confirmed that 015 stays on the intended
boundary, classifies candidate sources, blocks data movement and evidence claims, and preserves license/privacy/raw-cache
and B-011 gates.

Non-blocking hardening accepted: manifest-level required fields now explicitly include `no_runtime_authority`,
`no_program_state_authority`, `no_evidence_ledger_authority`, and `no_remote_authority`.

## Current Claim Ceiling

This can prove only that source-manifest and download boundaries are specified before any data movement.

## Next Minimal Closed-Loop Action

Commit this 015 package locally only. Then open a separate implementation task before creating `SOURCE_MANIFEST.json`,
creating a source cache, or downloading eligible non-gated public datasets.

## What This Does Not Prove

This does not prove real source cache existence, desktop capture, `CREATURE_ON` effect, same-access saturation, baseline
score, candidate attribution, route advancement, product benefit, runtime integration safety, stable user benefit,
durable memory efficacy, agency, emotion, subjectivity, consciousness, alive status, or Bar-2 specialness.
