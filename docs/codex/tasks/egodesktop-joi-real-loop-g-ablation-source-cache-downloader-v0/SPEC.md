# EgoDesktop Joi Real-Loop G-ABLATION Source Cache Downloader v0

- task_id: `EGODESKTOP-GABLATION-017`
- parent_task_id: `EGODESKTOP-GABLATION-016`
- status: `accepted_local_fallback_reviewed`
- created_at: `2026-06-27`
- owner: `Codex`
- layer: `engineering implementation / local-only source cache downloader`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `no_runtime_enablement`
- real_trigger_evidence: `none_for_017_downloader_tool`
- claim_ceiling: `source_cache_downloader_tool_and_metadata_smoke_only`
- auto_remote_anchor: `forbidden`

## Objective

Implement a downloader/cache tool that reads the accepted 016 `SOURCE_MANIFEST.json` and `SOURCE_DOWNLOAD_PLAN.json`,
refuses blocked sources, and can perform a metadata-only reachability/hash smoke for eligible non-gated public sources.

This task does not commit raw dataset text, does not create tracked raw source rows, does not capture desktop rows, does
not score, does not compare, does not emit a verdict, does not update program state/evidence ledger, and does not
push/tag/remote-anchor.

## Task Card

- problem definition: add a safe local-only downloader surface without turning source cache into evidence or capture.
- current stage/layer: `engineering implementation / local-only source cache downloader`.
- mainline target: tool and metadata smoke only, not runtime.
- enabled-state requirement: no runtime enablement.
- real-trigger evidence requirement: none in 017.
- hypothesis: a manifest-driven downloader with default metadata-only behavior can verify source reachability while
  preserving raw-cache local-only boundaries.
- strongest baseline: same-access controller over any future cached text remains the future attribution steelman.
- ablation requirement: none in 017.
- trace/replay requirement: smoke report records source ids, URLs, response status, byte counts, content hashes, and no
  raw text.
- computed-evidence provenance gate: callable downloader generates the smoke report.
- acceptance gate: tests and local checks pass; source-limited review returns no blockers.
- claim ceiling: source cache downloader tool and metadata smoke only.
- stop condition: desktop capture, scoring, comparison, verdict, program-state/evidence-ledger update, push, tag,
  remote-anchor, gated data access, or committing raw dataset text.
- rollback plan: delete 017 docs, script, tests, smoke report, `.gitignore` raw-cache entry, task-board entry, and
  regenerate route views.
- expected changed files:
  - `.gitignore`
  - `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-source-cache-downloader-v0/`
  - `scripts/codex/run_egodesktop_gablation_source_cache_downloader.py`
  - `scripts/tests/test_run_egodesktop_gablation_source_cache_downloader.py`
  - `artifacts/egodesktop_joi_real_loop_g_ablation_source_cache_v0/CACHE_SMOKE_REPORT.json`
  - `artifacts/egodesktop_joi_real_loop_g_ablation_source_cache_v0/CACHE_SMOKE_REPORT.sha256`
  - `Tasks/TASK_BOARD.yaml`
  - `docs/codex/tasks/TASK_LANE_INDEX.md`
- forbidden changes:
  - no committed raw dataset text;
  - no gated dataset access or terms acceptance;
  - no local/private text upload;
  - no desktop capture;
  - no same-access baseline execution;
  - no scoring, comparison, verdict, or route advancement;
  - no default runtime enablement;
  - no `PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger update;
  - no push, tag, or remote anchor.
- Auto-Remote-Anchor decision: forbidden.

## Acceptance Gate

This task is accepted only if:

- downloader reads 016 manifest and plan;
- downloader refuses blocked, local-private, and negative-evidence-only sources;
- default run is metadata-only and records no raw text;
- raw cache directory is ignored by git and not staged;
- smoke report records no capture/scoring/runtime/program-state/evidence-ledger/remote authority;
- local tests/checks pass;
- source-limited review returns no blocking findings.

## What This Can Prove

Only that eligible public source metadata endpoints can be reached by a bounded local tool and hashed without admitting
raw text as evidence.

## What This Does Not Prove

This does not prove raw source cache completeness, dataset row availability, desktop capture, `CREATURE_ON` effect,
same-access saturation, baseline score, candidate attribution, route advancement, product benefit, runtime integration
safety, stable user benefit, durable memory efficacy, agency, emotion, subjectivity, consciousness, alive status, or
Bar-2 specialness.

## Next Minimal Closed-Loop Action

Open a separate source-id repair/update task for `dailydialog_hf` before any raw-cache population task. Do not capture
or score until a later preregistered capture design is accepted.
