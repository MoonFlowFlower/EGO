# EgoDesktop Joi Real-Loop G-ABLATION Captured Calibration Reference v0 Spec

- task_id: `EGODESKTOP-GABLATION-009`
- status: `card_reviewed_no_blocking_findings__implementation_not_started`
- created_at: `2026-06-27`
- owner: `Codex`
- layer: `engineering implementation / calibration provenance and replay hygiene`
- main_chain_status: `not_connected_to_default_runtime`
- enabled_status: `explicit_cli_only`
- real_trigger_evidence: `none_yet_for_this_slice`
- claim_ceiling: `egodesktop_real_loop_g_ablation_captured_calibration_reference_contract_only`
- auto_remote_anchor: `forbidden`

## Problem Definition

`EGODESKTOP-GABLATION-008` produced one replayable `OFF_STATIC_REPLAY_HELDOUT` non-LLM `D` row, but its adapter seed
still comes from a schema-labeled `synthetic_reference`. That was acceptable for the narrow 008 precondition row only.
Before any paired `CREATURE_ON` row, threshold freeze, scoring run, or baseline comparison, the static replay reference
must be grounded in a captured or fitted calibration source that is distinct from the heldout observation.

This slice opens that boundary. It does not score, compare, emit `CREATURE_ON`, or advance a route verdict.

## Current Readback

- Current repo branch at card drafting: `main`.
- Current repo `HEAD` at card drafting: `4fffb768f980c70796f52b11e640ae6ed1d18edd`.
- `EGODESKTOP-GABLATION-008` row hash: `bd120552670850025ab531a8dc8b9a064c50ba30277115451a0d86c84b38de04`.
- Existing 006 source trace artifact has exactly one `CURRENT_SHIM` / `heldout` row:
  `artifacts/egodesktop_joi_real_loop_g_ablation_backend_trace_snapshot_v0/trace/trace_rows.jsonl`.
- No current artifact provides a separate `calibration` split trace row. Therefore 009 must capture or consume a real
  calibration-source artifact before it can replace the synthetic reference. It must not relabel the heldout row as
  calibration and must not derive the adapter seed from heldout observation content.

## Bounded Audit

- real objective: replace the hand-authored synthetic calibration source with a captured/fitted calibration reference
  that a future heldout/static replay row can consume without split leakage.
- strongest baseline explanation: even a captured calibration source only improves provenance; it is still a static replay
  baseline component and cannot be positive route evidence.
- strongest invalidity risk: using the heldout row's own output, prompt, observation, run, or prompt pack to fit the
  calibration seed and then claiming input-blind replay.
- falsifier for this framing: no separate calibration source can be captured or serialized, or the rebuilt heldout row
  still reports `synthetic_reference`.
- insufficient evidence: a renamed constant, a hardcoded calibration JSON, a calibration hash with no source row, a
  calibration row that overlaps heldout prompts/turns/runs, or a reference that cannot be traced back to real backend
  trace-row fields.
- task type: evidence-hygiene and replay-provenance implementation only.
- leakage check: leakage remains a schema/authority hygiene gate only until `CREATURE_ON` privileged/stateful rows exist.
- trace/replay-id check: `llm_replay_id` remains `none` while `D` excludes LLM text; do not invent an LLM replay id from
  trace ids or hashes.
- stop condition: any need to emit `CREATURE_ON`, compare candidate vs baseline, freeze scoring thresholds, output
  `baseline_saturated_stop`, or update program state/evidence ledger.

## Mainline Target

The target is still explicit local artifact tooling plus the existing replay evaluator:

- a pre-capture split partition manifest that freezes calibration and heldout prompt partitions before any capture;
- a calibration-reference builder that consumes real calibration split trace rows;
- the 008 offline replay builder updated to consume that calibration reference instead of a static synthetic object;
- a CLI path that writes a captured/fitted calibration reference artifact and a rebuilt `OFF_STATIC_REPLAY_HELDOUT` row;
- tests that prove the calibration source is distinct from the heldout observation and is actually consumed by the
  offline adapter seed.

No renderer/main-process/backend default runtime path is enabled or changed by this slice.

## Enabled-State Requirement

All 009 behavior is CLI-only and artifact-only. Default EgoDesktop runtime behavior remains unchanged unless explicit
`JOI_REAL_LOOP_*` experiment flags and the calibration-builder CLI are used.

## Real-Trigger Evidence Requirement

Acceptance requires:

1. A split partition manifest frozen before capture. It must record:
   - `producer_function`;
   - `partition_protocol_hash`;
   - calibration prompt pack id/hash;
   - heldout prompt pack id/hash;
   - calibration prompt ids/user-text hashes;
   - heldout prompt ids/user-text hashes;
   - disjointness assertions for prompt ids, user-text hashes, source row hashes, turn ids, trace record hashes, and
     capture run ids;
   - an overlap-positive-control case that intentionally reuses at least one heldout prompt/hash and must be rejected.
2. A calibration source artifact built from a real trace row with `split_id: calibration` or from a fitted artifact that
   embeds and hashes its real calibration trace-row inputs.
3. The calibration source row must be produced through the existing 006 tap surface:
   - explicit `JOI_REAL_LOOP_*` flags;
   - real `window.egoDesktop.sendChatTurn(...)` / default chat-turn result boundary;
   - existing `trace_rows.jsonl` writer/sink;
   - no second chat-turn implementation path;
   - default runtime no-op when flags are absent;
   - closeout scope covering the capture artifacts.
4. The calibration reference records:
   - `calibration_reference_kind: captured_backend_trace_reference` or `fitted_from_captured_calibration_trace`;
   - `calibration_reference_source: fixed_output_schedule_from_calibration_trace`;
   - source trace path;
   - source row hash;
   - source prompt id / prompt-pack hash;
   - source adapter output hash;
   - adapter seed fields consumed by offline replay;
   - explicit list of captured source fields that are provenance-only and forbidden from heldout `D` recompute;
   - producer function and source hashes.
5. The rebuilt `OFF_STATIC_REPLAY_HELDOUT` row records:
   - `split_contract_status: captured_calibration_reference_distinct_from_heldout_observation`;
   - no `synthetic_reference` kind or `synthetic_calibration_reference_v0` seed source;
   - calibration source hash distinct from heldout observation source hash;
   - `partition_protocol_hash`;
   - partition disjointness status `pass`;
   - adapter output echoing the calibration reference hash and seed source.
6. The existing evaluator precondition still reports `d_field_replay_precondition_satisfied=true`,
   `scoring_authorized=false`, `scoring_run_authorized=false`, and `verdict_authorized=false`.

## Hypothesis

If the static replay adapter seed is derived from a captured/fitted calibration source rather than a hand-authored
constant, then the single heldout baseline row can preserve the 008 replayability property while removing the synthetic
calibration caveat. This only strengthens provenance; it is not a comparison or mechanism result.

## Strongest Baseline

`OFF_STATIC_REPLAY_HELDOUT` remains the decisive static replay floor for future contrast work. 009 only prepares that
floor with a non-synthetic calibration source.

## Ablation Requirement

No ablation or condition battery is authorized. `CREATURE_ON`, `SAME_ACCESS_REPRODUCER_BATTERY`, and scoring thresholds
are future slices.

## Trace / Replay Requirement

The 009 row must preserve all 008 replay fields and additionally prove:

- calibration source is serialized or reconstructable from a captured calibration artifact;
- calibration reference hash is computed from captured/fitted calibration data, not a literal constant;
- adapter seed carries `calibration_reference_hash` and non-synthetic `seed_source`;
- heldout `D` recompute consumes the captured fixed output schedule only, not the captured calibration `creature_state`,
  `state_digest`, `viability_state`, `subject_context_hash`, `llm_meta_hash`, bot text, prompt text, or heldout
  observation content;
- heldout observation remains separate and public-input-only;
- observation-shuffle control is rerun against the captured calibration reference;
- calibration-state shuffle/control proves non-seed captured state fields are provenance-only and do not affect adapter
  output;
- captured calibration controls are still below any `CREATURE_ON` or decisive same-access baseline verdict.

## Computed-Evidence Provenance Gate

Reports must record:

- producer function;
- split partition manifest path/hash;
- partition disjointness status;
- calibration input artifact(s);
- calibration source row hash(es);
- heldout source row hash;
- row count;
- source hashes;
- recompute function id;
- precondition status;
- explicit `scoring_run_authorized=false`.

## Acceptance Gate

- Task card and mutation scope exist before production implementation.
- Tests are written first and fail before implementation.
- Calibration reference cannot be built from a heldout-only artifact without an explicit blocked result.
- The builder consumes a calibration reference artifact path; it no longer silently creates a synthetic reference for 009.
- Split overlap positive control must fire by reusing a heldout prompt/hash/row as calibration input.
- Synthetic fallback positive control must fire when a synthetic reference is supplied or implied.
- `calibration_reference_kind=synthetic_reference` positive control must fire.
- Captured calibration shuffle control must show heldout adapter output is invariant to heldout-observation shuffle and to
  non-seed calibration-state mutation.
- The rebuilt heldout row passes offline recompute and evaluator precondition but emits no baseline/attribution verdict.
- `npm test` from `EgoDesktop` passes.
- `python scripts\codex\verify_repo.py --mode fast` passes.
- Scoped closeout reports no unsafe dirty paths.

## Claim Ceiling

`egodesktop_real_loop_g_ablation_captured_calibration_reference_contract_only`.

This can prove only that the static replay heldout row consumes a captured/fitted calibration reference instead of a
synthetic constant. It cannot prove baseline saturation, candidate failure, attribution, route advancement, product
benefit, stable user benefit, durable memory efficacy, runtime integration safety, agency, real emotion, subjectivity,
consciousness, alive status, or Bar-2 specialness.

## Rollback Plan

Delete this task directory and artifacts, remove `EGODESKTOP-GABLATION-009` from `Tasks/TASK_BOARD.yaml`, revert any
calibration-reference builder/module/script/tests, restore the 008 offline replay builder behavior, and regenerate
route-convergence views.

## Expected Changed Files

- `EgoDesktop/src/joiRealLoopGAblationCalibrationReference.js`
- `EgoDesktop/src/joiRealLoopGAblationOfflineReplay.js`
- `EgoDesktop/scripts/build-joi-g-ablation-calibration-reference.js`
- `EgoDesktop/scripts/build-joi-g-ablation-off-static-replay-heldout.js`
- `EgoDesktop/tests/joi_real_loop_g_ablation_calibration_reference.test.js`
- `EgoDesktop/tests/joi_real_loop_g_ablation_off_static_replay.test.js`
- `artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/partition/SPLIT_PARTITION_MANIFEST.json`
- `artifacts/egodesktop_joi_real_loop_g_ablation_calibration_reference_v0/`
- `docs/codex/tasks/egodesktop-joi-real-loop-g-ablation-calibration-reference-v0/*`
- `docs/codex/tasks/TASK_LANE_INDEX.md`
- `Tasks/TASK_BOARD.yaml`

## Forbidden Changes

- No default runtime enablement.
- No `PROGRAM_STATE_UNIFIED.yaml` update.
- No evidence-ledger claim update.
- No EgoOperator memory, gate, approval, transport, proactive, planner, model-training, or operator-trial mutation.
- No direct creature action, user message send, schedule, memory write, gate decision, approval, or runtime registration.
- No `CREATURE_ON` row.
- No baseline score, threshold freeze, `baseline_saturated_stop`, attribution, route advancement, product/readiness
  wording, push, tag, or remote anchor.
- No relabeling heldout rows as calibration.
- No synthetic calibration fallback in the 009 acceptance artifact.
- No shared prompt id, user-text hash, source row hash, turn id, trace record hash, or capture run id between calibration
  and heldout partitions.
- No use of captured calibration state beyond fixed output schedule fields for heldout `D` recompute.

## Claude Card Review Repair

Desktop Claude returned `BLOCKING_FINDINGS` source-limited for the first 009 card draft. The card-level repairs now
incorporated are:

1. Freeze a pre-capture calibration/heldout split partition manifest, require disjointness assertions, and require an
   overlap positive control.
2. Define input-blind replay as fixed output schedule replay, with captured calibration state fields marked
   provenance-only and forbidden from heldout `D` recompute.
3. Require calibration rows to be produced by the existing 006 tap / real sendChatTurn path under explicit flags, with no
   second chat-turn path or default runtime change.
4. Add must-fire positive controls for synthetic fallback, split overlap, synthetic kind, and captured-calibration
   shuffle/invariance.

Non-blocking caveat carried forward: without `CREATURE_ON` output, captured calibration remains a `CURRENT_SHIM`-level
weak baseline component. Decisive saturation handling still depends on a separate same-access reproducer battery slice.

Desktop Claude then returned `NO_BLOCKING_FINDINGS` source-limited for the repaired card text. The source-limited
review accepted that B-009-1..4 are closed in the card text and that the card is blocker-free for implementation, while
not claiming repo/artifact execution proof.

## Next Minimal Closed-Loop Action

Implement only the tests-first calibration-reference builder and rebuilt `OFF_STATIC_REPLAY_HELDOUT` row that consumes
it. Do not score, compare, emit `CREATURE_ON`, update program state, update evidence ledger, push, tag, or remote-anchor
in 009.
