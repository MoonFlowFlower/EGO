# EgoDesktop Joi Real-Loop G-ABLATION Capture Manifest v0

- task_id: `EGODESKTOP-GABLATION-021`
- parent_task_id: `EGODESKTOP-GABLATION-020`
- status: `accepted`
- created_at: `2026-06-27`
- owner: `Codex`
- layer: `engineering implementation / capture manifest builder`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `no_runtime_enablement`
- real_trigger_evidence: `none_for_021_capture_manifest`
- claim_ceiling: `capture_manifest_hash_selection_only`
- auto_remote_anchor: `forbidden`

## Objective

Create a callable builder that reads the 019 `RAW_CACHE_REPORT.json` plus ignored local `source_cache/` sample files,
verifies cache hashes, and emits a hash-only row-selection manifest for a future explicit EgoDesktop capture task.

This task must not include raw text in committed artifacts and must not run EgoDesktop, capture rows, score, compare,
update program state/evidence ledger, push, tag, or remote-anchor.

## Task Card

- problem definition: freeze a small row-selection/hash contract before any desktop trigger.
- current stage/layer: `engineering implementation / capture manifest builder`.
- mainline target: local artifact builder only, not runtime.
- enabled-state requirement: no runtime enablement.
- real-trigger evidence requirement: none in 021.
- hypothesis: row hashes and source-cache hashes can freeze future capture input selection without committing raw text.
- strongest baseline: future same-access controllers over the same selected source rows.
- ablation requirement: none in 021.
- trace/replay requirement: manifest must require future rows to use the real EgoDesktop chat-turn path and existing
  trace writer.
- computed-evidence provenance gate: callable builder verifies local cache hashes and writes manifest sidecar.
- acceptance gate: TDD red/green, generated manifest contains no raw text, local checks pass, source-limited review no
  blockers.
- claim ceiling: capture manifest hash/selection only.
- stop condition: raw text staging, EgoDesktop run, capture, scoring, comparison, runtime enablement,
  program-state/evidence-ledger update, push, tag, or remote anchor.
- rollback plan: delete 021 docs/script/tests/artifacts/task-board entry and regenerate route views.
- expected changed files:
  - `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-capture-manifest-v0/`
  - `scripts/codex/build_egodesktop_gablation_capture_manifest.py`
  - `scripts/tests/test_build_egodesktop_gablation_capture_manifest.py`
  - `artifacts/egodesktop_joi_real_loop_g_ablation_capture_manifest_v0/CAPTURE_MANIFEST.json`
  - `artifacts/egodesktop_joi_real_loop_g_ablation_capture_manifest_v0/CAPTURE_MANIFEST.sha256`
  - `artifacts/egodesktop_joi_real_loop_g_ablation_capture_manifest_v0/BUILD_REPORT.json`
  - `Tasks/TASK_BOARD.yaml`
  - `docs/codex/tasks/TASK_LANE_INDEX.md`
- forbidden changes:
  - no raw text staging;
  - no desktop capture;
  - no same-access baseline execution;
  - no scoring, comparison, verdict, or route advancement;
  - no runtime enablement;
  - no `PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger update;
  - no push, tag, or remote anchor.
- Auto-Remote-Anchor decision: forbidden.

## What This Can Prove

Only that a future capture input selection can be frozen by source/cache/row hashes without committing raw text.

## What This Does Not Prove

This does not prove desktop-chat-turn capture, `CREATURE_ON` effect, replay, D-provenance, same-access saturation,
baseline score, candidate attribution, route advancement, product benefit, runtime integration safety, stable user
benefit, durable memory efficacy, agency, emotion, subjectivity, consciousness, alive status, or Bar-2 specialness.

## Next Minimal Closed-Loop Action

Write failing tests for the hash-only capture manifest builder, then implement the smallest builder that passes.
