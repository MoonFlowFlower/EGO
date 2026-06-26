const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const test = require("node:test");

const { buildJoiRealLoopTraceRow, hashValue } = require("../src/joiRealLoopGAblationHarness");
const {
  buildOffStaticReplayHeldoutRow,
  recomputeOffStaticReplayHeldoutAdapter,
} = require("../src/joiRealLoopGAblationOfflineReplay");
const {
  evaluateScoringPreconditions,
  evaluateTraceRows,
  parseTraceRowsJsonl,
} = require("../src/joiRealLoopGAblationReplayEvaluator");

const FORBIDDEN_BASELINE_STOP = /baseline_saturated_stop/;
const FORBIDDEN_ATTRIBUTION_PASS = new RegExp(`attribution_${"pass"}`);

function sourceCollectOnlyRow() {
  const creatureState = {
    schema_version: "ego_desktop.joi_real_loop_backend_trace_snapshot.v0",
    state_source: "ego_operator_runtime_trace_store",
    event_id: "event-006",
    trace_record_hash: "trace-record-hash",
  };
  const publicInputs = {
    user_text_hash: hashValue("heldout source prompt"),
    condition: "CURRENT_SHIM",
    prompt_pack: "prompt-pack",
    split: "heldout",
    llm_mode: "replay_locked",
  };
  return buildJoiRealLoopTraceRow({
    runId: "source-run-006",
    conditionId: "CURRENT_SHIM",
    turnId: "turn-006",
    tickId: "tick-006",
    seed: "seed-006",
    sourceHashes: { harness_hash: "harness", trace_runner_hash: "trace-runner" },
    promptId: "prompt-006",
    promptPackHash: "prompt-pack",
    splitId: "heldout",
    llmReplayId: "none",
    chatTurn: { status: "ok", expression_name: "记笔记", bot_text: "source reply" },
    creatureState,
    adapterOutput: {
      schema_version: "ego_desktop.joi_real_loop_backend_adapter_output.v0",
      source: "ego_desktop_chat_turn_result_boundary",
      adapter_status: "connected_real_backend_trace_snapshot",
      output_authority: "none",
      expression_name: "记笔记",
      backend_trace_record_hash: "trace-record-hash",
    },
    publicInputs,
    replayInputs: {
      serialized_state_hash: hashValue(creatureState),
      observation_hash: hashValue(publicInputs),
      replay_policy: "trace_runner_v0_collect_only",
    },
    outputEvent: { order: 1, timestamp_ms: 1 },
  });
}

function rehashRow(row) {
  const next = JSON.parse(JSON.stringify(row));
  next.replay_inputs_hash = hashValue(next.replay_inputs || {});
  delete next.row_hash;
  next.row_hash = hashValue(next);
  return next;
}

test("OFF_STATIC_REPLAY_HELDOUT row is replayable from serialized state plus observation", () => {
  const row = buildOffStaticReplayHeldoutRow({
    sourceRow: sourceCollectOnlyRow(),
    runId: "run-008",
    turnId: "turn-008",
    tickId: "tick-008",
    seed: "seed-008",
  });

  assert.equal(row.condition_id, "OFF_STATIC_REPLAY_HELDOUT");
  assert.equal(row.llm_replay_id, "none");
  assert.equal(row.replay_inputs.replay_policy, "offline_non_llm_adapter_recompute_v0");
  assert.equal(row.replay_inputs.d_field_mode, "non_llm_adapter_output_only");
  assert.equal(row.replay_inputs.d_fields_frozen, true);
  assert.equal(row.replay_inputs.llm_dependency, "excluded_from_d");
  assert.equal(row.replay_inputs.offline_replay_function_id, "off_static_replay_heldout_non_llm_adapter_v0");
  assert.equal(row.replay_inputs.static_replay_provenance.split_contract_status, "calibration_and_heldout_distinct");
  assert.notEqual(
    row.replay_inputs.static_replay_provenance.calibration_reference_hash,
    row.replay_inputs.static_replay_provenance.heldout_observation_source_hash,
  );
  assert.equal(row.replay_inputs.observation_shuffle_control.status, "pass");
  assert.equal(row.replay_inputs.observation_shuffle_control.adapter_output_invariant, true);
  assert.equal(row.replay_inputs.serialized_state_hash, hashValue(row.replay_inputs.complete_serialized_state));
  assert.equal(row.replay_inputs.observation_hash, hashValue(row.replay_inputs.complete_observation));
  assert.equal(row.creature_state_hash, hashValue(row.replay_inputs.complete_serialized_state));
  assert.equal(row.public_inputs_hash, hashValue(row.replay_inputs.complete_observation));

  const recomputed = recomputeOffStaticReplayHeldoutAdapter({
    serializedState: row.replay_inputs.complete_serialized_state,
    observation: row.replay_inputs.complete_observation,
    row,
  });
  assert.deepEqual(recomputed, row.adapter_output);

  const evaluatorReport = evaluateTraceRows([row], { runId: "eval-008" });
  assert.equal(evaluatorReport.status, "replay_integrity_preflight_pass_no_verdict");
  assert.equal(evaluatorReport.verdict_authorized, false);

  const precondition = evaluateScoringPreconditions([row], {
    runId: "precondition-008",
    requiredCondition: "OFF_STATIC_REPLAY_HELDOUT",
  });
  assert.equal(precondition.status, "d_field_replay_precondition_pass_no_scoring_verdict");
  assert.equal(precondition.d_field_replay_precondition_satisfied, true);
  assert.equal(precondition.scoring_authorized, false);
  assert.equal(precondition.scoring_run_authorized, false);
  assert.ok(precondition.scoring_run_authorization_blockers.includes("creature_on_pair_missing"));
  assert.ok(precondition.scoring_run_authorization_blockers.includes("baseline_battery_not_present"));
  assert.ok(precondition.scoring_run_authorization_blockers.includes("thresholds_not_frozen_for_scoring"));
  assert.equal(precondition.verdict_authorized, false);
  assert.doesNotMatch(JSON.stringify({ evaluatorReport, precondition }), FORBIDDEN_BASELINE_STOP);
  assert.doesNotMatch(JSON.stringify({ evaluatorReport, precondition }), FORBIDDEN_ATTRIBUTION_PASS);
});

test("LLM replay exception rejects D-field smuggling despite self-reported flags", () => {
  const row = buildOffStaticReplayHeldoutRow({
    sourceRow: sourceCollectOnlyRow(),
    runId: "run-008-smuggle",
    turnId: "turn-008-smuggle",
    tickId: "tick-008-smuggle",
    seed: "seed-008-smuggle",
  });
  const smuggled = rehashRow({
    ...row,
    replay_inputs: {
      ...row.replay_inputs,
      d_fields: [
        ...row.replay_inputs.d_fields,
        "chat_turn.bot_text_hash",
      ],
    },
  });

  const report = evaluateTraceRows([smuggled], { runId: "eval-smuggle" });
  assert.equal(report.status, "blocked_unreplayable_runtime_trace");
  assert.ok(report.blockers.includes("llm_or_observation_d_field_present"));
  assert.ok(report.blockers.includes("non_llm_d_field_whitelist_violation"));
});

test("builder CLI writes one heldout row and evaluator precondition passes without verdict", () => {
  const outDir = fs.mkdtempSync(path.join(os.tmpdir(), "ego-joi-heldout-replay-"));
  const sourceRowsPath = path.join(outDir, "source_trace_rows.jsonl");
  const buildOutDir = path.join(outDir, "heldout");
  const evalOutDir = path.join(outDir, "eval");
  fs.writeFileSync(sourceRowsPath, `${JSON.stringify(sourceCollectOnlyRow())}\n`, "utf8");

  const builder = spawnSync(process.execPath, [
    path.join(__dirname, "..", "scripts", "build-joi-g-ablation-off-static-replay-heldout.js"),
    "--source-rows", sourceRowsPath,
    "--out", buildOutDir,
    "--run-id", "cli-008",
  ], { encoding: "utf8" });

  assert.equal(builder.status, 0, builder.stderr || builder.stdout);
  const builderStdout = JSON.parse(builder.stdout);
  assert.equal(builderStdout.status, "off_static_replay_heldout_row_written");
  assert.equal(builderStdout.trace_row_count, 1);
  const builderReport = JSON.parse(fs.readFileSync(path.join(buildOutDir, "builder_report.json"), "utf8"));
  assert.equal(builderReport.split_contract_status, "calibration_and_heldout_distinct");
  assert.notEqual(builderReport.calibration_reference_hash, builderReport.heldout_observation_source_hash);
  assert.equal(builderReport.observation_shuffle_control_status, "pass");

  const rowsPath = path.join(buildOutDir, "trace_rows.jsonl");
  const rows = parseTraceRowsJsonl(fs.readFileSync(rowsPath, "utf8"));
  assert.equal(rows.length, 1);
  assert.equal(rows[0].condition_id, "OFF_STATIC_REPLAY_HELDOUT");

  const evaluator = spawnSync(process.execPath, [
    path.join(__dirname, "..", "scripts", "evaluate-joi-g-ablation-replay.js"),
    "--rows", rowsPath,
    "--out", evalOutDir,
    "--run-id", "cli-008-eval",
    "--require-007-scoring-precondition",
    "--required-condition", "OFF_STATIC_REPLAY_HELDOUT",
  ], { encoding: "utf8" });

  assert.equal(evaluator.status, 0, evaluator.stderr || evaluator.stdout);
  const report = JSON.parse(fs.readFileSync(path.join(evalOutDir, "evaluation_report.json"), "utf8"));
  assert.equal(report.status, "replay_integrity_preflight_pass_no_verdict");
  assert.equal(report.scoring_precondition.d_field_replay_precondition_satisfied, true);
  assert.equal(report.scoring_precondition.scoring_authorized, false);
  assert.equal(report.scoring_precondition.scoring_run_authorized, false);
  assert.equal(report.scoring_run_authorized, false);
  assert.equal(report.verdict_authorized, false);
  assert.doesNotMatch(JSON.stringify(report), FORBIDDEN_BASELINE_STOP);
  assert.doesNotMatch(JSON.stringify(report), FORBIDDEN_ATTRIBUTION_PASS);
});
