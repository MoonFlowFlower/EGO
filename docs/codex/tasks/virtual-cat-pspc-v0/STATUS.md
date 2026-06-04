# VirtualCatPSPC v0 Status

## Current Milestone

Task 3: world-model causal strength.

## Status

Task 3 local verification passed for this milestone. Publication is handled by the scoped commit and push for the current Codex turn.

## Decisions

- Keep repo authority unchanged: `docs/PROGRAM_STATE_UNIFIED.yaml` remains at `highest_evidence_level=E3`.
- Treat PSPC-local `E4_passed` and Task 3 `pass` as local lab status only.
- Keep `mainline_connected:false` and `enabled:false` for PSPC.
- Keep the self model and target set fixed while replacing only the world model used by the planner.
- Require a visible score margin, not only nominal ordering, because a near-tie would mean the world-model causal signal remains weak.
- Do not treat this as admission readiness; Task 4 and later self/memory/value gates remain pending.

## Evidence Added This Milestone

- `artifacts/virtual_cat_pspc_v0/summary.json`
- `artifacts/virtual_cat_pspc_v0/WORLD_MODEL_CAUSAL_STRENGTH_REPORT.md`
- `artifacts/virtual_cat_pspc_v0/world_model_causal_strength.json`
- `labs/virtual_cat_pspc_v0/tests/test_world_model_causal_strength.py`

## Commands Run

- `python -m pytest -q labs\virtual_cat_pspc_v0\tests\test_world_model_causal_strength.py labs\virtual_cat_pspc_v0\tests\test_report_generation.py --basetemp %TEMP%\pytest-pspc-task3-green3` - pass, `3 passed`
- `python -m pytest -q labs\virtual_cat_pspc_v0\tests --basetemp %TEMP%\pytest-pspc-task3-full2` - pass, `17 passed`
- `python -m py_compile labs\virtual_cat_pspc_v0\environment.py labs\virtual_cat_pspc_v0\memory.py labs\virtual_cat_pspc_v0\models.py labs\virtual_cat_pspc_v0\planning.py labs\virtual_cat_pspc_v0\experiments.py labs\virtual_cat_pspc_v0\run_experiments.py` - pass
- `python -m pytest -q labs\virtual_cat_pspc_v0\tests --basetemp %TEMP%\pytest-pspc-task3-final` - pass, `17 passed`
- `python -m labs.virtual_cat_pspc_v0.run_experiments --out artifacts\virtual_cat_pspc_v0 --seeds 101,102,103` - pass, PSPC-local `E4_passed`, world-model causal strength `pass`
- `python scripts\codex\check_program_state_integrity.py` - pass
- `python scripts\codex\verify_route_convergence.py` - pass
- `python scripts\codex\verify_mainline_clarity.py` - pass
- `python scripts\codex\lint_repo.py` - pass
- `git diff --check` - pass with line-ending warnings only
- `python scripts\codex\verify_repo.py --mode fast` - unavailable, `legacy/root OpenEmotion WinError 267`; does not count as PSPC pass and does not upgrade repo-wide pass status

## What This Proves

The world-model causal-strength audit shows `normal > frozen > shuffled/random` planner support under a fixed self model and target set. The current scores are `normal=2.1511`, `frozen=0.5499`, `shuffled=0.4974`, and `random=0.3188`.

## What This Does Not Prove

It does not prove world-model causal strength outside this lab target set, self-model causal strength, memory consolidation validity, homeostatic anti-reward-hacking, admission readiness, EgoOperator runtime efficacy, stable real user benefit, live autonomy, consciousness, or subjective experience.

## Rollback

Remove this milestone's world-model causal audit code, tests, report artifacts, summary fields, and task status updates. No EgoOperator rollback is needed because no runtime integration exists.
