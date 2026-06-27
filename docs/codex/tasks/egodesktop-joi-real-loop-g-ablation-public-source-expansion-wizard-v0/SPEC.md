# EgoDesktop Joi Real-Loop G-ABLATION Public Source Expansion Wizard v0

- task_id: `EGODESKTOP-GABLATION-024`
- parent_task_id: `EGODESKTOP-GABLATION-019`
- status: `active`
- created_at: `2026-06-27`
- owner: `Codex`
- layer: `engineering validation / public source collection`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `source_manifest_and_raw_local_cache_only`
- real_trigger_evidence: `none_collection_only`
- claim_ceiling: `public_source_expansion_raw_local_cache_only`
- auto_remote_anchor: `forbidden`

## Objective

Add one more public human-dialogue source, `wizard_of_wikipedia_hf`, to the existing source manifest and bounded
raw-local cache downloader. Preserve only manifest/hash/report artifacts in git; raw text cache remains local ignored
material and has no capture, scoring, runtime, or product authority.

## Task Card

- problem definition: existing public source cache only covers DailyDialog and EmpatheticDialogues; the user requested
  more real dialogue data from other people.
- current stage/layer: `engineering validation / public source collection`.
- mainline target: source collection only, not desktop trigger, replay, or runtime.
- enabled-state requirement: explicit local manifest/downloader scripts only.
- real-trigger evidence requirement: none; this task does not send text through EgoDesktop.
- hypothesis: `chujiezheng/wizard_of_wikipedia` can be admitted as a public noncommercial candidate source with current
  Hugging Face metadata `license:cc-by-nc-4.0`, sampled through HF rows API, and kept raw-local only.
- strongest baseline: current two-source cache is enough for pipeline smoke; this task only increases source diversity,
  not mechanism evidence.
- ablation requirement: none in 024.
- trace/replay requirement: none in 024.
- computed-evidence provenance gate: source manifest, download plan, raw cache report, and cache hashes must be produced
  by callable scripts.
- acceptance gate: tests fail before implementation and pass after; manifest/download plan include
  `wizard_of_wikipedia_hf`; raw cache report records a local cache sample for it; committed reports contain no selected
  raw text; raw `source_cache/` remains ignored; local checks pass; source-limited review has no blockers.
- claim ceiling: public source expansion raw-local cache only.
- stop condition: unclear license, gated source, raw text staged, default runtime enablement, capture/scoring/replay
  execution, program-state/evidence-ledger update, push, tag, or remote anchor.
- rollback plan: revert script/tests/artifacts/task-board changes, delete 024 task docs/artifacts, and regenerate route
  views.
- expected changed files:
  - `scripts/codex/build_egodesktop_gablation_source_manifest.py`
  - `scripts/codex/run_egodesktop_gablation_source_cache_downloader.py`
  - `scripts/tests/test_build_egodesktop_gablation_source_manifest.py`
  - `scripts/tests/test_run_egodesktop_gablation_source_cache_downloader.py`
  - `artifacts/egodesktop_joi_real_loop_g_ablation_source_manifest_v0/`
  - `artifacts/egodesktop_joi_real_loop_g_ablation_source_cache_v0/`
  - `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-public-source-expansion-wizard-v0/`
  - `Tasks/TASK_BOARD.yaml`
  - `docs/codex/tasks/TASK_LANE_INDEX.md`
- forbidden changes:
  - no raw source text staging;
  - no EgoDesktop capture or replay run;
  - no scoring, comparison, attribution verdict, or route advancement;
  - no runtime enablement;
  - no `PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger update;
  - no push, tag, or remote anchor.
- Auto-Remote-Anchor decision: forbidden.

## What This Can Prove

Only that an additional public noncommercial human-dialogue dataset can be tracked in the local source manifest and
sampled into an ignored raw-local cache with hash/provenance reports.

## What This Does Not Prove

This does not prove capture, replay, `CREATURE_ON`, same-access comparison, baseline score, candidate attribution, route
advancement, product benefit, runtime integration safety, stable user benefit, durable memory efficacy, agency, emotion,
subjectivity, consciousness, alive status, or Bar-2 specialness.
