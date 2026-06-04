# VirtualCatPSPC v0 Status

## Current Milestone

Task 7: admission packet contract, with no adapter.

## Status

Task 7 local verification passed for this milestone. Publication is handled by the scoped commit and push for the current Codex turn.

## Decisions

- Keep repo authority unchanged: `docs/PROGRAM_STATE_UNIFIED.yaml` remains at `highest_evidence_level=E3`.
- Treat PSPC-local `E4_passed` and Task 7 `pass` as local lab/contract status only.
- Keep `mainline_connected:false` and `enabled:false` for PSPC.
- Define only a proposal packet schema; do not create `EgoOperator/adapters/pspc_lab_adapter.py`.
- Keep the packet claim level at `lab_only_proto_self_mechanism_candidate`.
- Require `proposal.trace_refs`; reject `proposal.reason_trace_refs` to avoid parallel packet dialects.
- Require `forbidden.runtime_gate_bypass=true` in addition to direct action/message/memory write flags.
- Do not treat this as adapter readiness; Task 8 go/no-go review remains pending.

## Evidence Added This Milestone

- `docs/codex/tasks/virtual-cat-pspc-v0/ADMISSION_PACKET_CONTRACT.md`
- `artifacts/virtual_cat_pspc_v0/summary.json`
- `artifacts/virtual_cat_pspc_v0/ADMISSION_PACKET_CONTRACT_REPORT.md`
- `artifacts/virtual_cat_pspc_v0/admission_packet_contract.schema.json`
- `labs/virtual_cat_pspc_v0/admission_packet.py`
- `labs/virtual_cat_pspc_v0/tests/test_admission_packet_contract.py`

## Commands Run

- `python scripts\codex_session_guard.py bootstrap --format markdown` - pass, repo remains `current_phase=ego_operator_human_operator_trial_v2_real_provider_scripted_review_pending`, `highest_evidence_level=E3`
- `python -m pytest -q labs\virtual_cat_pspc_v0\tests\test_admission_packet_contract.py --basetemp $env:TEMP\pytest-pspc-task7-red` - expected fail, missing `labs.virtual_cat_pspc_v0.admission_packet`
- `python -m pytest -q labs\virtual_cat_pspc_v0\tests\test_contract_docs.py --basetemp $env:TEMP\pytest-pspc-task7-doc-red` - expected fail, missing `ADMISSION_PACKET_CONTRACT.md`
- `python -m pytest -q labs\virtual_cat_pspc_v0\tests\test_admission_packet_contract.py --basetemp $env:TEMP\pytest-pspc-task7-green-schema` - pass, `3 passed`
- `python -m pytest -q labs\virtual_cat_pspc_v0\tests\test_contract_docs.py --basetemp $env:TEMP\pytest-pspc-task7-green-docs` - pass, `3 passed`
- `python -m pytest -q labs\virtual_cat_pspc_v0\tests\test_report_generation.py --basetemp $env:TEMP\pytest-pspc-task7-green-report` - failed, contract report lacked a trace/audit marker
- `python -m pytest -q labs\virtual_cat_pspc_v0\tests\test_report_generation.py --basetemp $env:TEMP\pytest-pspc-task7-green-report2` - pass, `1 passed`
- `python -m labs.virtual_cat_pspc_v0.run_experiments --out artifacts\virtual_cat_pspc_v0 --seeds 101,102,103` - pass, PSPC-local `E4_passed`, admission packet contract `pass`
- `python scripts\codex\generate_program_state_views.py` - pass
- `python scripts\codex\generate_route_convergence_views.py` - pass
- `python -m py_compile labs\virtual_cat_pspc_v0\admission_packet.py labs\virtual_cat_pspc_v0\environment.py labs\virtual_cat_pspc_v0\memory.py labs\virtual_cat_pspc_v0\models.py labs\virtual_cat_pspc_v0\planning.py labs\virtual_cat_pspc_v0\experiments.py labs\virtual_cat_pspc_v0\run_experiments.py` - pass
- `python scripts\codex\check_program_state_integrity.py` - initial fail because evidence ledger `source_type=contract` was not allowed; fixed to `doc`
- `python scripts\codex\check_program_state_integrity.py` - pass
- `python scripts\codex\verify_route_convergence.py` - pass
- `python scripts\codex\verify_mainline_clarity.py` - pass
- `if (Test-Path EgoOperator\adapters\pspc_lab_adapter.py) { Write-Error 'adapter exists'; exit 1 } else { 'adapter absent' }` - pass, adapter absent
- `python -m pytest -q labs\virtual_cat_pspc_v0\tests\test_admission_packet_contract.py labs\virtual_cat_pspc_v0\tests\test_contract_docs.py labs\virtual_cat_pspc_v0\tests\test_report_generation.py --basetemp $env:TEMP\pytest-pspc-task7-directed-final` - pass, `7 passed`
- `python -m pytest -q labs\virtual_cat_pspc_v0\tests --basetemp $env:TEMP\pytest-pspc-task7-full` - pass, `27 passed`
- `python scripts\codex\lint_repo.py` - pass
- `git diff --check` - pass with line-ending warnings only
- `python scripts\codex\verify_repo.py --mode fast` - unavailable, `legacy/root OpenEmotion WinError 267`; does not count as PSPC pass and does not upgrade repo-wide pass status

## What This Proves

The Task 7 contract proves that PSPC v0 now has a test-validated proposal-only packet schema:

- `source` is fixed to `virtual_cat_pspc_v0`.
- `claim_level` is fixed to `lab_only_proto_self_mechanism_candidate`.
- `mainline_connected` and `enabled` are fixed to `false`.
- `proposal.trace_refs` is the only trace-reference field.
- `evidence` carries world prediction, self prediction, homeostatic score, and ablation status.
- direct action, direct user message, direct memory write, and runtime gate bypass are all explicitly forbidden.
- tests confirm no EgoOperator runtime import and no adapter file.

## What This Does Not Prove

It does not prove adapter readiness, EgoOperator runtime efficacy, stable real user benefit, live autonomy, production integration safety, consciousness, or subjective experience.

## Rollback

Remove this milestone's admission packet schema module, tests, contract doc, generated schema/report artifacts, summary fields, and task status updates. No EgoOperator rollback is needed because no adapter or runtime integration exists.
