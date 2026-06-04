# VirtualCatPSPC v0 Status

## Current Milestone

Task 4: self-model causal strength.

## Status

Task 4 local verification passed for this milestone. Publication is handled by the scoped commit and push for the current Codex turn.

## Decisions

- Keep repo authority unchanged: `docs/PROGRAM_STATE_UNIFIED.yaml` remains at `highest_evidence_level=E3`.
- Treat PSPC-local `E4_passed` and Task 4 `pass` as local lab status only.
- Keep `mainline_connected:false` and `enabled:false` for PSPC.
- Keep the learned world model and target set fixed while replacing only the self model used by the planner.
- Extend the self model with an affinity head and make the homeostatic value consume ability/failure and affinity predictions, because otherwise head removal would not be causally visible to the planner.
- Reject action-label shortcutting: self-model inputs remain world-prediction fields, not direct action one-hot features, so Task 3 world-model causality is not bypassed.
- Do not treat this as admission readiness; Task 5 and later memory/value/admission gates remain pending.

## Evidence Added This Milestone

- `artifacts/virtual_cat_pspc_v0/summary.json`
- `artifacts/virtual_cat_pspc_v0/SELF_MODEL_CAUSAL_STRENGTH_REPORT.md`
- `artifacts/virtual_cat_pspc_v0/self_model_causal_strength.json`
- `labs/virtual_cat_pspc_v0/tests/test_self_model_causal_strength.py`

## Commands Run

- `python -m pytest -q labs\virtual_cat_pspc_v0\tests\test_self_model_causal_strength.py labs\virtual_cat_pspc_v0\tests\test_report_generation.py --basetemp $env:TEMP\pytest-pspc-task4-red` - expected fail, missing `run_self_model_causal_strength`
- `python -m pytest -q labs\virtual_cat_pspc_v0\tests\test_self_model_causal_strength.py labs\virtual_cat_pspc_v0\tests\test_models_and_planner.py --basetemp $env:TEMP\pytest-pspc-task4-green2` - pass, `8 passed`
- `python -m pytest -q labs\virtual_cat_pspc_v0\tests\test_self_model_causal_strength.py labs\virtual_cat_pspc_v0\tests\test_models_and_planner.py labs\virtual_cat_pspc_v0\tests\test_report_generation.py --basetemp $env:TEMP\pytest-pspc-task4-green4` - pass, `9 passed`
- `python -m py_compile labs\virtual_cat_pspc_v0\environment.py labs\virtual_cat_pspc_v0\memory.py labs\virtual_cat_pspc_v0\models.py labs\virtual_cat_pspc_v0\planning.py labs\virtual_cat_pspc_v0\experiments.py labs\virtual_cat_pspc_v0\run_experiments.py` - pass
- `python scripts\codex\check_program_state_integrity.py` - pass
- `python scripts\codex\verify_route_convergence.py` - pass
- `python scripts\codex\verify_mainline_clarity.py` - pass
- `python -m pytest -q labs\virtual_cat_pspc_v0\tests --basetemp $env:TEMP\pytest-pspc-task4-full` - pass, `19 passed`
- `python -m labs.virtual_cat_pspc_v0.run_experiments --out artifacts\virtual_cat_pspc_v0 --seeds 101,102,103` - pass, PSPC-local `E4_passed`, self-model causal strength `pass`
- `python scripts\codex\lint_repo.py` - pass
- `git diff --check` - pass with line-ending warnings only
- `python scripts\codex\verify_repo.py --mode fast` - unavailable, `legacy/root OpenEmotion WinError 267`; does not count as PSPC pass and does not upgrade repo-wide pass status

## What This Proves

The self-model causal-strength audit shows `normal > frozen/head-removed` planner support under a fixed learned world model and target set. Current Task 4 scores are:

- risk control: `normal=2.4947`, `frozen=0.0948`, `stress_removed=1.8442`
- ability planning: `normal=1.3838`, `ability_removed=0.0000`
- relationship preference: `normal=0.6185`, `affinity_removed=0.0000`

It also records action-level degradation: frozen self model changes risk-control action from `observe` to `approach`, ability removal changes ability-planning action from `observe` to `approach`, and affinity removal changes relationship-preference action from `observe` to `approach`.

## What This Does Not Prove

It does not prove self-model causal strength outside this lab target set, memory consolidation validity, homeostatic anti-reward-hacking, admission readiness, EgoOperator runtime efficacy, stable real user benefit, live autonomy, consciousness, or subjective experience.

## Rollback

Remove this milestone's self-model causal audit code, tests, report artifacts, summary fields, and task status updates. No EgoOperator rollback is needed because no runtime integration exists.
