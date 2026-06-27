# EgoDesktop Joi Real-Loop G-ABLATION Capture Manifest Refresh v0 - PLAN

## Task summary

Refresh the capture manifest artifact from the current three-source raw-local cache while preserving the hash-only,
no-runtime-authority boundary.

## Execution mode

- mode: implementation
- why this mode: the next action is a bounded artifact refresh with existing builder code and clear acceptance.
- proof required after discovery: focused freshness test, generated artifact readback, route convergence, repo fast
  verification, and closeout-check.

## Milestones

### Milestone 1: Refresh Three-Source Capture Manifest

- type: implementation
- question: does the committed capture manifest match the current `RAW_CACHE_REPORT.json` after 024 added Wizard?
- current framing: the artifact is stale, not a runtime or scoring problem.
- hypotheses:
  - the existing builder can regenerate the manifest with no production-code change;
  - the refreshed manifest will contain three sources and 15 selected row hashes with no raw text.
- scope:
  - add a freshness regression test;
  - regenerate capture manifest artifacts;
  - update task docs/task board/route views.
- positive mechanism / observable behavior: committed hash-only capture manifest reflects every cache-written public
  source currently present in the raw cache report.
- experiments planned:
  - red: focused test fails against stale two-source artifact;
  - green: regenerate artifact and rerun focused tests.
- kill criteria: raw text would need to be staged, source cache missing, builder hash validation fails, or artifact
  cannot be refreshed without changing runtime/scoring paths.
- files / areas likely touched:
  - `scripts/tests/test_build_egodesktop_gablation_capture_manifest.py`
  - `artifacts/egodesktop_joi_real_loop_g_ablation_capture_manifest_v0/`
  - `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-capture-manifest-refresh-v0/`
  - `Tasks/TASK_BOARD.yaml`
  - `docs/codex/tasks/TASK_LANE_INDEX.md`
- acceptance:
  - current artifact freshness test fails before regeneration and passes after;
  - `BUILD_REPORT.json` reports `source_count=3` and `selected_row_count=15`;
  - manifest selected source ids include `dailydialog_hf`, `empathetic_dialogues_hf`, and
    `wizard_of_wikipedia_hf`;
  - raw text remains absent from committed artifact files;
  - `source_cache/` remains ignored and unstaged.
- validation:
  - `python -m pytest -q scripts/tests/test_build_egodesktop_gablation_capture_manifest.py`
  - `python scripts/codex/generate_route_convergence_views.py`
  - `python scripts/codex/verify_route_convergence.py`
  - `python scripts/codex/verify_repo.py --mode fast`
  - `git diff --check`
- rollback note: revert test/artifact/docs/task-board changes and regenerate route views.

## Progress

- current_status: `accepted_local`
- current_milestone: `Refresh Three-Source Capture Manifest`
- milestone_state: `complete`
- candidate_vs_proof: `proof_passed`

## Decision log

- 2026-06-27: Treat 025 as an artifact refresh after 024, not as desktop trigger, replay, scoring, or route
  advancement.
- 2026-06-27: Red freshness test failed for the expected reason: the stale manifest lacked
  `wizard_of_wikipedia_hf`.
- 2026-06-27: No builder code change was needed; regenerating with the existing callable builder produced a three-source,
  15-row hash-only manifest.

## Surprises / discoveries

- The existing builder already handled all cache-written sources; the defect was artifact staleness, not production code.

## Outcomes / retrospective

- this round has proven: current capture manifest artifacts now reflect the current three-source raw cache as hash-only
  future capture selection.
- still not proven: capture, replay, scoring, same-access saturation, attribution, route advancement, runtime effect
- this round ruled out: need for a builder/runtime change in this slice.
- next minimal closed-loop action: if continuing this lane, open a separate selected-source desktop trigger smoke for a
  predeclared Wizard row through `window.egoDesktop.sendChatTurn(...)`, still without scoring or verdict.
