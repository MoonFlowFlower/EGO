# EgoDesktop Joi Real-Loop G-ABLATION OFF_STATIC_REPLAY_HELDOUT v0 Spec

- task_id: `EGODESKTOP-GABLATION-008`
- status: `active`
- created_at: `2026-06-26`
- owner: `Codex`
- layer: `engineering implementation / single-condition replayable non-LLM D row`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `explicit_cli_only`
- real_trigger_evidence: `none_yet_for_this_slice`
- claim_ceiling: `egodesktop_real_loop_g_ablation_off_static_replay_heldout_replay_row_contract_only`
- auto_remote_anchor: `forbidden`

## Problem Definition

`EGODESKTOP-GABLATION-007` made the replay/D-field precondition executable and correctly blocks current 006
collect-only rows. The next valid slice is not a baseline verdict. It is a single `OFF_STATIC_REPLAY_HELDOUT`
non-LLM `D` row with complete serialized state plus observation and a callable offline adapter recompute function, so the
007 precondition can pass for exactly one baseline-condition row without scoring attribution.

## Bounded Audit

- real objective: create one replayable row for the decisive static replay condition, below any baseline-saturation
  verdict.
- strongest baseline explanation: the row is itself a static replay baseline condition; it cannot be positive route
  evidence.
- strongest invalidity risk: fabricating an LLM replay id or treating precondition pass as a baseline pass.
- falsifier for this framing: the row cannot be recomputed offline from serialized state plus observation, or the CLI emits
  a baseline/attribution verdict.
- insufficient evidence: a row with only hashes/digests, no complete serialized payload, no callable recompute, or a
  `trace_runner_v0_collect_only` replay policy.
- task type: replayability/evidence-hygiene implementation only, not mechanism validation.
- leakage check: leakage pass on this row remains schema/authority hygiene only; CREATURE_ON privileged-field leakage is
  still deferred.
- trace/replay-id check: `llm_replay_id` remains `none` because `D` explicitly excludes LLM output. Do not invent a replay
  id from trace hashes.
- stop condition: any need to compare candidate vs baseline, emit `baseline_saturated_stop`, or update program
  state/evidence ledger.

## Mainline Target

The target is an explicit local artifact builder plus the existing replay evaluator:

- `EgoDesktop/src/joiRealLoopGAblationOfflineReplay.js`
- `EgoDesktop/scripts/build-joi-g-ablation-off-static-replay-heldout.js`
- `EgoDesktop/src/joiRealLoopGAblationReplayEvaluator.js`

No renderer/main-process/backend runtime path is enabled or changed by this slice.

## Enabled-State Requirement

The row builder is CLI-only and artifact-only. Default EgoDesktop runtime behavior remains unchanged.

## Real-Trigger Evidence Requirement

Acceptance requires:

1. Build one row from the current 006 trace artifact into:
   `artifacts/egodesktop_joi_real_loop_g_ablation_off_static_replay_heldout_v0/trace/trace_rows.jsonl`
2. Run the existing evaluator CLI with:
   `--require-007-scoring-precondition --required-condition OFF_STATIC_REPLAY_HELDOUT`
3. The precondition subreport must show `d_field_replay_precondition_satisfied=true`,
   `scoring_authorized=false`, and `scoring_run_authorized=false`, while the overall report still has
   `verdict_authorized=false` and no baseline/attribution verdict.

## Hypothesis

If `D` is restricted to deterministic non-LLM adapter output, then one static replay heldout row can be reconstructed
from complete serialized state plus public observation by a local offline callable, while preserving the claim ceiling.

## Strongest Baseline

`OFF_STATIC_REPLAY_HELDOUT` is the strongest static replay floor for the future minimal contrast. This slice only proves
the floor row is replayable; it does not compare it against `CREATURE_ON`.

## Ablation Requirement

No ablation or condition battery is authorized. Only one `OFF_STATIC_REPLAY_HELDOUT` row is produced.

## Trace / Replay Requirement

The row must include:

- `condition_id: OFF_STATIC_REPLAY_HELDOUT`;
- `llm_replay_id: none`;
- `replay_policy: offline_non_llm_adapter_recompute_v0`;
- `d_field_mode: non_llm_adapter_output_only`;
- `d_fields_frozen: true`;
- `llm_dependency: excluded_from_d`;
- complete serialized state object;
- complete observation object;
- explicit `synthetic_reference` calibration provenance until a captured/fitted calibration source exists;
- true hash for the heldout prompt-pack descriptor plus an explicit `single_smoke_prompt_not_full_pack` scope;
- observation-shuffle control labeled as a constructive regression guard, not final input-blind evidence;
- `offline_replay_function_id: off_static_replay_heldout_non_llm_adapter_v0`;
- recomputed adapter output hash equal to the row's adapter output hash.

## Computed-Evidence Provenance Gate

Reports must record:

- producer function;
- source 006 row hash/input artifact;
- row count;
- source hashes;
- recompute function id;
- precondition status.

## Acceptance Gate

- Task card and mutation scope exist before production implementation.
- Tests are written first and fail before implementation.
- The builder produces one `OFF_STATIC_REPLAY_HELDOUT` row from the current 006 row.
- The row contains complete serialized state and observation, not only hashes.
- Offline recompute from serialized state plus observation reproduces adapter output.
- Evaluator precondition passes for this row but still emits no baseline/attribution verdict.
- `npm test` from `EgoDesktop` passes.
- `python scripts\codex\verify_repo.py --mode fast` passes.
- Scoped closeout reports no unsafe dirty paths.

## Claim Ceiling

`egodesktop_real_loop_g_ablation_off_static_replay_heldout_replay_row_contract_only`.

This can prove only that one static replay heldout non-LLM `D` row is replayable through a callable local recompute path.
It cannot prove baseline saturation, candidate failure, attribution, route advancement, product benefit, stable user
benefit, durable memory efficacy, runtime integration safety, agency, real emotion, subjectivity, consciousness, alive
status, or Bar-2 specialness.

## Rollback Plan

Delete this task directory and artifacts, remove `EGODESKTOP-GABLATION-008` from `Tasks/TASK_BOARD.yaml`, delete the
offline replay module/script/tests, revert the evaluator precondition extension, and regenerate route-convergence views.

## Expected Changed Files

- `EgoDesktop/src/joiRealLoopGAblationOfflineReplay.js`
- `EgoDesktop/src/joiRealLoopGAblationReplayEvaluator.js`
- `EgoDesktop/scripts/build-joi-g-ablation-off-static-replay-heldout.js`
- `EgoDesktop/scripts/evaluate-joi-g-ablation-replay.js`
- `EgoDesktop/tests/joi_real_loop_g_ablation_off_static_replay.test.js`
- `EgoDesktop/tests/joi_real_loop_g_ablation_replay_evaluator.test.js`
- `artifacts/egodesktop_joi_real_loop_g_ablation_off_static_replay_heldout_v0/`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-off-static-replay-heldout-v0/*`
- `docs/codex/tasks/TASK_LANE_INDEX.md`
- `Tasks/TASK_BOARD.yaml`

## Forbidden Changes

- No default runtime enablement.
- No `PROGRAM_STATE_UNIFIED.yaml` update.
- No evidence-ledger claim update.
- No EgoOperator memory, gate, approval, transport, proactive, planner, model-training, or operator-trial mutation.
- No direct creature action, user message send, schedule, memory write, gate decision, approval, or runtime registration.
- No `baseline_saturated_stop`, attribution, route advancement, product/readiness wording, push, tag, or remote anchor.

## Next Minimal Closed-Loop Action

After this row is replayable, the next separate slice must replace the synthetic calibration reference with a
captured/fitted calibration source before building the paired `CREATURE_ON` non-LLM `D` replay row or a minimal contrast
card. Do not score or compare in this task.
