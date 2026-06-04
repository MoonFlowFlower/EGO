# VirtualCatPSPC v0 Status

## Current Milestone

Task 2: multi-seed / multi-layout / multi-object generalization.

## Status

Task 2 local verification passed for this milestone. Publication is handled by the scoped commit and push for the current Codex turn.

## Decisions

- Keep repo authority unchanged: `docs/PROGRAM_STATE_UNIFIED.yaml` remains at `highest_evidence_level=E3`.
- Treat PSPC-local `E4_passed` and Task 2 `pass` as local lab status only.
- Keep `mainline_connected:false` and `enabled:false` for PSPC.
- Run the generalization matrix across seeds `101,102,103`, layouts `center_room / near_wall`, and object kinds `cup / vase / bottle / tall_box`.
- Do not treat this as admission readiness; Task 3 and later causal-strength gates remain pending.

## Evidence Added This Milestone

- `artifacts/virtual_cat_pspc_v0/summary.json`
- `artifacts/virtual_cat_pspc_v0/GENERALIZATION_MATRIX_REPORT.md`
- `artifacts/virtual_cat_pspc_v0/generalization_matrix.json`
- `labs/virtual_cat_pspc_v0/tests/test_multi_seed_layout_generalization.py`

## Commands Run

- `python -m pytest -q labs\virtual_cat_pspc_v0\tests\test_multi_seed_layout_generalization.py labs\virtual_cat_pspc_v0\tests\test_report_generation.py --basetemp %TEMP%\pytest-pspc-task2-green2` - pass, `3 passed`
- `python -m py_compile labs\virtual_cat_pspc_v0\environment.py labs\virtual_cat_pspc_v0\memory.py labs\virtual_cat_pspc_v0\models.py labs\virtual_cat_pspc_v0\planning.py labs\virtual_cat_pspc_v0\experiments.py labs\virtual_cat_pspc_v0\run_experiments.py` - pass
- `python -m pytest -q labs\virtual_cat_pspc_v0\tests --basetemp %TEMP%\pytest-pspc-task2-full` - pass, `15 passed`
- `python -m pytest -q labs\virtual_cat_pspc_v0\tests --basetemp %TEMP%\pytest-pspc-task2-final` - pass, `15 passed`
- `python -m labs.virtual_cat_pspc_v0.run_experiments --out artifacts\virtual_cat_pspc_v0 --seeds 101,102,103` - pass, PSPC-local `E4_passed`, anti-hardcoding `pass`, multi-seed/layout generalization `pass`
- `python scripts\codex\check_program_state_integrity.py` - pass
- `python scripts\codex\verify_route_convergence.py` - pass
- `python scripts\codex\verify_mainline_clarity.py` - pass
- `python scripts\codex\lint_repo.py` - pass
- `git diff --check` - pass with line-ending warnings only
- `python scripts\codex\verify_repo.py --mode fast` - unavailable, `legacy/root OpenEmotion WinError 267`; does not count as PSPC pass and does not upgrade repo-wide pass status

## What This Proves

The generalization matrix shows danger-history caution above safe-history baseline across seeds `101,102,103`, layouts `center_room / near_wall`, and unstable object kinds `cup / vase / bottle / tall_box`.

## What This Does Not Prove

It does not prove unlimited layout generalization, stronger world/self causal ordering, memory consolidation validity, homeostatic anti-reward-hacking, admission readiness, EgoOperator runtime efficacy, stable real user benefit, live autonomy, consciousness, or subjective experience.

## Rollback

Remove this milestone's generalization matrix code, tests, report artifacts, summary fields, and task status updates. No EgoOperator rollback is needed because no runtime integration exists.
