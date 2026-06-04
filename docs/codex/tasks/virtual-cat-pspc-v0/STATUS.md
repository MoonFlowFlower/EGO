# VirtualCatPSPC v0 Status

## Current Milestone

Task 0 + Task 1: closeout hygiene plus anti-hardcoding audit.

## Status

Task 0 + Task 1 local verification passed for this milestone. Publication is handled by the scoped commit and push for the current Codex turn.

## Decisions

- Keep repo authority unchanged: `docs/PROGRAM_STATE_UNIFIED.yaml` remains at `highest_evidence_level=E3`.
- Treat PSPC-local `E4_passed` as local lab status only.
- Keep `mainline_connected:false` and `enabled:false` for PSPC.
- Record `verify_repo.py --mode fast` unavailable as a repo-wide verification gap, not as a PSPC pass.
- Use object-renaming plus instability-feature deletion as the first anti-hardcoding slice before expanding to multi-seed or multi-layout work.

## Evidence Added This Milestone

- `artifacts/virtual_cat_pspc_v0/summary.json`
- `artifacts/virtual_cat_pspc_v0/ANTI_HARDCODING_AUDIT.md`
- `artifacts/virtual_cat_pspc_v0/anti_hardcoding_audit.json`
- `labs/virtual_cat_pspc_v0/tests/test_closeout_hygiene.py`
- `labs/virtual_cat_pspc_v0/tests/test_anti_hardcoding_audit.py`

## Commands Run

- `python -m py_compile labs\virtual_cat_pspc_v0\environment.py labs\virtual_cat_pspc_v0\memory.py labs\virtual_cat_pspc_v0\models.py labs\virtual_cat_pspc_v0\planning.py labs\virtual_cat_pspc_v0\experiments.py labs\virtual_cat_pspc_v0\run_experiments.py` - pass
- `python -m pytest -q labs\virtual_cat_pspc_v0\tests --basetemp %TEMP%\pytest-pspc-task0-task1-final` - pass, `13 passed`
- `python -m labs.virtual_cat_pspc_v0.run_experiments --out artifacts\virtual_cat_pspc_v0 --seeds 101,102,103` - pass, PSPC-local `E4_passed`, anti-hardcoding `pass`
- `python scripts\codex\check_program_state_integrity.py` - pass
- `python scripts\codex\verify_route_convergence.py` - pass
- `python scripts\codex\verify_mainline_clarity.py` - pass
- `python scripts\codex\lint_repo.py` - pass
- `git diff --check` - pass with line-ending warnings only
- `python scripts\codex\verify_repo.py --mode fast` - unavailable, `legacy/root OpenEmotion WinError 267`; does not count as PSPC pass and does not upgrade repo-wide pass status

## What This Proves

The summary now separates PSPC-local lab success from repo-wide verification status. The anti-hardcoding audit shows that object-name changes do not change the cautious decision, an unstable tall object without a `cup` name still gets cautious behavior, and removing the instability feature reduces caution in the audit slice.

## What This Does Not Prove

It does not prove multi-seed or multi-layout generalization, that all shortcut classes are absent, stronger world/self causal ordering, memory consolidation validity, homeostatic anti-reward-hacking, admission readiness, EgoOperator runtime efficacy, stable real user benefit, live autonomy, consciousness, or subjective experience.

## Rollback

Remove this milestone's added audit tests, audit report artifacts, summary fields, and task status updates. No EgoOperator rollback is needed because no runtime integration exists.
