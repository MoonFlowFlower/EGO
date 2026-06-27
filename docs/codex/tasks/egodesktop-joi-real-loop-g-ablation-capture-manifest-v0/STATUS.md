# EgoDesktop Joi Real-Loop G-ABLATION Capture Manifest v0 Status

- status: `accepted`
- task_id: `EGODESKTOP-GABLATION-021`
- parent_task_id: `EGODESKTOP-GABLATION-020`
- claim_ceiling: `capture_manifest_hash_selection_only`
- mainline_connected: `false`
- enabled: `false`
- real_trigger_evidence: `none_for_021_capture_manifest`
- runtime_authority: `none`

## Current Readback

- current branch: `main`
- source HEAD before 021 edits: `4c1d8a814bf3a4f3c033d142091e5cb1ea68c4aa`
- source worktree before 021 edits: clean except ignored 019 raw cache files
- 020 status: `accepted`
- 020 commit: `4c1d8a81 docs: define egodesktop desktop capture provenance`

## Current Claim Ceiling

This can prove only hash-only capture input selection. It does not trigger EgoDesktop or capture rows.

## TDD Evidence

- red test:
  `python -m pytest -q scripts\tests\test_build_egodesktop_gablation_capture_manifest.py`
  failed because `scripts\codex\build_egodesktop_gablation_capture_manifest.py` did not exist.
- fixture correction: the first green attempt exposed that the test fixture was missing the real 019
  `cache_written=true` report field; fixture was repaired to match `RAW_CACHE_REPORT`.
- green test:
  `python -m pytest -q scripts\tests\test_build_egodesktop_gablation_capture_manifest.py`
  passed with `2 passed`.

## Evidence Produced

- command:
  `python scripts\codex\build_egodesktop_gablation_capture_manifest.py --rows-per-source 5 --created-at 2026-06-27T00:00:00+00:00`
- manifest: `artifacts/egodesktop_joi_real_loop_g_ablation_capture_manifest_v0/CAPTURE_MANIFEST.json`
- manifest hash: `54af881d9d276524e5566230602a46e9d4a4f7e03cb90b34ea5c9ba1cbfc08bd`
- build report: `artifacts/egodesktop_joi_real_loop_g_ablation_capture_manifest_v0/BUILD_REPORT.json`
- source_count: `2`
- selected_row_count: `10`
- row_selection_rule: `first_5_rows_per_source_in_cached_jsonl_order`
- raw_text_in_manifest: `false`
- raw-text scan: `Say , Jim`, `I felt guilty`, `alpha raw text`, and `I felt proud` absent from
  `CAPTURE_MANIFEST.json`.
- ignored raw cache readback: `artifacts/egodesktop_joi_real_loop_g_ablation_source_cache_v0/source_cache/` remains
  ignored and unstaged.

## Local Checks

- `python -m pytest -q scripts\tests\test_build_egodesktop_gablation_capture_manifest.py scripts\tests\test_run_egodesktop_gablation_source_cache_downloader.py scripts\tests\test_build_egodesktop_gablation_source_manifest.py`: `13 passed`
- `python scripts\codex\verify_route_convergence.py`: `pass`
- `python scripts\codex\verify_repo.py --mode fast`: `pass`
- YAML parse for `Tasks/TASK_BOARD.yaml` and this `MUTATION_SCOPE.yaml`: `pass`
- `git diff --check`: `pass` with line-ending warnings only
- scoped closeout:
  `python scripts\codex_session_guard.py --mutation-scope docs\codex\tasks\egodesktop-joi-real-loop-g-ablation-capture-manifest-v0\MUTATION_SCOPE.yaml closeout-check --format markdown`
  reports `dirty_scoped/task_scoped/local_only/unsafe: 4 / 8 / 0 / 0`; remaining blockers are
  `push_pending`, `no_staged_changes`, and `remote_sync_unavailable`.

## Review Readback

- reviewer_status: `NO_BLOCKING_FINDINGS`
- reviewer_type: `Codex fallback reviewer; Claude CLI unavailable due subscription/403`
- reviewed_scope: builder, tests, 021 docs/task-board, capture manifest artifacts, route index
- reviewer_claim_ceiling: `capture_manifest_hash_selection_only`
- reviewer_next_action: accept 021 locally, then open a separate explicit desktop-trigger capture task if real
  EgoDesktop execution is still wanted.

## Next Minimal Closed-Loop Action

Commit 021 locally only. The next separate task must be an explicit desktop-trigger capture task before any row
serialization through EgoDesktop.
