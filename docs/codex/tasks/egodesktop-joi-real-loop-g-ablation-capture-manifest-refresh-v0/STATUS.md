# EgoDesktop Joi Real-Loop G-ABLATION Capture Manifest Refresh v0 - STATUS

## Current milestone

- name: `Refresh Three-Source Capture Manifest`
- owner: `Codex`
- state: `complete`
- type: implementation

## Current state

- current_layer: `engineering implementation / capture manifest refresh`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `explicit local artifact builder only`
- real_trigger_evidence: `none_hash_selection_only`
- completion_class: `accepted_local`
- candidate_vs_proof: `proof_passed`
- claim_ceiling: `capture_manifest_hash_selection_only`

## Completed work

- Task package created and scoped.
- Acceptance path locked to artifact freshness, raw-text absence, and local verification.
- Added freshness regression test for committed capture manifest versus current `RAW_CACHE_REPORT.json`.
- Red test failed against stale two-source artifact because `wizard_of_wikipedia_hf` was missing.
- Regenerated capture manifest artifacts with the existing callable builder.
- Green focused test passed with three sources and 15 selected row hashes.

## Last experiment

- question: can the committed capture manifest be proven stale relative to the current three-source raw cache?
- framing: artifact freshness, not runtime behavior.
- result: red test failed as expected, then passed after regeneration.
- evidence_upgraded: no

## What was learned

- The builder code already supported the current raw cache shape; the committed artifact was stale.
- The refreshed manifest preserves no runtime/scoring/capture authority.

## What was ruled out

- This task does not authorize desktop trigger, replay, scoring, same-access comparison, or route verdict.
- A manifest refresh alone does not create real trigger evidence.

## Next framing

- The next slice must be an explicit selected-source desktop trigger smoke if this lane continues.

## Last validation results

- mode: focused + route + repo fast
- result: pass
- summary: focused capture-manifest tests passed; route convergence passed; repo fast verifier passed; diff check clean
  except LF-to-CRLF warnings on touched files.

## Decisions made

- 2026-06-27: Use existing capture builder if the red test shows only artifact staleness.
- 2026-06-27: Mark 025 accepted locally after three-source artifact readback and verification.

## Open risks

- Raw cache files are local ignored inputs; if missing, the task blocks.
- A refreshed manifest still proves only hash selection, not capture.
- proof gap: no real desktop trigger evidence in this slice.

## Next step

- Open a separate selected-source desktop trigger smoke for one predeclared Wizard row, if continuing the G-ABLATION lane.

## Commands run / evidence

- Red:
  - `python -m pytest -q scripts\tests\test_build_egodesktop_gablation_capture_manifest.py`
  - result: `1 failed, 2 passed`; failure was expected missing `wizard_of_wikipedia_hf`.
- Artifact:
  - `python scripts\codex\build_egodesktop_gablation_capture_manifest.py --rows-per-source 5 --created-at 2026-06-27T00:00:00+00:00`
  - `artifacts/egodesktop_joi_real_loop_g_ablation_capture_manifest_v0/CAPTURE_MANIFEST.json`
  - `artifacts/egodesktop_joi_real_loop_g_ablation_capture_manifest_v0/BUILD_REPORT.json`
  - `capture_manifest_sha256=32ccd9925bf46b555b2ffbcb225beb6e3bd7834a0b23d1b80296884b6ecfdc26`
  - `source_count=3`
  - `selected_row_count=15`
  - selected sources: `dailydialog_hf`, `empathetic_dialogues_hf`, `wizard_of_wikipedia_hf`
- Green:
  - `python -m pytest -q scripts\tests\test_build_egodesktop_gablation_capture_manifest.py`
  - result: `3 passed`
- Route/repo:
  - `python scripts\codex\generate_route_convergence_views.py`
  - `python scripts\codex\verify_route_convergence.py`
  - result: `pass`
  - `python scripts\codex\verify_repo.py --mode fast`
  - result: `pass`
  - `git diff --check`
  - result: pass with LF-to-CRLF warnings on touched files
