const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const test = require("node:test");

const { buildJoiRealLoopTraceRow, hashValue } = require("../src/joiRealLoopGAblationHarness");
const {
  buildCapturedCalibrationReference,
  buildPredeclaredCalibrationPromptPack,
  buildSplitPartitionManifest,
} = require("../src/joiRealLoopGAblationCalibrationReference");
const {
  buildOffStaticReplayHeldoutRow,
  recomputeOffStaticReplayHeldoutAdapter,
} = require("../src/joiRealLoopGAblationOfflineReplay");
const {
  evaluateScoringPreconditions,
  parseTraceRowsJsonl,
} = require("../src/joiRealLoopGAblationReplayEvaluator");

const SHA256_HEX = /^[a-f0-9]{64}$/;

function backendTraceRow({
  split,
  runId,
  turnId,
  promptId,
  promptText,
  expressionName,
  traceRecordHash,
}) {
  const creatureState = {
    schema_version: "ego_desktop.joi_real_loop_backend_trace_snapshot.v0",
    source: "ego_operator_desktop_turn_trace_store",
    state_source: "ego_operator_runtime_trace_store",
    event_id: `evt-${turnId}`,
    trace_record_hash: traceRecordHash,
    trace_path_hash: hashValue({ traceRecordHash, split }),
    state_digest: {
      mode: split,
      focus: promptId,
      drives: { curiosity: split === "calibration" ? 0.41 : 0.17 },
      revision_counter: split === "calibration" ? 4 : 5,
      cycle_count: split === "calibration" ? 6 : 7,
    },
    viability_state: { score: split === "calibration" ? 0.21 : 0.11 },
    subject_context_hash: hashValue({ subject: split, promptId }),
    llm_meta_hash: hashValue({ llm: split, promptId }),
    llm_replay_contract: "absent",
    side_effect_boundary: {
      side_effects_executed: false,
      memory_written: false,
      tools_used: false,
      messages_sent: false,
      files_written: false,
      network_used: false,
    },
    claim_ceiling: "egodesktop_real_loop_g_ablation_backend_trace_snapshot_contract_only",
  };
  const adapterOutput = {
    schema_version: "ego_desktop.joi_real_loop_backend_adapter_output.v0",
    source: "ego_desktop_chat_turn_result_boundary",
    adapter_status: "connected_real_backend_trace_snapshot",
    output_authority: "none",
    expression_name: expressionName,
    chat_turn_status: "ok",
    backend_status: "ok",
    backend_reason: "",
    backend_trace_record_hash: traceRecordHash,
    backend_trace_state_source: "ego_operator_runtime_trace_store",
    llm_trace_id: hashValue({ llm: turnId }),
    side_effect_boundary: {
      side_effects_executed: false,
      memory_written: false,
      tools_used: false,
      messages_sent: false,
      files_written: false,
      network_used: false,
    },
    claim_ceiling: "egodesktop_real_loop_g_ablation_trace_runner_contract_only",
  };
  const publicInputs = {
    user_text_hash: hashValue(promptText),
    condition: "CURRENT_SHIM",
    prompt_pack: `${split}-prompt-pack`,
    split,
    llm_mode: "replay_locked",
    desktop_session_context_hash: hashValue({ session: split }),
    desktop_recovery_context_hash: hashValue({ recovery: split }),
  };
  return buildJoiRealLoopTraceRow({
    runId,
    conditionId: "CURRENT_SHIM",
    turnId,
    tickId: `tick-${turnId}`,
    seed: `seed-${turnId}`,
    sourceHashes: { harness_hash: "harness", trace_runner_hash: "trace-runner" },
    promptId,
    promptPackHash: `${split}-prompt-pack-hash`,
    splitId: split,
    llmReplayId: "none",
    chatTurn: { status: "ok", expression_name: expressionName, bot_text: `${split} reply` },
    creatureState,
    adapterOutput,
    publicInputs,
    replayInputs: {
      serialized_state_hash: hashValue(creatureState),
      observation_hash: hashValue(publicInputs),
      replay_policy: "trace_runner_v0_collect_only",
    },
    outputEvent: { order: 1, timestamp_ms: 1 },
  });
}

function calibrationRow() {
  return backendTraceRow({
    split: "calibration",
    runId: "run-calibration",
    turnId: "turn-calibration",
    promptId: "prompt-calibration",
    promptText: "calibration prompt",
    expressionName: "看手机",
    traceRecordHash: "a".repeat(64),
  });
}

function predeclaredPackForCalibrationRow(row = calibrationRow(), promptText = "calibration prompt") {
  return buildPredeclaredCalibrationPromptPack({
    runId: "test-predeclared-calibration-pack",
    promptText,
    promptId: row.prompt_id,
    heldoutRowsPath: "heldout_trace_rows.jsonl",
  });
}

function heldoutRow() {
  return backendTraceRow({
    split: "heldout",
    runId: "run-heldout",
    turnId: "turn-heldout",
    promptId: "prompt-heldout",
    promptText: "heldout prompt",
    expressionName: "记笔记",
    traceRecordHash: "b".repeat(64),
  });
}

test("split partition manifest freezes disjoint calibration and heldout sources with overlap positive control", () => {
  const sourceCalibrationRow = calibrationRow();
  const manifest = buildSplitPartitionManifest({
    calibrationRows: [sourceCalibrationRow],
    heldoutRows: [heldoutRow()],
    predeclaredPromptPack: predeclaredPackForCalibrationRow(sourceCalibrationRow),
    producerFunction: "test_build_partition_manifest",
  });

  assert.equal(manifest.partition_disjointness_status, "pass");
  assert.equal(manifest.content_disjointness_status, "pass");
  assert.equal(manifest.provenance_distinctness_status, "pass");
  assert.equal(manifest.turn_id_provenance_status, "informational_only_not_content_disjointness_gate");
  assert.equal(manifest.selection_policy_status, "deterministic_predeclared_single_prompt_consumed");
  assert.equal(manifest.post_hoc_selection_status, "absent");
  assert.equal(manifest.overlap_positive_control_status, "pass");
  assert.match(manifest.partition_protocol_hash, SHA256_HEX);
  assert.deepEqual(manifest.content_partition_dimensions, ["prompt_ids", "user_text_hashes"]);
  assert.deepEqual(manifest.informational_provenance_dimensions, ["turn_ids"]);
  assert.equal(manifest.content_disjointness.prompt_ids.status, "pass");
  assert.equal(manifest.content_disjointness.user_text_hashes.status, "pass");
  assert.equal(manifest.provenance_distinctness.source_row_hashes.status, "pass");
  assert.equal(manifest.provenance_distinctness.trace_record_hashes.status, "pass");
  assert.equal(manifest.provenance_distinctness.capture_run_ids.status, "pass");
  assert.ok(!Object.hasOwn(manifest.disjointness, "turn_ids"));
  assert.equal(manifest.turn_id_provenance.turn_ids.status, "pass");

  assert.throws(
    () => buildSplitPartitionManifest({
      calibrationRows: [heldoutRow()],
      heldoutRows: [heldoutRow()],
      predeclaredPromptPack: predeclaredPackForCalibrationRow(heldoutRow(), "heldout prompt"),
      producerFunction: "test_overlap_control",
    }),
    /split partition overlap/,
  );
  assert.throws(
    () => buildSplitPartitionManifest({
      calibrationRows: [calibrationRow(), heldoutRow()],
      heldoutRows: [heldoutRow()],
      predeclaredPromptPack: predeclaredPackForCalibrationRow(calibrationRow()),
      producerFunction: "test_post_hoc_selection_reject",
    }),
    /requires exactly one captured matching row/,
  );
});

test("captured calibration reference rejects heldout-only or synthetic calibration sources", () => {
  assert.throws(
    () => buildCapturedCalibrationReference({
      calibrationRows: [heldoutRow()],
      heldoutRows: [heldoutRow()],
      sourceTracePath: "heldout-only.jsonl",
    }),
    /calibration split/,
  );
  assert.throws(
    () => buildCapturedCalibrationReference({
      calibrationRows: [{
        schema_version: "ego_desktop.joi_real_loop_off_static_replay_calibration_reference.v0",
        calibration_reference_kind: "synthetic_reference",
      }],
      heldoutRows: [heldoutRow()],
      sourceTracePath: "synthetic.json",
    }),
    /synthetic calibration reference/,
  );
});

test("captured calibration reference feeds input-blind heldout replay without synthetic fallback", () => {
  const sourceCalibrationRow = calibrationRow();
  const sourceHeldoutRow = heldoutRow();
  const reference = buildCapturedCalibrationReference({
    calibrationRows: [sourceCalibrationRow],
    heldoutRows: [sourceHeldoutRow],
    predeclaredPromptPack: predeclaredPackForCalibrationRow(sourceCalibrationRow),
    sourceTracePath: "calibration-trace_rows.jsonl",
  });

  assert.equal(reference.calibration_reference_kind, "captured_backend_trace_reference");
  assert.equal(reference.calibration_reference_source, "fixed_output_schedule_from_calibration_trace");
  assert.equal(reference.partition_disjointness_status, "pass");
  assert.equal(reference.content_disjointness_status, "pass");
  assert.equal(reference.provenance_distinctness_status, "pass");
  assert.equal(reference.turn_id_provenance_status, "informational_only_not_content_disjointness_gate");
  assert.equal(reference.selection_policy_status, "deterministic_predeclared_single_prompt_consumed");
  assert.equal(reference.post_hoc_selection_status, "absent");
  assert.equal(reference.adapter_seed.seed_source, "captured_backend_trace_reference");
  assert.equal(reference.adapter_seed.expression_name, "看手机");
  assert.notEqual(reference.source_row_hash, sourceHeldoutRow.row_hash);
  assert.ok(reference.provenance_only_forbidden_from_heldout_d.includes("creature_state.state_digest"));

  const row = buildOffStaticReplayHeldoutRow({
    sourceRow: sourceHeldoutRow,
    calibrationReference: reference,
    runId: "run-009",
    turnId: "turn-009",
    tickId: "tick-009",
    seed: "seed-009",
  });

  assert.equal(
    row.replay_inputs.static_replay_provenance.split_contract_status,
    "captured_calibration_reference_distinct_from_heldout_observation",
  );
  assert.equal(row.replay_inputs.static_replay_provenance.calibration_reference_kind, "captured_backend_trace_reference");
  assert.equal(row.replay_inputs.static_replay_provenance.calibration_reference_source, "fixed_output_schedule_from_calibration_trace");
  assert.equal(row.replay_inputs.static_replay_provenance.partition_disjointness_status, "pass");
  assert.equal(row.replay_inputs.complete_serialized_state.adapter_seed.seed_source, "captured_backend_trace_reference");
  assert.notEqual(row.replay_inputs.static_replay_provenance.calibration_reference_hash, sourceHeldoutRow.row_hash);
  assert.equal(row.adapter_output.adapter_seed_source, "captured_backend_trace_reference");
  assert.equal(row.replay_inputs.observation_shuffle_control.status, "pass");
  assert.equal(row.replay_inputs.calibration_state_shuffle_control.status, "pass");
  assert.equal(row.replay_inputs.calibration_state_shuffle_control.adapter_output_invariant, true);
  assert.ok(
    row.replay_inputs.d_field_provenance.excluded_sources.includes("captured_calibration_state"),
  );

  const recomputed = recomputeOffStaticReplayHeldoutAdapter({
    serializedState: row.replay_inputs.complete_serialized_state,
    observation: row.replay_inputs.complete_observation,
    row,
  });
  assert.deepEqual(recomputed, row.adapter_output);

  const precondition = evaluateScoringPreconditions([row], {
    runId: "precondition-009",
    requiredCondition: "OFF_STATIC_REPLAY_HELDOUT",
  });
  assert.equal(precondition.d_field_replay_precondition_satisfied, true);
  assert.equal(precondition.scoring_run_authorized, false);
  assert.equal(precondition.verdict_authorized, false);
});

test("calibration-reference CLI and heldout builder CLI produce captured-reference replay row", () => {
  const outDir = fs.mkdtempSync(path.join(os.tmpdir(), "ego-joi-calibration-reference-"));
  const calibrationRowsPath = path.join(outDir, "calibration_trace_rows.jsonl");
  const heldoutRowsPath = path.join(outDir, "heldout_trace_rows.jsonl");
  const calibrationOutDir = path.join(outDir, "calibration-reference");
  const heldoutOutDir = path.join(outDir, "heldout");

  fs.writeFileSync(calibrationRowsPath, `${JSON.stringify(calibrationRow())}\n`, "utf8");
  fs.writeFileSync(heldoutRowsPath, `${JSON.stringify(heldoutRow())}\n`, "utf8");
  const predeclaredPromptPackPath = path.join(outDir, "predeclared_calibration_prompt_pack.json");
  fs.writeFileSync(
    predeclaredPromptPackPath,
    JSON.stringify(predeclaredPackForCalibrationRow(calibrationRow()), null, 2),
    "utf8",
  );

  const calibrationBuilder = spawnSync(process.execPath, [
    path.join(__dirname, "..", "scripts", "build-joi-g-ablation-calibration-reference.js"),
    "--calibration-rows", calibrationRowsPath,
    "--heldout-rows", heldoutRowsPath,
    "--predeclared-calibration-prompt-pack", predeclaredPromptPackPath,
    "--out", calibrationOutDir,
    "--run-id", "cli-009-calibration",
  ], { encoding: "utf8" });
  assert.equal(calibrationBuilder.status, 0, calibrationBuilder.stderr || calibrationBuilder.stdout);
  const calibrationStdout = JSON.parse(calibrationBuilder.stdout);
  assert.equal(calibrationStdout.status, "captured_calibration_reference_written");
  assert.equal(calibrationStdout.selection_policy_status, "deterministic_predeclared_single_prompt_consumed");
  assert.equal(calibrationStdout.post_hoc_selection_status, "absent");
  assert.equal(calibrationStdout.partition_disjointness_status, "pass");

  const heldoutBuilder = spawnSync(process.execPath, [
    path.join(__dirname, "..", "scripts", "build-joi-g-ablation-off-static-replay-heldout.js"),
    "--source-rows", heldoutRowsPath,
    "--calibration-reference", calibrationStdout.calibration_reference_path,
    "--out", heldoutOutDir,
    "--run-id", "cli-009-heldout",
  ], { encoding: "utf8" });
  assert.equal(heldoutBuilder.status, 0, heldoutBuilder.stderr || heldoutBuilder.stdout);

  const builderReport = JSON.parse(fs.readFileSync(path.join(heldoutOutDir, "builder_report.json"), "utf8"));
  assert.equal(
    builderReport.split_contract_status,
    "captured_calibration_reference_distinct_from_heldout_observation",
  );
  assert.equal(builderReport.calibration_reference_kind, "captured_backend_trace_reference");
  assert.equal(builderReport.partition_disjointness_status, "pass");
  assert.equal(builderReport.scoring_run_authorized, false);
  assert.equal(builderReport.verdict_authorized, false);

  const rows = parseTraceRowsJsonl(fs.readFileSync(path.join(heldoutOutDir, "trace_rows.jsonl"), "utf8"));
  assert.equal(rows.length, 1);
  assert.equal(rows[0].replay_inputs.static_replay_provenance.calibration_reference_kind, "captured_backend_trace_reference");
});
