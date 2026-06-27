# EgoDesktop Joi Real-Loop G-ABLATION Capture Manifest Refresh v0 - IMPLEMENT

## Source of truth

- `SPEC.md`
- `PLAN.md`
- `STATUS.md`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-capture-manifest-v0/`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-public-source-expansion-wizard-v0/`

## Execution rules

- Advance only `Refresh Three-Source Capture Manifest`.
- Preserve claim ceiling `capture_manifest_hash_selection_only`.
- Do not run EgoDesktop, serialize trace rows, replay, score, compare, emit verdicts, update program state/evidence
  ledger, push, tag, or remote-anchor.
- Keep raw source text under ignored `artifacts/egodesktop_joi_real_loop_g_ablation_source_cache_v0/source_cache/`.

## Scope control

- Allowed mutation surface is defined in `MUTATION_SCOPE.yaml`.
- No production code change is expected unless the freshness test proves the builder cannot consume the current raw cache.
- Existing G-ABLATION task docs remain historical authority for their own slices; this task records only the refresh.

## Validation strategy

- Red/green:
  - `python -m pytest -q scripts/tests/test_build_egodesktop_gablation_capture_manifest.py`
- Artifact regeneration:
  - `python scripts/codex/build_egodesktop_gablation_capture_manifest.py --rows-per-source 5 --created-at 2026-06-27T00:00:00+00:00`
- Route/repo:
  - `python scripts/codex/generate_route_convergence_views.py`
  - `python scripts/codex/verify_route_convergence.py`
  - `python scripts/codex/verify_repo.py --mode fast`
  - `git diff --check`
  - `python scripts/codex_session_guard.py --mutation-scope docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-capture-manifest-refresh-v0/MUTATION_SCOPE.yaml closeout-check --format markdown`

## Failure handling

- If the current raw cache is missing or hash validation fails, stop and report blocker.
- If raw text appears in committed artifacts, stop and rollback the artifact refresh.
- If route/repo verification fails outside the mutation surface, do not broaden scope; report the blocker.

## Final handoff checklist

- [ ] `PLAN.md` updated with outcome.
- [ ] `STATUS.md` updated with validation and next step.
- [ ] `BUILD_REPORT.json` read back as three sources / 15 rows.
- [ ] raw cache ignored and unstaged.
- [ ] closeout-check run with task mutation scope.
