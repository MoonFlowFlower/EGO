# EgoDesktop Joi Real-Loop G-ABLATION Source Cache Downloader v0 Review

## Review Scope

Review only this downloader/metadata-smoke slice:

- `.gitignore`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-source-cache-downloader-v0/`
- `scripts/codex/run_egodesktop_gablation_source_cache_downloader.py`
- `scripts/tests/test_run_egodesktop_gablation_source_cache_downloader.py`
- `artifacts/egodesktop_joi_real_loop_g_ablation_source_cache_v0/CACHE_SMOKE_REPORT.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_source_cache_v0/CACHE_SMOKE_REPORT.sha256`
- `Tasks/TASK_BOARD.yaml` entry `EGODESKTOP-GABLATION-017`

Reviewer should not treat this as permission to commit raw dataset text, accept gated terms, capture `CREATURE_ON`, run
same-access baselines, score, compare, emit a verdict, update program state/evidence ledger, push, tag, or remote-anchor.

## Requested Verdict Format

- `NO_BLOCKING_FINDINGS`, with next minimal action; or
- `BLOCKING_FINDINGS`, with numbered blockers, required repairs, and next minimal action.

## Fallback Review 1

- reviewer: `Codex read-only reviewer fallback / source-limited`
- verdict: `NO_BLOCKING_FINDINGS`

Reviewer readback: 017 can be accepted at `source_cache_downloader_tool_and_metadata_smoke_only`. The implementation
admits only manifest/plan rows that are `candidate_metadata_only` and `future_local_download_conditional`, rejects
gated/operator-review cases, and limits inputs to Hugging Face dataset-page URLs. The emitted report stores only
metadata and hashes, with `raw_text_stored=false`, `raw_cache_created=false`, and all capture/scoring/runtime/program-
state/evidence-ledger/remote authority flags false. The raw cache path is excluded in `.gitignore`.

DailyDialog 404 is not a blocker for 017 because this task's acceptance is downloader behavior plus honest metadata
smoke. The 404 is preserved as negative metadata evidence: `reachable=false`, `status_code=404`.

Residual advisories:

- add explicit tests for local/private URL rejection and `negative_evidence_only` row rejection;
- consider turning non-HTTP network failures into reportable negative metadata results instead of aborts.

Repair applied: tests now explicitly cover local/private source rejection and `negative_evidence_only` source rejection.

Next minimal action: commit 017 locally only, then open a separate source-id repair/update task for `dailydialog_hf`.
