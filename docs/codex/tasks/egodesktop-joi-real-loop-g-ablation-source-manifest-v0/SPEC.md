# EgoDesktop Joi Real-Loop G-ABLATION Source Manifest v0

- task_id: `EGODESKTOP-GABLATION-016`
- parent_task_id: `EGODESKTOP-GABLATION-015`
- status: `accepted_local_fallback_reviewed`
- created_at: `2026-06-27`
- owner: `Codex`
- layer: `engineering implementation / source manifest artifact`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `no_runtime_enablement`
- real_trigger_evidence: `none_for_016_manifest_artifact`
- claim_ceiling: `source_manifest_artifact_only`
- auto_remote_anchor: `forbidden`

## Objective

Implement a callable builder that creates `SOURCE_MANIFEST.json` and `SOURCE_DOWNLOAD_PLAN.json` under the accepted 015
boundary. This task produces hash-addressed manifest/download-plan artifacts only.

This task does not download datasets, create a raw source cache, accept gated terms, capture desktop rows, score,
compare, emit a verdict, update program state, update the evidence ledger, push, tag, or remote-anchor.

## Task Card

- problem definition: turn the accepted source-manifest/download-boundary contract into a deterministic local artifact.
- current stage/layer: `engineering implementation / source manifest artifact`.
- mainline target: artifact builder only, not runtime.
- enabled-state requirement: no runtime enablement and no download in 016.
- real-trigger evidence requirement: none in 016; future capture still requires real EgoDesktop chat-turn trigger.
- hypothesis: a generated manifest and download plan reduce ambiguity before any data movement.
- strongest baseline: same-access controller over the same public source text remains the future attribution steelman.
- ablation requirement: none in 016.
- trace/replay requirement: artifact JSON and SHA256 sidecars must be deterministic and reproducible from the builder.
- computed-evidence provenance gate: builder records `producer_function`, schema, source policy, candidate admissions,
  denied authority booleans, and sidecar hashes.
- acceptance gate: tests and local checks pass; source-limited review returns no blockers.
- claim ceiling: source manifest artifact only.
- stop condition: any download, cache creation, capture, score, comparison, verdict, remotes, program-state, or evidence
  ledger mutation.
- rollback plan: delete 016 docs, script, tests, artifacts, task-board entry, and regenerate route views.
- expected changed files:
  - `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-source-manifest-v0/`
  - `scripts/codex/build_egodesktop_gablation_source_manifest.py`
  - `scripts/tests/test_build_egodesktop_gablation_source_manifest.py`
  - `artifacts/egodesktop_joi_real_loop_g_ablation_source_manifest_v0/`
  - `Tasks/TASK_BOARD.yaml`
  - `docs/codex/tasks/TASK_LANE_INDEX.md`
- forbidden changes:
  - no dataset download;
  - no source cache creation;
  - no gated dataset access or terms acceptance;
  - no raw local/private text upload;
  - no desktop capture;
  - no same-access baseline execution;
  - no scoring, comparison, verdict, or route advancement;
  - no default runtime enablement;
  - no `PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger update;
  - no push, tag, or remote anchor.
- Auto-Remote-Anchor decision: forbidden.

## Acceptance Gate

This task is accepted only if:

- a callable builder creates deterministic `SOURCE_MANIFEST.json` and `SOURCE_DOWNLOAD_PLAN.json` artifacts with SHA256
  sidecars;
- manifest-level `no_capture_authority`, `no_scoring_authority`, `no_product_claim_authority`, `no_runtime_authority`,
  `no_program_state_authority`, `no_evidence_ledger_authority`, and `no_remote_authority` are all `true`;
- candidate source rows preserve 015 admission classes and blocked reasons;
- the download plan includes only future conditional actions for eligible non-gated public sources and includes no
  download action for gated, unknown-license, local-private, or negative-evidence-only sources;
- raw source cache directory is not created;
- local tests/checks pass;
- source-limited review returns no blocking findings before any follow-up downloader/cache task.

## What This Can Prove

Only that the source manifest and download plan can be generated deterministically under the accepted 015 boundary.

## What This Does Not Prove

This does not prove source cache existence, raw dataset availability, desktop capture, `CREATURE_ON` effect,
same-access saturation, baseline score, candidate attribution, route advancement, product benefit, runtime integration
safety, stable user benefit, durable memory efficacy, agency, emotion, subjectivity, consciousness, alive status, or
Bar-2 specialness.

## Next Minimal Closed-Loop Action

Open a separate downloader/cache task if raw local source caching is still wanted. Do not capture or score until a later
preregistered capture design is accepted.
