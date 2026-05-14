# Repo Mainline Clarity v1 Plan

## Phase 1: Mainline View

- Add `docs/MAINLINE_QUICKSTART.md` as the first human onboarding page.
- Generate `docs/REPO_SURFACE_MAP.md` from route-convergence code.
- Register this task as a supporting active lane, not active default.
- Add `verify_mainline_clarity.py` to check README links, quickstart content, surface map drift, and staged operational exhaust.
- Wire the verifier into `verify_repo.py --mode fast`.

## Phase 2: Controlled Physical Archive

Deferred. Only begin after Phase 1 is stable and each move has caller/reference audit.

## Phase 3: Split / Restructure

Deferred. Only consider if Phase 1-2 still fail onboarding, CI isolation, or authority-boundary clarity.

## Validation

```bash
python3 -m py_compile scripts/codex/route_convergence_common.py scripts/codex/generate_route_convergence_views.py scripts/codex/verify_route_convergence.py scripts/codex/verify_mainline_clarity.py scripts/codex/verify_repo.py
python3 scripts/codex/generate_route_convergence_views.py
python3 scripts/codex/verify_route_convergence.py
python3 scripts/codex/verify_mainline_clarity.py
python3 scripts/codex/check_program_state_integrity.py --skip-diff-check
python3 scripts/codex/verify_repo.py --mode fast
git diff --check -- docs scripts .gitignore README.md
```
