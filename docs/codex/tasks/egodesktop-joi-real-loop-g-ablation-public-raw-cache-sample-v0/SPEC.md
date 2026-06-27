# EgoDesktop Joi Real-Loop G-ABLATION Public Raw Cache Sample v0

- task_id: `EGODESKTOP-GABLATION-019`
- parent_task_id: `EGODESKTOP-GABLATION-018`
- status: `accepted`
- created_at: `2026-06-27`
- owner: `Codex`
- layer: `engineering implementation / public raw cache sample`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `no_runtime_enablement`
- real_trigger_evidence: `none_for_019_raw_cache_sample`
- claim_ceiling: `bounded_public_raw_cache_sample_only`
- auto_remote_anchor: `forbidden`

## Objective

Add an explicit opt-in raw-cache sample mode to the existing source-cache downloader. The mode may fetch a bounded
sample from public, non-gated sources already admitted by the 016/018 manifest, write raw rows only under the ignored
local `source_cache/` directory, and commit only hash/count/provenance reports.

This task does not perform desktop chat-turn capture, scoring, same-access comparison, route advancement, runtime
enablement, program-state/evidence-ledger update, push, tag, or remote anchor.

## Bounded Audit

- real objective: prove that public source material can be cached locally through a callable path without confusing it
  with real EgoDesktop trigger evidence.
- strongest baseline explanation: future attribution will still be explained by same-access controllers unless a later
  capture/scoring task proves otherwise.
- strongest invalidity reason: cached public text could be mistaken for real desktop-chat-turn capture evidence.
- falsifier for this slice: eligible public sources cannot yield bounded rows/archive bytes through callable paths, or
  raw text is staged/tracked.
- insufficient evidence: row cache alone does not prove desktop capture, replay, D-provenance, baseline saturation, or
  mechanism attribution.
- mechanism test status: engineering substrate only, not a mechanism or agency test.
- leakage/hard-code check: raw cached rows remain local-only; committed report records hashes/counts, not text.
- stop condition: any attempt to track raw text, capture desktop rows, score/compare, update evidence ledger/program
  state, enable runtime, push, tag, or remote-anchor.
- rollback plan: delete 019 docs/report, remove task-board entry, revert downloader/tests, and delete ignored local
  `source_cache/` files if desired.

## Task Card

- problem definition: add a bounded opt-in raw-cache sample path after 018 repaired the DailyDialog source id.
- current stage/layer: `engineering implementation / public raw cache sample`.
- mainline target: downloader/report artifacts only, not runtime.
- enabled-state requirement: no runtime enablement.
- real-trigger evidence requirement: none in 019.
- hypothesis: a manifest-driven raw-cache sample can fetch public source rows locally while preserving claim boundaries.
- strongest baseline: same-access controller over the same cached text remains the future attribution steelman.
- ablation requirement: none in 019.
- trace/replay requirement: report source ids, methods, URLs, split, max rows, row counts, cache file hashes, producer
  function, and no capture/scoring/runtime authority.
- computed-evidence provenance gate: callable downloader writes the raw cache sample and report.
- acceptance gate: TDD red/green evidence, local tests/checks, hash readback, `git status --ignored` proves raw cache is
  ignored, and source-limited review returns no blockers.
- claim ceiling: bounded public raw cache sample only.
- stop condition: raw text staged/tracked, desktop capture, scoring, comparison, verdict, route advancement, runtime
  enablement, program-state/evidence-ledger update, push, tag, or remote anchor.
- expected changed files:
  - `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-public-raw-cache-sample-v0/`
  - `scripts/codex/run_egodesktop_gablation_source_cache_downloader.py`
  - `scripts/tests/test_run_egodesktop_gablation_source_cache_downloader.py`
  - `artifacts/egodesktop_joi_real_loop_g_ablation_source_cache_v0/RAW_CACHE_REPORT.json`
  - `artifacts/egodesktop_joi_real_loop_g_ablation_source_cache_v0/RAW_CACHE_REPORT.sha256`
  - `Tasks/TASK_BOARD.yaml`
  - `docs/codex/tasks/TASK_LANE_INDEX.md`
- forbidden changes:
  - no committed raw dataset text;
  - no gated dataset access or terms acceptance;
  - no local/private text upload or cache;
  - no desktop capture;
  - no same-access baseline execution;
  - no scoring, comparison, verdict, or route advancement;
  - no default runtime enablement;
  - no `PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger update;
  - no push, tag, or remote anchor.
- Auto-Remote-Anchor decision: forbidden.

## Source Method Readback

- `dailydialog_hf`: Hugging Face datasets-server `rows` API supports `dataset=roskoN/dailydialog`,
  `config=full`, `split=train`.
- `empathetic_dialogues_hf`: Hugging Face datasets-server viewer reports unsupported arbitrary Python dataset script.
  The public dataset script points to
  `https://dl.fbaipublicfiles.com/parlai/empatheticdialogues/empatheticdialogues.tar.gz`; 019 may cache that public
  archive locally and extract a bounded `train.csv` sample.

## What This Can Prove

Only that bounded public source rows/archive samples can be fetched into an ignored local cache and summarized by
hash/count artifacts.

## What This Does Not Prove

This does not prove full raw source cache completeness, desktop-chat-turn capture, `CREATURE_ON` effect, replay,
D-provenance, same-access saturation, baseline score, candidate attribution, route advancement, product benefit,
runtime integration safety, stable user benefit, durable memory efficacy, agency, emotion, subjectivity,
consciousness, alive status, or Bar-2 specialness.
