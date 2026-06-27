# EgoDesktop Joi Real-Loop G-ABLATION DailyDialog Source ID Repair v0

- task_id: `EGODESKTOP-GABLATION-018`
- parent_task_id: `EGODESKTOP-GABLATION-017`
- status: `accepted`
- created_at: `2026-06-27`
- owner: `Codex`
- layer: `engineering implementation / source-id repair`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `no_runtime_enablement`
- real_trigger_evidence: `none_for_018_source_id_repair`
- claim_ceiling: `source_id_repair_and_metadata_smoke_only`
- auto_remote_anchor: `forbidden`

## Objective

Repair the `dailydialog_hf` source URL after 017 metadata smoke found
`https://huggingface.co/datasets/daily_dialog` returns `404`.

This task may update the manifest builder, regenerate 016 manifest/download-plan artifacts, and rerun 017 metadata-only
smoke. It does not download raw dataset rows, create a raw source cache, accept gated terms, capture desktop rows,
score, compare, emit a verdict, update program state/evidence ledger, push, tag, or remote-anchor.

## Source Readback

Live metadata checks found these reachable DailyDialog candidate pages on 2026-06-27:

- `https://huggingface.co/datasets/roskoN/dailydialog`
  - page status: `200`
  - raw card: `https://huggingface.co/datasets/roskoN/dailydialog/raw/main/README.md`
  - raw card status: `200`
  - license line: `DailyDialog dataset is licensed under CC BY-NC-SA 4.0`
- `https://huggingface.co/datasets/Akhil391/daily_dialog`
  - page status: `200`
  - raw card status: `200`
  - license line references `CC BY-NC-SA 4.0`
- `https://huggingface.co/datasets/ConvLab/dailydialog`
  - page status: `200`
  - raw card status: `200`
  - license line references `CC BY-NC-SA 4.0`

018 selects `roskoN/dailydialog` because its raw card explicitly states the DailyDialog license and preserves the
existing `public_nc_sa` tier. This is a source-id repair only; it is not legal advice and does not authorize product,
commercial, companion-readiness, or user-benefit claims.

## Task Card

- problem definition: replace the stale DailyDialog source URL with a currently reachable HF dataset card while
  preserving non-commercial/share-alike constraints.
- current stage/layer: `engineering implementation / source-id repair`.
- mainline target: source manifest and metadata smoke artifacts only, not runtime.
- enabled-state requirement: no runtime enablement.
- real-trigger evidence requirement: none in 018.
- hypothesis: correcting source id before raw-cache work prevents 404 source drift from contaminating future cache tasks.
- strongest baseline: same-access controller over any future cached text remains the future attribution steelman.
- ablation requirement: none in 018.
- trace/replay requirement: regenerated manifest/download-plan/smoke artifacts and sidecars must be hash-addressed.
- computed-evidence provenance gate: tests and metadata smoke must show `dailydialog_hf` reachable or preserve failure.
- acceptance gate: tests/checks pass; source-limited review returns no blockers.
- claim ceiling: source-id repair and metadata smoke only.
- stop condition: raw dataset download, source cache creation, capture, score, comparison, verdict, program-state/evidence
  ledger update, push, tag, or remote-anchor.
- rollback plan: restore prior DailyDialog URL/artifacts/task-board entry and regenerate route views.
- expected changed files:
  - `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-dailydialog-source-id-repair-v0/`
  - `scripts/codex/build_egodesktop_gablation_source_manifest.py`
  - `scripts/tests/test_build_egodesktop_gablation_source_manifest.py`
  - `artifacts/egodesktop_joi_real_loop_g_ablation_source_manifest_v0/`
  - `artifacts/egodesktop_joi_real_loop_g_ablation_source_cache_v0/CACHE_SMOKE_REPORT.json`
  - `artifacts/egodesktop_joi_real_loop_g_ablation_source_cache_v0/CACHE_SMOKE_REPORT.sha256`
  - `Tasks/TASK_BOARD.yaml`
  - `docs/codex/tasks/TASK_LANE_INDEX.md`
- forbidden changes:
  - no raw dataset row download;
  - no source cache creation;
  - no gated dataset access or terms acceptance;
  - no desktop capture;
  - no same-access baseline execution;
  - no scoring, comparison, verdict, or route advancement;
  - no default runtime enablement;
  - no `PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger update;
  - no push, tag, or remote anchor.
- Auto-Remote-Anchor decision: forbidden.

## Acceptance Gate

This task is accepted only if:

- `dailydialog_hf` source URL is updated to a currently reachable source with explicit `CC BY-NC-SA 4.0` card text;
- source tier remains `public_nc_sa`;
- manifest/download-plan artifacts are regenerated with sidecars;
- metadata smoke is rerun without storing raw text or creating `source_cache`;
- local tests/checks pass;
- source-limited review returns no blocking findings.

## What This Can Prove

Only that the DailyDialog source id used by the manifest is repaired and reachable at metadata-smoke level.

## What This Does Not Prove

This does not prove raw source cache completeness, dataset row availability, desktop capture, `CREATURE_ON` effect,
same-access saturation, baseline score, candidate attribution, route advancement, product benefit, runtime integration
safety, stable user benefit, durable memory efficacy, agency, emotion, subjectivity, consciousness, alive status, or
Bar-2 specialness.

## Next Minimal Closed-Loop Action

Accepted locally after source-limited fallback reviewer `NO_BLOCKING_FINDINGS`. Next, open a separate raw-cache
population task if continuing the public-source path. Do not capture or score until a later preregistered capture
design is accepted.
