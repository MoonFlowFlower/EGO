# VirtualCatPSPC v0 Status

## Current Milestone

Task 5: memory consolidation admission.

## Status

Task 5 local verification passed for this milestone. Publication is handled by the scoped commit and push for the current Codex turn.

## Decisions

- Keep repo authority unchanged: `docs/PROGRAM_STATE_UNIFIED.yaml` remains at `highest_evidence_level=E3`.
- Treat PSPC-local `E4_passed` and Task 5 `pass` as local lab status only.
- Keep `mainline_connected:false` and `enabled:false` for PSPC.
- Do not connect PSPC memory to EgoOperator memory or any runtime gate.
- Implement memory admission as `episodic traces -> semantic rule candidate -> admission gate -> semantic replay transitions -> learned world/self models`.
- Use semantic replay in the Task 5 audit so the admitted memory candidate has a causal training surface instead of being report-only text.
- Keep object-name shortcut protection intact: semantic candidate selection uses feature thresholds for instability/height, not object names.
- Do not treat this as admission readiness; Task 6 and later value/admission gates remain pending.

## Evidence Added This Milestone

- `artifacts/virtual_cat_pspc_v0/summary.json`
- `artifacts/virtual_cat_pspc_v0/MEMORY_CONSOLIDATION_ADMISSION_REPORT.md`
- `artifacts/virtual_cat_pspc_v0/memory_consolidation_admission.json`
- `labs/virtual_cat_pspc_v0/tests/test_memory_consolidation_admission.py`

## Commands Run

- `python -m pytest -q labs\virtual_cat_pspc_v0\tests\test_memory_consolidation_admission.py labs\virtual_cat_pspc_v0\tests\test_report_generation.py --basetemp $env:TEMP\pytest-pspc-task5-red` - expected fail, missing `run_memory_consolidation_admission`
- `python -m pytest -q labs\virtual_cat_pspc_v0\tests\test_memory_consolidation_admission.py --basetemp $env:TEMP\pytest-pspc-task5-green1` - pass, `2 passed`
- `python -m pytest -q labs\virtual_cat_pspc_v0\tests\test_report_generation.py --basetemp $env:TEMP\pytest-pspc-task5-report` - pass, `1 passed`
- `python -m py_compile labs\virtual_cat_pspc_v0\environment.py labs\virtual_cat_pspc_v0\memory.py labs\virtual_cat_pspc_v0\models.py labs\virtual_cat_pspc_v0\planning.py labs\virtual_cat_pspc_v0\experiments.py labs\virtual_cat_pspc_v0\run_experiments.py` - pass
- `python scripts\codex\check_program_state_integrity.py` - pass
- `python scripts\codex\verify_route_convergence.py` - pass
- `python scripts\codex\verify_mainline_clarity.py` - pass
- `python -m pytest -q labs\virtual_cat_pspc_v0\tests --basetemp $env:TEMP\pytest-pspc-task5-full` - pass, `21 passed`
- `python -m labs.virtual_cat_pspc_v0.run_experiments --out artifacts\virtual_cat_pspc_v0 --seeds 101,102,103` - pass, PSPC-local `E4_passed`, memory consolidation admission `pass`
- `python scripts\codex\lint_repo.py` - pass
- `git diff --check` - pass with line-ending warnings only
- `python scripts\codex\verify_repo.py --mode fast` - unavailable, `legacy/root OpenEmotion WinError 267`; does not count as PSPC pass and does not upgrade repo-wide pass status

## What This Proves

The memory-consolidation admission audit shows an admitted semantic rule candidate can be causally consumed through semantic replay records under a fixed lab target. Current Task 5 evidence:

- normal: semantic candidate `admitted`, action `observe`, caution `0.72`, approach danger prediction `0.9902`
- relevant deletion: semantic candidate `no_relevant_memory`, action `approach`, caution `0.00`, regression `0.72`
- irrelevant deletion: semantic candidate still `admitted`, action `observe`, caution delta `0.00`
- corrupted relevant memory: semantic candidate `admitted`, action `approach`, approach danger prediction `0.0001`, selected-action shift `observe -> approach`

## What This Does Not Prove

It does not prove durable memory consolidation outside this lab audit, homeostatic anti-reward-hacking, admission readiness, EgoOperator runtime efficacy, stable real user benefit, live autonomy, consciousness, or subjective experience.

## Rollback

Remove this milestone's memory-consolidation admission code, tests, report artifacts, summary fields, and task status updates. No EgoOperator rollback is needed because no runtime integration exists.
