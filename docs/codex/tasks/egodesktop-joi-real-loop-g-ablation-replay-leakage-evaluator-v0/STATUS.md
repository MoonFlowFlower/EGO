# EgoDesktop Joi Real-Loop G-ABLATION Replay/Leakage Evaluator v0 Status

- status: `blocked_expected__replay_leakage_preflight_callable`
- task_id: `EGODESKTOP-GABLATION-005`
- claim_ceiling: `egodesktop_real_loop_g_ablation_replay_leakage_evaluator_contract_only`
- mainline_connected: `false`
- enabled: `false_by_default`
- real_trigger_evidence: `callable_evaluator_over_004_trace_rows`
- runtime_authority: `none`
- claude_reviewer_status: `pending`

## Current Result

The replay/leakage evaluator slice is implemented as a pure artifact evaluator plus explicit CLI. It reads 004
`trace_rows.jsonl`, recomputes row hashes, runs a leakage scanner, injects a positive-control leakage case, and writes:

- `artifacts/egodesktop_joi_real_loop_g_ablation_replay_leakage_evaluator_v0/evaluation_report.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_replay_leakage_evaluator_v0/EVALUATION_REPORT.md`

The evaluator report records:

- `status: blocked_unreplayable_runtime_trace`
- `rows_evaluated: 1`
- `hash_integrity_status: pass`
- `leakage_scan_status: pass`
- `leakage_positive_control_status: pass`
- blockers: `placeholder_creature_state`, `placeholder_adapter_output`, `collect_only_replay_policy`,
  `missing_llm_replay_id`

This blocked result is the expected bounded result for 004 rows because the trace runner still stores placeholder
creature state and adapter output.

## Verification

- Red check: `node --test EgoDesktop\tests\joi_real_loop_g_ablation_replay_evaluator.test.js` failed before
  implementation because `../src/joiRealLoopGAblationReplayEvaluator` did not exist.
- Green check: `node --test EgoDesktop\tests\joi_real_loop_g_ablation_replay_evaluator.test.js` passed: `4 passed`.
- CLI run:
  `node EgoDesktop\scripts\evaluate-joi-g-ablation-replay.js --rows artifacts\egodesktop_joi_real_loop_g_ablation_chat_turn_trace_v0\trace\trace_rows.jsonl --out artifacts\egodesktop_joi_real_loop_g_ablation_replay_leakage_evaluator_v0 --run-id egodesktop_replay_leakage_eval_v0_on_004`
  exited `0` and produced the evaluator reports.

## Current Blocker

The current trace rows remain unreplayable for verdict purposes because they contain placeholder state/adapter surfaces and
no LLM replay id.

## Next Minimal Closed-Loop Action

Create the next bounded slice only after deciding whether to connect a real CreatureState/adapter snapshot and LLM replay
id into trace rows. Do not add baseline verdict logic until real replay recomputation is possible.

## What This Does Not Prove

This does not prove real-loop effect, baseline superiority, runtime integration safety, product benefit, stable user
benefit, durable memory efficacy, live autonomy, agency, real emotion, subjectivity, consciousness, alive status,
route advancement, or Bar-2 specialness.
