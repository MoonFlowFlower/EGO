# EgoDesktop Joi Real-Loop G-ABLATION Replay/Leakage Evaluator v0 Spec

- task_id: `EGODESKTOP-GABLATION-005`
- status: `active`
- created_at: `2026-06-26`
- owner: `Codex`
- layer: `engineering implementation / replay integrity and leakage preflight`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `false_by_default`
- real_trigger_evidence: `none_yet_for_this_slice`
- claim_ceiling: `egodesktop_real_loop_g_ablation_replay_leakage_evaluator_contract_only`
- auto_remote_anchor: `forbidden`

## Problem Definition

`EGODESKTOP-GABLATION-004` produced a real Electron chat-turn trace row through the renderer IPC path. The next valid
slice is not a route verdict or same-access baseline tournament. The next valid slice is a callable evaluator that reads
the produced rows, recomputes internal hashes, scans for leakage or authority fields, runs a leakage positive-control
case, and honestly blocks replay/verdict claims while the row still contains placeholder creature state and adapter
output.

## Bounded Audit

- real objective: make replay/leakage preflight callable over 004 trace rows.
- strongest baseline explanation: current shim output plus placeholder trace-runner state explains the row; no creature
  mechanism effect is available.
- strongest invalidity risk: treating row hash consistency as replay recomputation or treating leakage-clean status as a
  positive attribution signal.
- falsifier for this framing: if the evaluator cannot detect an injected leakage positive control, the slice is invalid.
- insufficient evidence: a report that only says clean without recomputing hashes, invoking a scanner, or running a
  positive-control case.
- task type: evidence-hygiene evaluator only, not mechanism validation.
- hard-coding check: verdict labels must be derived from callable row checks, not static success literals.
- leakage check: scan for future/target/verdict leakage and runtime-authority fields in row payload surfaces.
- stop condition: any positive route/verdict label, any default runtime enablement, or any need to weaken 002-004
  contracts.

## Mainline Target

This target is an explicit local evaluator/CLI over artifact rows. It must not connect to default EgoDesktop runtime,
must not register a runtime adapter, and must not update `docs/PROGRAM_STATE_UNIFIED.yaml` or evidence-ledger claims.

## Enabled-State Requirement

The evaluator is callable only by an explicit command or test import. It has no renderer/main-process hook and no default
runtime effect.

## Real-Trigger Evidence Requirement

Acceptance requires running the evaluator over:

- `artifacts/egodesktop_joi_real_loop_g_ablation_chat_turn_trace_v0/trace/trace_rows.jsonl`

and producing:

- `artifacts/egodesktop_joi_real_loop_g_ablation_replay_leakage_evaluator_v0/evaluation_report.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_replay_leakage_evaluator_v0/EVALUATION_REPORT.md`

The report must show row hash recomputation, leakage positive-control detection, and a blocked replay/verdict status for
placeholder trace rows.

## Hypothesis

If 004 rows are well-formed but still placeholder-backed, a callable evaluator should verify hash/replay-input integrity
and leakage scanner behavior while refusing any causal or baseline verdict.

## Strongest Baseline

Same-access and static replay baselines remain stronger explanations than any current positive claim. This slice may only
prepare the evidence surface; it must not score or compare those baselines.

## Ablation Requirement

The only ablation-like requirement in this slice is a leakage positive-control injection that the scanner must catch.
No condition reruns or same-access reproducer evaluation are authorized.

## Trace / Replay Requirement

The evaluator must distinguish:

- hash integrity preflight: allowed in this slice;
- real replay recomputation from serialized state plus observation: not yet available for placeholder rows;
- baseline/verdict evaluation: forbidden in this slice.

Rows with `state_source: not_connected_in_trace_runner_v0`, `adapter_status: not_connected_trace_runner_v0`, or
`replay_policy: trace_runner_v0_collect_only` must block replay/verdict claims.

## Computed-Evidence Provenance Gate

The evaluator report must record:

- producer function;
- input trace path;
- row count;
- aggregation rule;
- source hash for the evaluator;
- positive-control result.

## Acceptance Gate

- Task card and mutation scope exist before evaluator implementation.
- Tests are written first and fail before implementation.
- Evaluator recomputes `creature_state_hash`, `adapter_output_hash`, `public_inputs_hash`, `replay_inputs_hash`, and
  `row_hash`.
- Evaluator detects injected leakage/authority positive control.
- Evaluator blocks placeholder 004 rows as `blocked_unreplayable_runtime_trace`.
- Evaluator writes JSON and Markdown reports from a callable CLI.
- `npm test` from `EgoDesktop` passes.
- `python scripts/codex/verify_repo.py --mode fast` passes.
- Scoped closeout reports no unsafe dirty paths.

## Claim Ceiling

`egodesktop_real_loop_g_ablation_replay_leakage_evaluator_contract_only`.

This can prove only that a local evaluator can check trace-row integrity and leakage scanner positive controls. It cannot
prove real-loop effect, baseline superiority, route advancement, product benefit, stable user benefit, durable
memory efficacy, runtime integration safety, agency, real emotion, subjectivity, consciousness, alive status, or Bar-2
specialness.

## Rollback Plan

Delete this task directory and artifacts, remove `EGODESKTOP-GABLATION-005` from `Tasks/TASK_BOARD.yaml`, delete the
evaluator module/CLI/tests, and regenerate route-convergence views.

## Expected Changed Files

- `EgoDesktop/src/joiRealLoopGAblationReplayEvaluator.js`
- `EgoDesktop/scripts/evaluate-joi-g-ablation-replay.js`
- `EgoDesktop/tests/joi_real_loop_g_ablation_replay_evaluator.test.js`
- `artifacts/egodesktop_joi_real_loop_g_ablation_replay_leakage_evaluator_v0/`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-replay-leakage-evaluator-v0/*`
- `docs/codex/tasks/TASK_LANE_INDEX.md`
- `Tasks/TASK_BOARD.yaml`

## Forbidden Changes

- No default runtime enablement.
- No `PROGRAM_STATE_UNIFIED.yaml` update.
- No evidence-ledger claim update.
- No EgoOperator memory, gate, approval, transport, proactive, planner, model-training, or operator-trial mutation.
- No direct creature action, user message send, schedule, memory write, gate decision, approval, or runtime registration.
- No baseline tournament, same-access verdict, route advancement, or product/readiness wording.
- No push, tag, or remote anchor from this card.

## Next Minimal Closed-Loop Action

Write failing tests for hash recomputation, leakage positive-control detection, placeholder replay blocking, and report
underclaiming; then implement the smallest evaluator module plus CLI and run it over the 004 trace rows.
