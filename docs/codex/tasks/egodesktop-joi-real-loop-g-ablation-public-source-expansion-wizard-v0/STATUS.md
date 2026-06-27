# EgoDesktop Joi Real-Loop G-ABLATION Public Source Expansion Wizard v0 Status

- status: `accepted_local`
- task_id: `EGODESKTOP-GABLATION-024`
- parent_task_id: `EGODESKTOP-GABLATION-019`
- claim_ceiling: `public_source_expansion_raw_local_cache_only`
- mainline_connected: `false`
- enabled: `source_manifest_and_raw_local_cache_only`
- real_trigger_evidence: `none_collection_only`
- runtime_authority: `none`

## Current Readback

- current branch: `main`
- source HEAD before 024 edits: `2545f3bd test: add selected source replay preflight evidence`
- source worktree before 024 edits: clean except ignored source cache
- current manifest public raw-cache sources before 024: `dailydialog_hf`, `empathetic_dialogues_hf`
- live source metadata readback: Hugging Face API for `chujiezheng/wizard_of_wikipedia` returned
  `gated=false`, `license:cc-by-nc-4.0`.
- TDD red checks:
  - `python -m pytest -q scripts/tests/test_build_egodesktop_gablation_source_manifest.py` failed on missing
    `wizard_of_wikipedia_hf`.
  - `python -m pytest -q scripts/tests/test_run_egodesktop_gablation_source_cache_downloader.py` failed on missing
    `wizard_of_wikipedia_hf` manifest/download action support after the test fixture URL match was corrected.
- TDD green checks:
  - source manifest tests: `3 passed`
  - source cache downloader tests: `8 passed`
- source manifest hash: `cfe381eb608d609efd07bc3cf1d83718d8ed21b25a0c108bdd928d41ff3ee913`
- source download plan hash: `a9e1aaf5a582c22f1a421301e19f6d5ea59e9f494db2fcd9595e882d24678d5b`
- metadata smoke command:
  `python scripts/codex/run_egodesktop_gablation_source_cache_downloader.py --created-at 2026-06-27T00:00:00+00:00`
- metadata smoke result: `dailydialog_hf`, `empathetic_dialogues_hf`, and `wizard_of_wikipedia_hf` all reachable with
  `status_code=200`; `raw_text_stored=false`.
- raw cache command:
  `python scripts/codex/run_egodesktop_gablation_source_cache_downloader.py --raw-cache-sample --split train --max-rows 25 --created-at 2026-06-27T00:00:00+00:00`
- raw cache report: `artifacts/egodesktop_joi_real_loop_g_ablation_source_cache_v0/RAW_CACHE_REPORT.json`
- raw cache sources:
  - `dailydialog_hf`: `row_count=25`, `num_rows_total=11118`,
    `cache_sha256=b2b6a2d348b2f71cea91a25e94c170f61e7eac5c5d4233121a56232883d50036`
  - `empathetic_dialogues_hf`: `row_count=25`,
    `cache_sha256=7f5fa7fc25a429d6959ac0cab5549e47c239f8a0ffb637486308d6aa2e72e494`
  - `wizard_of_wikipedia_hf`: `row_count=25`, `num_rows_total=18430`,
    `cache_sha256=622253df96a131ac3e6e807ad0ca573c93f742e3caf1e860719ea111f964eb4d`
- committed-report raw text scan: `pass`; first sampled wizard raw prompt is absent from source manifest, download
  plan, raw cache report, and raw cache report sidecar.
- raw source cache location: `artifacts/egodesktop_joi_real_loop_g_ablation_source_cache_v0/source_cache/`
- raw source cache staging status: ignored by `.gitignore`.

## Current Claim Ceiling

This can prove only public source expansion and raw-local cache collection. It does not prove capture, replay, scoring,
runtime effect, or mechanism attribution.

## Next Minimal Closed-Loop Action

Use the expanded three-source raw-local cache only as input to a future separately carded capture-manifest refresh or
selected-source trigger slice; do not treat this collection task as capture, replay, scoring, or route advancement.
