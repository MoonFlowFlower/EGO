# EgoDesktop Joi Real-Loop G-ABLATION Capture Manifest Refresh v0

- task_id: `EGODESKTOP-GABLATION-025`
- parent_task_id: `EGODESKTOP-GABLATION-024`
- status: `active`
- created_at: `2026-06-27`
- owner: `Codex`
- layer: `engineering implementation / capture manifest refresh`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `explicit local artifact builder only`
- real_trigger_evidence: `none_hash_selection_only`
- claim_ceiling: `capture_manifest_hash_selection_only`
- auto_remote_anchor: `forbidden`

## Goal

Refresh the hash-only EgoDesktop G-ABLATION capture manifest so the current three-source raw-local cache from 024 is
represented in future capture input selection without committing raw text or running EgoDesktop.

## Task Card

- problem definition: 024 expanded the raw-local public source cache to include `wizard_of_wikipedia_hf`, but the current
  capture manifest artifact still reflects the earlier two-source cache and therefore cannot be used as the next frozen
  selection boundary.
- current stage/layer: `engineering implementation / capture manifest refresh`.
- mainline target: local hash-only artifact refresh, not runtime.
- enabled-state requirement: explicit local builder script only.
- real-trigger evidence requirement: none in 025; this task must not send text through EgoDesktop.
- hypothesis: the existing capture manifest builder can regenerate a three-source, 15-row hash-only manifest from the
  current `RAW_CACHE_REPORT.json` and ignored raw cache without raw text leakage or runtime authority.
- strongest baseline: the stale 021 capture manifest is a sufficient two-source selection boundary only for pre-024
  cache state, not for Wizard rows.
- ablation requirement: none in 025.
- trace/replay requirement: manifest must preserve future `window.egoDesktop.sendChatTurn` and trace-writer
  requirements, but must not create trace rows.
- computed-evidence provenance gate: freshness test plus callable builder output must produce `CAPTURE_MANIFEST.json`,
  sidecar hash, and `BUILD_REPORT.json`.
- acceptance gate: red test fails on the stale two-source artifact; regeneration passes focused tests; manifest contains
  three source ids and 15 selected row hashes; raw text is absent from committed artifacts; raw `source_cache/` remains
  ignored; route views and repo fast verification pass.
- claim ceiling: `capture_manifest_hash_selection_only`.
- stop condition: raw text staging, desktop trigger, capture row serialization, replay, scoring, comparison, verdict,
  runtime enablement, program-state/evidence-ledger update, push, tag, or remote anchor.
- rollback plan: revert the freshness test and regenerated capture artifacts, delete this task package/task-board entry,
  and regenerate route-convergence views.
- expected changed files:
  - `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-capture-manifest-refresh-v0/`
  - `scripts/tests/test_build_egodesktop_gablation_capture_manifest.py`
  - `artifacts/egodesktop_joi_real_loop_g_ablation_capture_manifest_v0/`
  - `Tasks/TASK_BOARD.yaml`
  - `docs/codex/tasks/TASK_LANE_INDEX.md`
- forbidden changes:
  - no raw source text staging;
  - no EgoDesktop run or trace capture;
  - no replay/scoring/same-access/`CREATURE_ON` execution;
  - no runtime enablement;
  - no `PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger update;
  - no push, tag, or remote anchor.
- Auto-Remote-Anchor decision: forbidden.

## What This Can Prove

Only that the current public raw-local cache can be reflected in a hash-only future capture selection manifest.

## What This Does Not Prove

This does not prove desktop-chat-turn capture, replay, D-provenance, `CREATURE_ON`, same-access saturation, baseline
score, candidate attribution, route advancement, runtime integration safety, stable user benefit, durable memory
efficacy, agency, emotion, subjectivity, consciousness, alive status, or Bar-2 specialness.

## Authority refs

- `docs/PROGRAM_STATE_UNIFIED.yaml`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-capture-manifest-v0/`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-public-source-expansion-wizard-v0/`
- `artifacts/egodesktop_joi_real_loop_g_ablation_source_cache_v0/RAW_CACHE_REPORT.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_capture_manifest_v0/BUILD_REPORT.json`
