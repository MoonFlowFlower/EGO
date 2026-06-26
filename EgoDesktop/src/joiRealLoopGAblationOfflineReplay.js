const fs = require("node:fs");
const path = require("node:path");

const {
  buildJoiRealLoopTraceRow,
  hashValue,
} = require("./joiRealLoopGAblationHarness");

const CLAIM_CEILING = "egodesktop_real_loop_g_ablation_off_static_replay_heldout_replay_row_contract_only";
const OFFLINE_REPLAY_FUNCTION_ID = "off_static_replay_heldout_non_llm_adapter_v0";

function objectOrEmpty(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function text(value, fallback = "") {
  const normalized = String(value === undefined || value === null ? "" : value).trim();
  return normalized || fallback;
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function readJsonlRows(filePath) {
  return String(fs.readFileSync(filePath, "utf8"))
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

function sourceHashFor(sourceRow) {
  const row = objectOrEmpty(sourceRow);
  return text(row.row_hash, hashValue(row));
}

function buildCompleteSerializedState(sourceRow) {
  const source = objectOrEmpty(sourceRow);
  const sourceAdapter = objectOrEmpty(source.adapter_output);
  const expressionName = text(
    source.chat_turn && source.chat_turn.expression_name,
    text(sourceAdapter.expression_name, "记笔记"),
  );

  return {
    schema_version: "ego_desktop.joi_real_loop_off_static_replay_state.v0",
    claim_ceiling: CLAIM_CEILING,
    condition: "OFF_STATIC_REPLAY_HELDOUT",
    state_source: "off_static_replay_heldout_serialized_state",
    source_row_hash: sourceHashFor(source),
    reference_sequence_id: "off_static_replay_heldout_v0",
    adapter_seed: {
      schema_version: "ego_desktop.joi_real_loop_off_static_replay_adapter_seed.v0",
      expression_name: expressionName,
      adapter_status: "recomputed_off_static_replay_heldout",
      output_authority: "none",
      live2d_parameter_samples: [],
    },
    d_field_mode: "non_llm_adapter_output_only",
    llm_dependency: "excluded_from_d",
  };
}

function buildCompleteObservation(sourceRow) {
  const source = objectOrEmpty(sourceRow);
  const sourceInputs = objectOrEmpty(source.public_inputs);
  return {
    schema_version: "ego_desktop.joi_real_loop_off_static_replay_observation.v0",
    claim_ceiling: CLAIM_CEILING,
    condition: "OFF_STATIC_REPLAY_HELDOUT",
    prompt_id: text(source.prompt_id, "prompt-heldout"),
    prompt_pack: text(source.prompt_pack_hash, text(sourceInputs.prompt_pack, "prompt-pack-heldout")),
    split: "heldout",
    llm_mode: "replay_locked",
    source_row_hash: sourceHashFor(source),
    user_text_hash: text(sourceInputs.user_text_hash, ""),
    renderer_idle_excluded: true,
  };
}

function recomputeOffStaticReplayHeldoutAdapter({ serializedState, observation }) {
  const state = objectOrEmpty(serializedState);
  const observed = objectOrEmpty(observation);
  const adapterSeed = objectOrEmpty(state.adapter_seed);
  const samples = Array.isArray(adapterSeed.live2d_parameter_samples)
    ? adapterSeed.live2d_parameter_samples.map((sample) => clone(sample))
    : [];

  return {
    schema_version: "ego_desktop.joi_real_loop_off_static_replay_adapter_output.v0",
    claim_ceiling: CLAIM_CEILING,
    source: "off_static_replay_heldout_offline_recompute",
    adapter_status: text(adapterSeed.adapter_status, "recomputed_off_static_replay_heldout"),
    output_authority: "none",
    condition: "OFF_STATIC_REPLAY_HELDOUT",
    expression_name: text(adapterSeed.expression_name, ""),
    live2d_parameter_samples: samples,
    source_row_hash: text(state.source_row_hash, text(observed.source_row_hash, "")),
    d_field_mode: "non_llm_adapter_output_only",
    llm_dependency: "excluded_from_d",
    offline_replay_function_id: OFFLINE_REPLAY_FUNCTION_ID,
  };
}

function buildOffStaticReplayHeldoutRow({
  sourceRow,
  runId = "egodesktop_gablation_008_off_static_replay_heldout",
  turnId = "turn-off-static-replay-heldout-0001",
  tickId = "tick-off-static-replay-heldout-0001",
  seed = "off-static-replay-heldout-seed-0001",
} = {}) {
  const source = objectOrEmpty(sourceRow);
  const completeState = buildCompleteSerializedState(source);
  const completeObservation = buildCompleteObservation(source);
  const adapterOutput = recomputeOffStaticReplayHeldoutAdapter({
    serializedState: completeState,
    observation: completeObservation,
  });
  const replayInputs = {
    schema_version: "ego_desktop.joi_real_loop_off_static_replay_inputs.v0",
    claim_ceiling: CLAIM_CEILING,
    serialized_state_hash: hashValue(completeState),
    observation_hash: hashValue(completeObservation),
    replay_policy: "offline_non_llm_adapter_recompute_v0",
    d_field_mode: "non_llm_adapter_output_only",
    d_fields_frozen: true,
    d_fields: [
      "chat_turn.expression_name",
      "adapter_output.expression_name",
      "output_event.order_index",
    ],
    llm_dependency: "excluded_from_d",
    complete_serialized_state: completeState,
    complete_observation: completeObservation,
    offline_replay_function_id: OFFLINE_REPLAY_FUNCTION_ID,
  };
  const sourceHashes = objectOrEmpty(source.source_hashes);
  return buildJoiRealLoopTraceRow({
    runId,
    conditionId: "OFF_STATIC_REPLAY_HELDOUT",
    turnId,
    tickId,
    seed,
    sourceHashes: {
      ...sourceHashes,
      source_row_hash: sourceHashFor(source),
      offline_replay_module_hash: hashValue({
        function_id: OFFLINE_REPLAY_FUNCTION_ID,
        policy: "offline_non_llm_adapter_recompute_v0",
      }),
    },
    promptId: text(completeObservation.prompt_id, "prompt-heldout"),
    promptPackHash: text(completeObservation.prompt_pack, "prompt-pack-heldout"),
    splitId: "heldout",
    llmReplayId: "none",
    chatTurn: {
      status: "ok",
      expression_name: adapterOutput.expression_name,
      bot_text_hash: hashValue(""),
      pspc_scenario_id: "off_static_replay_heldout_non_llm_d",
    },
    creatureState: completeState,
    adapterOutput,
    publicInputs: completeObservation,
    replayInputs,
    sameAccessReproducerId: "",
    baselineSplit: "heldout",
    live2dParameterSamples: [],
    rendererIdleParams: ["idle_pose", "idle_blink", "idle_breath"],
    outputEvent: {
      order_index: 1,
      event_type: "off_static_replay_heldout_non_llm_adapter_output",
      replay_function_id: OFFLINE_REPLAY_FUNCTION_ID,
    },
  });
}

function renderBuilderReport(report) {
  return [
    "# EgoDesktop Joi Real-Loop G-ABLATION OFF_STATIC_REPLAY_HELDOUT Row",
    "",
    `- status: \`${report.status}\``,
    `- claim_ceiling: \`${CLAIM_CEILING}\``,
    `- trace_row_count: \`${report.trace_row_count}\``,
    `- source_rows_path: \`${report.source_rows_path}\``,
    `- trace_rows_path: \`${report.trace_rows_path}\``,
    `- row_hash: \`${report.row_hash}\``,
    "",
    "## Current Meaning",
    "",
    "This artifact contains one offline static replay heldout row with non-LLM D fields and a callable recompute path.",
    "It is not a baseline comparison, attribution verdict, route decision, product result, or runtime integration proof.",
    "",
  ].join("\n");
}

function writeOffStaticReplayHeldoutRows({
  sourceRowsPath,
  outDir,
  runId = "egodesktop_gablation_008_off_static_replay_heldout",
} = {}) {
  if (!sourceRowsPath) {
    throw new Error("sourceRowsPath is required");
  }
  if (!outDir) {
    throw new Error("outDir is required");
  }
  const resolvedSourceRowsPath = path.resolve(sourceRowsPath);
  const resolvedOutDir = path.resolve(outDir);
  const sourceRows = readJsonlRows(resolvedSourceRowsPath);
  if (sourceRows.length < 1) {
    throw new Error("at least one source row is required");
  }
  const row = buildOffStaticReplayHeldoutRow({
    sourceRow: sourceRows[0],
    runId,
    turnId: "turn-off-static-replay-heldout-0001",
    tickId: "tick-off-static-replay-heldout-0001",
    seed: "off-static-replay-heldout-seed-0001",
  });
  fs.mkdirSync(resolvedOutDir, { recursive: true });
  const traceRowsPath = path.join(resolvedOutDir, "trace_rows.jsonl");
  fs.writeFileSync(traceRowsPath, `${JSON.stringify(row)}\n`, "utf8");
  const report = {
    schema_version: "ego_desktop.joi_real_loop_off_static_replay_builder_report.v0",
    status: "off_static_replay_heldout_row_written",
    claim_ceiling: CLAIM_CEILING,
    producer_function: "writeOffStaticReplayHeldoutRows",
    source_rows_path: resolvedSourceRowsPath,
    trace_rows_path: traceRowsPath,
    trace_row_count: 1,
    source_row_hash: sourceHashFor(sourceRows[0]),
    row_hash: row.row_hash,
    offline_replay_function_id: OFFLINE_REPLAY_FUNCTION_ID,
    verdict_authorized: false,
  };
  fs.writeFileSync(path.join(resolvedOutDir, "builder_report.json"), JSON.stringify(report, null, 2), "utf8");
  fs.writeFileSync(path.join(resolvedOutDir, "BUILDER_REPORT.md"), renderBuilderReport(report), "utf8");
  return report;
}

module.exports = {
  CLAIM_CEILING,
  OFFLINE_REPLAY_FUNCTION_ID,
  buildOffStaticReplayHeldoutRow,
  recomputeOffStaticReplayHeldoutAdapter,
  writeOffStaticReplayHeldoutRows,
};
