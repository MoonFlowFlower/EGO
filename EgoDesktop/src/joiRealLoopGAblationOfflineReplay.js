const fs = require("node:fs");
const path = require("node:path");

const {
  buildJoiRealLoopTraceRow,
  hashValue,
} = require("./joiRealLoopGAblationHarness");

const CLAIM_CEILING = "egodesktop_real_loop_g_ablation_off_static_replay_heldout_replay_row_contract_only";
const OFFLINE_REPLAY_FUNCTION_ID = "off_static_replay_heldout_non_llm_adapter_v0";
const NON_LLM_D_FIELDS = Object.freeze([
  "chat_turn.expression_name",
  "adapter_output.expression_name",
  "output_event.order_index",
]);

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

function buildCalibrationReference() {
  const reference = {
    schema_version: "ego_desktop.joi_real_loop_off_static_replay_calibration_reference.v0",
    claim_ceiling: CLAIM_CEILING,
    reference_pack_id: "off_static_replay_calibration_reference_v0",
    split_id: "calibration",
    reference_sequence_id: "calibration_reference_sequence_0001",
    adapter_seed: {
      schema_version: "ego_desktop.joi_real_loop_off_static_replay_adapter_seed.v0",
      expression_name: "看手机",
      adapter_status: "recomputed_off_static_replay_heldout",
      output_authority: "none",
      live2d_parameter_samples: [],
    },
  };
  return {
    ...reference,
    reference_pack_hash: hashValue(reference),
  };
}

function buildCompleteSerializedState(sourceRow) {
  const source = objectOrEmpty(sourceRow);
  const calibrationReference = buildCalibrationReference();

  return {
    schema_version: "ego_desktop.joi_real_loop_off_static_replay_state.v0",
    claim_ceiling: CLAIM_CEILING,
    condition: "OFF_STATIC_REPLAY_HELDOUT",
    state_source: "off_static_replay_heldout_serialized_state",
    source_row_hash: sourceHashFor(source),
    reference_sequence_id: "off_static_replay_heldout_v0",
    calibration_reference: calibrationReference,
    adapter_seed: calibrationReference.adapter_seed,
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
    prompt_pack_hash: text(source.prompt_pack_hash, text(sourceInputs.prompt_pack, "prompt-pack-heldout")),
    split: "heldout",
    split_id: "heldout",
    llm_mode: "replay_locked",
    source_row_hash: sourceHashFor(source),
    user_text_hash: text(sourceInputs.user_text_hash, ""),
    renderer_idle_excluded: true,
  };
}

function recomputeOffStaticReplayHeldoutAdapter({ serializedState }) {
  const state = objectOrEmpty(serializedState);
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
    source_row_hash: text(state.source_row_hash, ""),
    d_field_mode: "non_llm_adapter_output_only",
    llm_dependency: "excluded_from_d",
    offline_replay_function_id: OFFLINE_REPLAY_FUNCTION_ID,
  };
}

function buildObservationShuffleControl({ completeState, completeObservation, adapterOutput }) {
  const shuffledObservation = {
    ...completeObservation,
    prompt_id: `${text(completeObservation.prompt_id, "prompt-heldout")}__shuffle_control`,
    prompt_pack: `${text(completeObservation.prompt_pack, "prompt-pack-heldout")}__shuffle_control`,
    prompt_pack_hash: hashValue({
      source_prompt_pack_hash: completeObservation.prompt_pack_hash,
      control: "observation_content_shuffle",
    }),
    user_text_hash: hashValue({
      source_user_text_hash: completeObservation.user_text_hash,
      control: "observation_content_shuffle",
    }),
    source_row_hash: hashValue({
      source_row_hash: completeObservation.source_row_hash,
      control: "observation_content_shuffle",
    }),
  };
  const recomputed = recomputeOffStaticReplayHeldoutAdapter({
    serializedState: completeState,
    observation: shuffledObservation,
  });
  const invariant = hashValue(recomputed) === hashValue(adapterOutput);
  return {
    schema_version: "ego_desktop.joi_real_loop_off_static_replay_observation_shuffle_control.v0",
    status: invariant ? "pass" : "fail",
    adapter_output_invariant: invariant,
    producer_function: "buildObservationShuffleControl",
    original_observation_hash: hashValue(completeObservation),
    shuffled_observation_hash: hashValue(shuffledObservation),
    recomputed_adapter_output_hash: hashValue(recomputed),
    original_adapter_output_hash: hashValue(adapterOutput),
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
  const observationShuffleControl = buildObservationShuffleControl({
    completeState,
    completeObservation,
    adapterOutput,
  });
  const staticReplayProvenance = {
    schema_version: "ego_desktop.joi_real_loop_off_static_replay_provenance.v0",
    split_contract_status: "calibration_and_heldout_distinct",
    calibration_split_id: "calibration",
    heldout_split_id: "heldout",
    calibration_reference_hash: hashValue(completeState.calibration_reference),
    calibration_reference_pack_hash: completeState.calibration_reference.reference_pack_hash,
    heldout_observation_source_hash: sourceHashFor(source),
    heldout_prompt_pack_hash: completeObservation.prompt_pack_hash,
    input_blind_contract: "adapter_output_recomputed_from_calibration_reference_state_not_heldout_observation_content",
    observation_shuffle_control_hash: hashValue(observationShuffleControl),
  };
  const replayInputs = {
    schema_version: "ego_desktop.joi_real_loop_off_static_replay_inputs.v0",
    claim_ceiling: CLAIM_CEILING,
    serialized_state_hash: hashValue(completeState),
    observation_hash: hashValue(completeObservation),
    replay_policy: "offline_non_llm_adapter_recompute_v0",
    d_field_mode: "non_llm_adapter_output_only",
    d_fields_frozen: true,
    d_fields: [...NON_LLM_D_FIELDS],
    d_field_provenance: {
      schema_version: "ego_desktop.joi_real_loop_non_llm_d_field_provenance.v0",
      mode: "offline_adapter_whitelist_v0",
      allowed_fields: [...NON_LLM_D_FIELDS],
      excluded_sources: ["llm_text", "complete_observation", "public_inputs", "renderer_idle_params"],
      producer_function: "recomputeOffStaticReplayHeldoutAdapter",
    },
    llm_dependency: "excluded_from_d",
    complete_serialized_state: completeState,
    complete_observation: completeObservation,
    static_replay_provenance: staticReplayProvenance,
    observation_shuffle_control: observationShuffleControl,
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
      calibration_reference_hash: staticReplayProvenance.calibration_reference_hash,
      heldout_observation_source_hash: staticReplayProvenance.heldout_observation_source_hash,
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
    `- split_contract_status: \`${report.split_contract_status}\``,
    `- calibration_reference_hash: \`${report.calibration_reference_hash}\``,
    `- heldout_observation_source_hash: \`${report.heldout_observation_source_hash}\``,
    `- observation_shuffle_control_status: \`${report.observation_shuffle_control_status}\``,
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
    split_contract_status: row.replay_inputs.static_replay_provenance.split_contract_status,
    calibration_reference_hash: row.replay_inputs.static_replay_provenance.calibration_reference_hash,
    calibration_reference_pack_hash: row.replay_inputs.static_replay_provenance.calibration_reference_pack_hash,
    heldout_observation_source_hash: row.replay_inputs.static_replay_provenance.heldout_observation_source_hash,
    heldout_prompt_pack_hash: row.replay_inputs.static_replay_provenance.heldout_prompt_pack_hash,
    observation_shuffle_control_status: row.replay_inputs.observation_shuffle_control.status,
    observation_shuffle_control_hash: row.replay_inputs.static_replay_provenance.observation_shuffle_control_hash,
    verdict_authorized: false,
  };
  fs.writeFileSync(path.join(resolvedOutDir, "builder_report.json"), JSON.stringify(report, null, 2), "utf8");
  fs.writeFileSync(path.join(resolvedOutDir, "BUILDER_REPORT.md"), renderBuilderReport(report), "utf8");
  return report;
}

module.exports = {
  CLAIM_CEILING,
  NON_LLM_D_FIELDS,
  OFFLINE_REPLAY_FUNCTION_ID,
  buildOffStaticReplayHeldoutRow,
  recomputeOffStaticReplayHeldoutAdapter,
  writeOffStaticReplayHeldoutRows,
};
