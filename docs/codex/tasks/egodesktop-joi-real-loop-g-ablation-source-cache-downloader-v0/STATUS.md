# EgoDesktop Joi Real-Loop G-ABLATION Source Cache Downloader v0 Status

- status: `accepted_local_fallback_reviewed`
- task_id: `EGODESKTOP-GABLATION-017`
- parent_task_id: `EGODESKTOP-GABLATION-016`
- claim_ceiling: `source_cache_downloader_tool_and_metadata_smoke_only`
- mainline_connected: `false`
- enabled: `false`
- real_trigger_evidence: `none_for_017_downloader_tool`
- runtime_authority: `none`

## Current Readback

- current branch: `main`
- source HEAD before 017 edits: `75074e4f9f1bbe6c3a1de40bc7c2cd48e0c3e908`
- source worktree before 017 edits: clean
- 016 status: `accepted`
- 016 commit: `75074e4f feat: add egodesktop source manifest artifact`

## Current Claim Ceiling

This can prove only source-cache downloader tool behavior and metadata-only reachability/hash smoke.

## Evidence Produced

- downloader: `scripts/codex/run_egodesktop_gablation_source_cache_downloader.py`
- tests: `scripts/tests/test_run_egodesktop_gablation_source_cache_downloader.py`
- metadata smoke report:
  `artifacts/egodesktop_joi_real_loop_g_ablation_source_cache_v0/CACHE_SMOKE_REPORT.json`
- metadata smoke report hash:
  `6a0f07c4157a10491556e78b39b85792d33a120ddd38b9313971837856273f2d`
- `raw_text_stored=false`
- `raw_cache_created=false`
- `dailydialog_hf`: `status_code=404`, `reachable=false`
- `empathetic_dialogues_hf`: `status_code=200`, `reachable=true`

## Current Reviewer-Risk Readback

The metadata smoke found a live source-resolution issue: the manifest URL
`https://huggingface.co/datasets/daily_dialog` currently returns `404`. This is negative metadata evidence for that
source URL, not a pass. `facebook/empathetic_dialogues` returned `200`.

## Fallback Reviewer Readback

Source-limited fallback reviewer returned `NO_BLOCKING_FINDINGS`. Reviewer accepted 017 at
`source_cache_downloader_tool_and_metadata_smoke_only` because downloader behavior is bounded, raw text is not stored,
the raw-cache path is ignored, and DailyDialog 404 is preserved as negative metadata evidence rather than rewritten as
success.

Residual advisories handled:

- tests now explicitly cover local/private source rejection;
- tests now explicitly cover `negative_evidence_only` source rejection.

## Next Minimal Closed-Loop Action

Commit this 017 package locally only. Then open a separate source-id repair/update task for `dailydialog_hf` before any
raw-cache population task.

## What This Does Not Prove

This does not prove raw source cache completeness, dataset row availability, desktop capture, `CREATURE_ON` effect,
same-access saturation, baseline score, candidate attribution, route advancement, product benefit, runtime integration
safety, stable user benefit, durable memory efficacy, agency, emotion, subjectivity, consciousness, alive status, or
Bar-2 specialness.
