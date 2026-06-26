# EgoDesktop Joi Real-Loop G-ABLATION Replay Precondition v0 Spec

- task_id: `EGODESKTOP-GABLATION-007`
- status: `active`
- created_at: `2026-06-26`
- owner: `Codex`
- layer: `engineering implementation / executable replay-scoring precondition gate`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `explicit_cli_only`
- real_trigger_evidence: `none_yet_for_this_slice`
- claim_ceiling: `egodesktop_real_loop_g_ablation_replay_precondition_contract_only`
- auto_remote_anchor: `forbidden`

## Problem Definition

`EGODESKTOP-GABLATION-006A` cleared the source-limited review blockers for the narrow claim that 006 rows remain
`schema_valid_collect_only_snapshot`. The next valid slice must stop surface repair and convert the 007 replay/D-field
precondition from a Markdown reminder into an executable abort gate before any scoring, baseline, or attribution run can
execute.

## Bounded Audit

- real objective: ensure any >=007 scoring request aborts unless non-LLM `D` fields are frozen, complete state and
  observation are serialized, and an offline replay callable can recompute the adapter output.
- strongest baseline explanation: current 006 rows are still collect-only backend snapshots; no replay or baseline signal
  exists.
- strongest invalidity risk: allowing a scoring/baseline command to proceed because the precondition exists only in docs.
- falsifier for this framing: a CLI or evaluator path can request scoring with current 006 rows and exit success.
- insufficient evidence: a `.md` file saying scoring is blocked without a callable guard that fails under current rows.
- task type: executable evidence-hygiene gate only, not mechanism validation.
- leakage check: current 006 leakage pass is low-signal because the row lacks CREATURE_ON privileged/stateful fields;
  leakage verdict work is deferred until CREATURE_ON rows exist.
- trace/replay-id check: `trace_id` and `replay_id` distinction is deferred until any LLM-modulated `D` field appears;
  before then, non-LLM `D` must exclude bot text and LLM semantic quality.
- stop condition: any need to run a baseline tournament, emit attribution labels, or update program state/evidence ledger.

## Mainline Target

The target is the existing local evaluator/CLI:

- `EgoDesktop/src/joiRealLoopGAblationReplayEvaluator.js`
- `EgoDesktop/scripts/evaluate-joi-g-ablation-replay.js`

No renderer, main-process, backend runtime, EgoOperator memory, gate, approval, transport, proactive, planner, or model
training behavior may be enabled or changed by this slice.

## Enabled-State Requirement

The precondition gate is active only when an explicit evaluator/CLI request asks for 007 scoring precondition enforcement.
Normal collect-only evaluation remains available for underclaiming reports.

## Real-Trigger Evidence Requirement

Acceptance requires the CLI to abort with a non-zero exit when invoked over current collect-only rows with:

```powershell
node EgoDesktop\scripts\evaluate-joi-g-ablation-replay.js `
  --rows artifacts\egodesktop_joi_real_loop_g_ablation_backend_trace_snapshot_v0\trace\trace_rows.jsonl `
  --out artifacts\egodesktop_joi_real_loop_g_ablation_replay_precondition_v0 `
  --require-007-scoring-precondition `
  --required-condition OFF_STATIC_REPLAY_HELDOUT
```

The report must include `blocked_d_field_replay_precondition_not_satisfied`, `scoring_authorized=false`, and blockers for
missing frozen `D`, missing complete state/observation serialization, unavailable offline replay callable, collect-only
policy, and condition mismatch where applicable.

## Hypothesis

If the precondition is executable rather than textual, then current 006 rows cannot accidentally pass into scoring or
baseline code. The next implementation slice can then focus on producing a single replayable non-LLM `D` row instead of
continuing review-surface repair.

## Strongest Baseline

`OFF_STATIC_REPLAY_HELDOUT` remains the first decisive baseline condition for the future minimal slice. This task only
guards admission to that slice; it does not score the baseline.

## Ablation Requirement

No ablation run is authorized. The only contrast is current collect-only rows versus the executable precondition gate.

## Trace / Replay Requirement

The gate must require:

- `d_field_mode: non_llm_adapter_output_only`;
- frozen non-LLM `D` fields;
- complete serialized state payload;
- complete observation payload;
- non-collect replay policy;
- a callable offline replay function supplied by the future scorer/evaluator path.

Missing any required item must block scoring before baseline or attribution logic is reached.

## Computed-Evidence Provenance Gate

Reports must record:

- producer function;
- run id;
- input artifact path;
- row count;
- required condition;
- blockers;
- source hash for the evaluator;
- `scoring_authorized=false` unless all executable preconditions pass.

## Acceptance Gate

- Task card and mutation scope exist before production implementation.
- Tests are written first and fail before implementation.
- Current collect-only rows are blocked by `evaluateScoringPreconditions`.
- CLI with `--require-007-scoring-precondition` exits non-zero on current collect-only rows and writes a blocked report.
- No baseline score, attribution verdict, route advancement, or positive mechanism claim is emitted.
- `npm test` from `EgoDesktop` passes.
- `python scripts\codex\verify_repo.py --mode fast` passes.
- Scoped closeout reports no unsafe dirty paths.

## Claim Ceiling

`egodesktop_real_loop_g_ablation_replay_precondition_contract_only`.

This can prove only that a local executable guard blocks >=007 scoring requests until replay/D-field prerequisites are
present. It cannot prove replay readiness, baseline superiority, attribution, route advancement, product benefit, stable
user benefit, durable memory efficacy, runtime integration safety, agency, real emotion, subjectivity, consciousness,
alive status, or Bar-2 specialness.

## Rollback Plan

Delete this task directory and artifacts, remove `EGODESKTOP-GABLATION-007` from `Tasks/TASK_BOARD.yaml`, revert the
precondition helper/CLI/test changes, and regenerate route-convergence views.

## Expected Changed Files

- `EgoDesktop/src/joiRealLoopGAblationReplayEvaluator.js`
- `EgoDesktop/scripts/evaluate-joi-g-ablation-replay.js`
- `EgoDesktop/tests/joi_real_loop_g_ablation_replay_evaluator.test.js`
- `artifacts/egodesktop_joi_real_loop_g_ablation_replay_precondition_v0/`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-replay-precondition-v0/*`
- `docs/codex/tasks/TASK_LANE_INDEX.md`
- `Tasks/TASK_BOARD.yaml`

## Forbidden Changes

- No default runtime enablement.
- No `PROGRAM_STATE_UNIFIED.yaml` update.
- No evidence-ledger claim update.
- No EgoOperator memory, gate, approval, transport, proactive, planner, model-training, or operator-trial mutation.
- No direct creature action, user message send, schedule, memory write, gate decision, approval, or runtime registration.
- No baseline tournament, same-access verdict, attribution verdict, route advancement, product/readiness wording, push,
  tag, or remote anchor.

## Next Minimal Closed-Loop Action

After this gate is executable, the next slice may produce one `OFF_STATIC_REPLAY_HELDOUT` non-LLM `D` replay row with
complete serialized state plus observation and a callable offline adapter recompute function. Do not add scoring or
baseline verdict labels until that row exists and the precondition passes.
