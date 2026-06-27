# EgoDesktop Joi Real-Loop G-ABLATION Source Manifest Download Boundary v0

- task_id: `EGODESKTOP-GABLATION-015`
- parent_task_id: `EGODESKTOP-GABLATION-014`
- status: `accepted_local_fallback_reviewed`
- created_at: `2026-06-27`
- owner: `Codex`
- layer: `engineering implementation / source manifest and download boundary design`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `no_runtime_enablement`
- real_trigger_evidence: `none_for_015_boundary_card`
- claim_ceiling: `source_manifest_download_boundary_only`
- auto_remote_anchor: `forbidden`

## Objective

Convert the accepted 014 real-source/capture semantics into a bounded source-manifest and download-boundary contract.
This is the checkpoint before any local source cache or public dataset download work.

This task does not download data, create a source cache, inspect gated data, accept third-party terms, capture desktop
rows, score, compare, emit a verdict, update program state, update the evidence ledger, push, tag, or remote-anchor.

## Stage Gate

- program_goal: improve future EgoDesktop G-ABLATION evidence hygiene by using real source text without confusing text
  provenance with desktop-trigger or replay-row provenance.
- current_stage_goal: freeze the source-manifest schema, candidate admission table, and download boundary for a later
  implementation task.
- stage_success_criteria: the card specifies which candidate sources are metadata-only, conditionally local-download
  eligible, blocked, or negative-evidence-only; it also specifies raw-text storage, privacy, attribution, license, and
  future capture blockers.
- next_decision_gate: source-limited review returns no blocking findings, then a later task may implement
  `SOURCE_MANIFEST.json` and a local-only source cache for eligible non-gated sources.

## Source Manifest Contract

A future implementation task may create:

- `artifacts/egodesktop_joi_real_loop_g_ablation_source_manifest_v0/SOURCE_MANIFEST.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_source_manifest_v0/SOURCE_MANIFEST.sha256`
- `artifacts/egodesktop_joi_real_loop_g_ablation_source_manifest_v0/SOURCE_DOWNLOAD_PLAN.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_source_manifest_v0/SOURCE_DOWNLOAD_PLAN.sha256`
- a local-only raw cache under
  `artifacts/egodesktop_joi_real_loop_g_ablation_source_manifest_v0/source_cache/`

The raw cache must be treated as local-only operational exhaust unless a later task explicitly admits a reduced,
hash-only, or redacted artifact for tracking. Raw public or local conversation text must not be staged by default.

Required manifest-level fields:

- `schema`: `egodesktop.joi_real_loop.source_manifest.v0`
- `manifest_id`
- `created_at`
- `producer_function`
- `source_policy_version`
- `source_rows`
- `download_plan_hash`
- `claim_ceiling`
- `no_capture_authority`
- `no_scoring_authority`
- `no_product_claim_authority`
- `no_runtime_authority`
- `no_program_state_authority`
- `no_evidence_ledger_authority`
- `no_remote_authority`

Required per-source fields:

- `source_id`
- `source_kind`
- `source_license_tier`
- `source_url_or_local_path`
- `retrieved_at`
- `license_name`
- `license_url`
- `license_text_hash_or_card_hash`
- `attribution_required`
- `sharealike_required`
- `noncommercial_only`
- `gated_terms_required`
- `operator_terms_review_required`
- `operator_terms_review_status`
- `admission_status`
- `download_status`
- `cache_policy`
- `raw_text_policy`
- `privacy_mode`
- `pii_review_required`
- `allowed_claim_ceiling`
- `blocked_downstream_claims`
- `future_capture_eligible`
- `future_capture_blockers`
- `b011_carry_forward_required`
- `independence_cluster_keys`
- `split_meta_leakage_scan_required`
- `source_hash`
- `content_hash_strategy`
- `blocked_reason`

## Candidate Admission Table

| source_id | source | tier | admission_status | download_status | future_capture_eligible | notes |
| --- | --- | --- | --- | --- | --- | --- |
| `local_egodesktop_session_context_v0` | `artifacts/egodesktop_session_local_conversation_context_v0/session_context_report.json` | `local_operator_private` | `metadata_allowed` | `not_downloadable` | `blocked_until_privacy_manifest` | Local session context can identify source availability only; raw/private text needs `hash_only` or redaction policy before future capture. |
| `egodesktop_gablation_009_predeclared_single_capture` | `artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/capture/calibration_ui_predeclared_single/trace/trace_rows.jsonl` | `local_operator_private` | `metadata_allowed` | `not_downloadable` | `blocked_prior_calibration_only` | Accepted prior calibration provenance only; not heldout `CREATURE_ON` source text. |
| `egodesktop_gablation_009_turn2_rejected_posthoc` | `artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/capture/calibration_ui_turn2/` | `blocked_negative_evidence` | `negative_evidence_only` | `not_downloadable` | `false` | Rejected post-hoc positional-selection attempt; must never enter source manifest input rows, calibration basis, capture basis, score, or comparison. |
| `dailydialog_hf` | `https://huggingface.co/datasets/daily_dialog` | `public_nc_sa` | `candidate_metadata_only` | `future_local_download_conditional` | `blocked_until_manifest_and_leakage_gates` | Non-commercial/share-alike constraints must be preserved; no product, companion-readiness, commercial, or user-benefit claims. |
| `empathetic_dialogues_hf` | `https://huggingface.co/datasets/facebook/empathetic_dialogues` | `public_noncommercial` | `candidate_metadata_only` | `future_local_download_conditional` | `blocked_until_manifest_and_leakage_gates` | Non-commercial constraints must be preserved; no product, companion-readiness, commercial, or user-benefit claims. |
| `lmsys_chat_1m_hf` | `https://huggingface.co/datasets/lmsys/lmsys-chat-1m` | `gated_or_terms_required` | `blocked` | `blocked` | `false` | Raw card access returned unauthorized in 014 metadata check; operator terms review required before any use. |
| `personachat_parlai` | `https://github.com/facebookresearch/ParlAI/tree/main/projects/personachat` | `unknown_or_unclear` | `blocked` | `blocked` | `false` | Data license and download path were not established in 014; block until verified. |

## Download Boundary

A future implementation task may download only sources whose manifest rows satisfy all of these conditions:

- `source_license_tier` is `public_permissive`, `public_attribution_required`, `public_noncommercial`,
  `public_sharealike`, or `public_nc_sa`;
- `gated_terms_required=false`;
- `operator_terms_review_required=false` or `operator_terms_review_status=not_required`;
- `license_text_hash_or_card_hash` is recorded before download;
- `download_status=future_local_download_conditional`;
- `raw_text_policy=raw_local_only` or `hash_only`;
- `allowed_claim_ceiling` remains local, non-commercial, evidence-only where the source is non-commercial or share-alike;
- no source is used for product, companion-readiness, commercial, stable user-benefit, agency, emotion, subjectivity,
  consciousness, alive-status, or Bar-2 specialness claims.

The future downloader must refuse:

- gated or unauthorized sources;
- sources with unknown or unclear license;
- local/private sources without privacy mode;
- negative-evidence-only artifacts;
- sources requiring terms acceptance not performed by the operator;
- any source that would require uploading local/private data to third parties.

## Future Source Cache Boundary

If a later task creates a local source cache:

- raw downloaded files must stay under the task-specific `source_cache/` directory;
- cache metadata must record source URL/path, retrieved timestamp, license/card hash, byte size, file hashes, and row
  count when parseable;
- raw cache paths must not be staged by default;
- manifest artifacts committed to git should prefer hashes, counts, and minimized metadata over raw text;
- if a reduced excerpt file is needed, it must be redacted and justified by a separate task acceptance gate.

## B-011 Carry-Forward Boundary

Any future source manifest that becomes a capture preregistration input must pass these gates before capture:

- no split/meta leakage in user-visible text;
- effective independence beyond unique ids, with cluster keys for dataset, session/speaker, topic, template or
  near-duplicate surface, and affect band;
- causal path statement for what is being tested;
- affect coverage and expression-channel anti-degeneracy;
- leakage scanner with positive controls;
- no use of blocked/superseded post-hoc artifacts as source rows.

## Bounded Audit

- real objective: prevent authorized public/local source data work from bypassing license, privacy, leakage, and
  provenance gates.
- strongest baseline explanation: public dialogue data may still be reproducible by same-access controllers, so real
  text does not create attribution evidence by itself.
- strongest invalidity risk: treating `SOURCE_MANIFEST.json` or a raw cache as capture evidence before desktop trigger
  and replayable row provenance exist.
- falsifier for this framing: a future task can download or use a source without manifest license tier, privacy mode,
  admission status, and blocked downstream claims.
- evidence still insufficient: no source cache, no `SOURCE_MANIFEST.json`, no real desktop trigger, no `CREATURE_ON`,
  no same-access run, no score, and no comparison exist in 015.
- mechanism vs resemblance: this task is provenance/download-boundary design only.
- claim-inflation check: source manifest acceptance does not imply runtime integration or mechanism evidence.
- stop condition: any download, raw cache creation, gated access, terms acceptance, capture, score, comparison, verdict,
  program-state/evidence-ledger update, push, tag, or remote-anchor inside this task.
- rollback plan: delete this task directory, remove `EGODESKTOP-GABLATION-015` from `Tasks/TASK_BOARD.yaml`, restore
  014 next-action text, and regenerate route-convergence views.

## Task Card

- problem definition: define the source-manifest/download boundary required before using local EgoDesktop/EgoOperator
  artifacts or public dialogue datasets as real source-text candidates.
- current stage/layer: `engineering implementation / source manifest and download boundary design`.
- mainline target: future local-only source manifest and source cache, not current runtime.
- enabled-state requirement: no runtime enablement and no download in 015.
- real-trigger evidence requirement: none in 015; future capture still requires real EgoDesktop chat-turn trigger.
- hypothesis: an explicit manifest/download gate prevents user authorization from being misread as evidence authority.
- strongest baseline: same-access controller over the same public source text and all allowed local calibration history.
- ablation requirement: none in 015; future capture preregistration must still carry same-access, off/frozen, and replay
  floors.
- trace/replay requirement: none in 015; future manifest artifacts must be hash-addressed and replayable at the source
  selection level.
- computed-evidence provenance gate: no evidence score is produced; only manifest schema and candidate admission are
  specified.
- acceptance gate: source schema, candidate admission table, download boundary, raw-cache policy, B-011 carry-forward
  gates, and negative-evidence exclusion are specified.
- claim ceiling: source manifest/download boundary only.
- stop condition: any download, cache creation, capture, score, comparison, verdict, remotes, program-state, or evidence
  ledger mutation.
- rollback plan: remove 015, restore 014 next action, regenerate route views.
- expected changed files:
  - `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-source-manifest-download-boundary-v0/`
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

- candidate sources are classified as metadata-only, future-local-download-conditional, blocked, or negative-evidence-only;
- the download boundary blocks gated, unknown-license, local-private-without-privacy-mode, and negative-evidence sources;
- non-commercial and share-alike constraints are preserved in allowed claim ceilings;
- raw cache content is local-only by default and not staged by default;
- B-011 leakage, independence, causal path, affect coverage, and anti-degeneracy gates carry forward;
- 015 does not create `SOURCE_MANIFEST.json`, download data, create a source cache, capture rows, score, compare, or emit
  a verdict;
- local route checks pass;
- source-limited review returns no blocking findings before a follow-up implementation/download task.

## What This Can Prove

Only that source-manifest and download boundaries are specified before any data movement.

## What This Does Not Prove

This does not prove real source cache existence, desktop capture, `CREATURE_ON` effect, same-access saturation, baseline
score, candidate attribution, route advancement, product benefit, runtime integration safety, stable user benefit,
durable memory efficacy, agency, emotion, subjectivity, consciousness, alive status, or Bar-2 specialness.

## Next Minimal Closed-Loop Action

Open a separate implementation task to create `SOURCE_MANIFEST.json` and optionally download only eligible non-gated
public datasets into a local-only cache. Do not capture or score until a later preregistered capture design is accepted.
