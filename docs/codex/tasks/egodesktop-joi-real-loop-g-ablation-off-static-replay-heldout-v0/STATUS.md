# EgoDesktop Joi Real-Loop G-ABLATION OFF_STATIC_REPLAY_HELDOUT v0 Status

- status: `accepted__off_static_replay_heldout_replay_row_written`
- task_id: `EGODESKTOP-GABLATION-008`
- claim_ceiling: `egodesktop_real_loop_g_ablation_off_static_replay_heldout_replay_row_contract_only`
- mainline_connected: `false`
- enabled: `explicit_cli_only`
- real_trigger_evidence: `builder_cli_and_evaluator_precondition_cli`
- runtime_authority: `none`

## Current Objective

Produce one replayable `OFF_STATIC_REPLAY_HELDOUT` non-LLM `D` row from the current 006 trace row. The 007 precondition
must pass for this row, but no baseline, attribution, or route verdict may be emitted.

## Evidence Produced

- row artifact:
  `artifacts/egodesktop_joi_real_loop_g_ablation_off_static_replay_heldout_v0/trace/trace_rows.jsonl`
- builder report:
  `artifacts/egodesktop_joi_real_loop_g_ablation_off_static_replay_heldout_v0/trace/builder_report.json`
- evaluator report:
  `artifacts/egodesktop_joi_real_loop_g_ablation_off_static_replay_heldout_v0/evaluator/evaluation_report.json`
- source row hash: `7f1d608088609b7909d2f527c336f4403d67553ea4b6d8512f1967fbd6b249f1`
- produced row hash: `bd120552670850025ab531a8dc8b9a064c50ba30277115451a0d86c84b38de04`
- split contract status: `synthetic_calibration_reference_distinct_from_heldout_observation`
- calibration reference kind: `synthetic_reference`
- calibration reference hash: `ba6172ab57fc4b3b2f1f937666969f86610fc23e49377b49c0180d59ee81ccd3`
- calibration reference pack hash: `958d1af423bd716ad2f53dce152178a9d517af87d684ca60bbd87d878a107a76`
- heldout observation source hash: `7f1d608088609b7909d2f527c336f4403d67553ea4b6d8512f1967fbd6b249f1`
- heldout prompt pack hash: `432a250a4e2458278e80e2b944a0b08c92cf00ff447173cee80694de10087cb6`
- heldout prompt pack scope: `single_smoke_prompt_not_full_pack`
- observation shuffle control: `pass`
- observation shuffle control evidence scope: `regression_guard_constructive_until_nontrivial_calibration`
- row condition: `OFF_STATIC_REPLAY_HELDOUT`
- `llm_replay_id`: `none`
- `d_field_mode`: `non_llm_adapter_output_only`
- `d_fields_frozen`: `true`
- `llm_dependency`: `excluded_from_d`
- `offline_replay_function_id`: `off_static_replay_heldout_non_llm_adapter_v0`

## Acceptance Readback

- `node --test EgoDesktop\tests\joi_real_loop_g_ablation_off_static_replay.test.js`: `3 passed`
- `node --test EgoDesktop\tests\joi_real_loop_g_ablation_replay_evaluator.test.js`: `7 passed`
- `node --test EgoDesktop\tests\joi_real_loop_g_ablation_backend_snapshot.test.js`: `5 passed`
- `node --test EgoDesktop\tests\joi_real_loop_g_ablation_trace_runner.test.js`: `7 passed`
- `node --test EgoDesktop\tests\joi_real_loop_g_ablation_chat_turn_trace.test.js`: `2 passed`
- `npm test` from `EgoDesktop`: `90 passed`
- builder CLI:
  `off_static_replay_heldout_row_written`, `trace_row_count=1`
- evaluator CLI:
  `status=replay_integrity_preflight_pass_no_verdict`, `blockers=[]`
- scoring precondition:
  `status=d_field_replay_precondition_pass_no_scoring_verdict`,
  `d_field_replay_precondition_satisfied=true`, `scoring_authorized=false`,
  `scoring_run_authorized=false`, `verdict_authorized=false`
- `python -m pytest -q tests\test_egodesktop_gablation_review_repair.py tests\test_ego_operator_desktop_trace_snapshot.py`:
  `6 passed`
- `python scripts\codex\verify_route_convergence.py`: `pass`
- `python scripts\codex\verify_repo.py --mode fast`: `pass`
- `git diff --check`: clean
- scoped closeout:
  mutation scope loaded, post-commit dirty scoped/task scoped/local-only/unsafe = `0 / 0 / 0 / 0`; remaining blockers
  were `push_pending` and `no_staged_changes`, with push/remote anchor not authorized by this task.

## What This Proves

One `OFF_STATIC_REPLAY_HELDOUT` static replay heldout row can be rebuilt from complete serialized state plus public
observation by a callable local non-LLM adapter recompute path. The row now explicitly marks its calibration source as a
synthetic reference distinct from the heldout observation, carries the calibration reference hash on the consumed adapter
seed, uses a true hash for the heldout prompt-pack descriptor, and records the observation-shuffle control as a
constructive regression guard until nontrivial calibration exists. The 007 D-field replay precondition is satisfied for
this row, but scoring and verdict runs remain unauthorized.

## What This Does Not Prove

This does not prove baseline saturation, creature failure, candidate attribution, real-loop effect, route advancement,
product benefit, runtime integration safety, stable user benefit, durable memory efficacy, agency, emotion,
subjectivity, consciousness, alive status, or Bar-2 specialness.

## Next Minimal Closed-Loop Action

Open a separate bounded slice that replaces the synthetic calibration reference with a captured/fitted calibration source
before building the paired `CREATURE_ON` non-LLM `D` replay row. Do not score or compare in this task.

## Claude Review Readback

Desktop Claude returned `NO_BLOCKING_FINDINGS` source-limited for the narrow 008 claim after the B1/B2/B3 repair. Its
carry-forward C1-C4 requested the synthetic-reference qualifier, adapter-seed calibration hash, shuffle-control evidence
scope, and true heldout prompt-pack hash/scope recorded here before any future `CREATURE_ON` or scoring slice.
