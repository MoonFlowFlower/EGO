const fs = require("node:fs");
const path = require("node:path");

const { hashValue } = require("./joiRealLoopGAblationHarness");

const CLAIM_CEILING = "egodesktop_real_loop_g_ablation_captured_calibration_reference_contract_only";
const PARTITION_PROTOCOL_ID = "egodesktop_gablation_009_calibration_heldout_disjoint_v0";
const FIXED_OUTPUT_SOURCE = "fixed_output_schedule_from_calibration_trace";
const CAPTURED_REFERENCE_KIND = "captured_backend_trace_reference";
const PREDECLARED_SELECTION_POLICY = "single_predeclared_prompt_exact_match_no_post_hoc_selection";

const CONTENT_PARTITION_DIMENSIONS = Object.freeze([
  "prompt_ids",
  "user_text_hashes",
]);

const PROVENANCE_DISTINCTNESS_DIMENSIONS = Object.freeze([
  "source_row_hashes",
  "trace_record_hashes",
  "capture_run_ids",
]);

const INFORMATIONAL_PROVENANCE_DIMENSIONS = Object.freeze([
  "turn_ids",
]);

const PROVENANCE_ONLY_FORBIDDEN_FROM_HELDOUT_D = Object.freeze([
  "creature_state.state_digest",
  "creature_state.viability_state",
  "creature_state.subject_context_hash",
  "creature_state.llm_meta_hash",
  "chat_turn.bot_text_hash",
  "public_inputs.user_text_hash",
  "heldout_observation_content",
]);

function objectOrEmpty(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function text(value, fallback = "") {
  const normalized = String(value === undefined || value === null ? "" : value).trim();
  return normalized || fallback;
}

function uniqueSorted(values) {
  return [...new Set(values.filter(Boolean).map((value) => String(value)))]
    .sort((left, right) => left.localeCompare(right));
}

function readJsonlRows(filePath) {
  return String(fs.readFileSync(filePath, "utf8"))
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function writeJson(filePath, payload) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, JSON.stringify(payload, null, 2), "utf8");
}

function cloneWithoutPromptPackHash(value) {
  const clone = JSON.parse(JSON.stringify(objectOrEmpty(value)));
  delete clone.prompt_pack_hash;
  return clone;
}

function hashPredeclaredCalibrationPromptPack(pack) {
  return hashValue(cloneWithoutPromptPackHash(pack));
}

function buildPredeclaredCalibrationPromptPack({
  runId = "egodesktop_gablation_009_predeclared_calibration_prompt_pack",
  promptText,
  promptId = "",
  promptPackId = "egodesktop_gablation_009_predeclared_single_calibration_prompt_pack_v0",
  heldoutRowsPath = "",
  producerFunction = "buildPredeclaredCalibrationPromptPack",
} = {}) {
  const userText = text(promptText, "");
  if (!userText) {
    throw new Error("promptText is required");
  }
  const userTextHash = hashValue(userText);
  const prompt = {
    prompt_id: text(promptId, `prompt_${userTextHash.slice(0, 12)}`),
    user_text_hash: userTextHash,
    prompt_text_hash: userTextHash,
    split_id: "calibration",
  };
  const packBase = {
    schema_version: "ego_desktop.joi_real_loop_g_ablation_predeclared_calibration_prompt_pack.v0",
    claim_ceiling: CLAIM_CEILING,
    producer_function: producerFunction,
    run_id: String(runId || ""),
    prompt_pack_id: String(promptPackId || ""),
    split_id: "calibration",
    selection_policy: PREDECLARED_SELECTION_POLICY,
    content_partition_dimensions: [...CONTENT_PARTITION_DIMENSIONS],
    provenance_distinctness_dimensions: [...PROVENANCE_DISTINCTNESS_DIMENSIONS],
    informational_provenance_dimensions: [...INFORMATIONAL_PROVENANCE_DIMENSIONS],
    heldout_rows_path: String(heldoutRowsPath || ""),
    prompts: [prompt],
    prompt_count: 1,
  };
  return {
    ...packBase,
    prompt_pack_hash: hashValue(packBase),
  };
}

function writePredeclaredCalibrationPromptPack({
  outPath,
  promptText,
  promptId = "",
  runId,
  promptPackId,
  heldoutRowsPath = "",
} = {}) {
  if (!outPath) {
    throw new Error("outPath is required");
  }
  const pack = buildPredeclaredCalibrationPromptPack({
    runId,
    promptText,
    promptId,
    promptPackId,
    heldoutRowsPath,
    producerFunction: "writePredeclaredCalibrationPromptPack",
  });
  writeJson(path.resolve(outPath), pack);
  return pack;
}

function normalizePredeclaredPromptPack(value) {
  if (!value) {
    return null;
  }
  const pack = objectOrEmpty(value);
  if (pack.schema_version !== "ego_desktop.joi_real_loop_g_ablation_predeclared_calibration_prompt_pack.v0") {
    throw new Error("predeclared calibration prompt pack schema is required");
  }
  if (pack.split_id !== "calibration") {
    throw new Error("predeclared calibration prompt pack must target calibration split");
  }
  if (pack.selection_policy !== PREDECLARED_SELECTION_POLICY) {
    throw new Error("predeclared calibration prompt pack must forbid post hoc selection");
  }
  if (pack.prompt_pack_hash !== hashPredeclaredCalibrationPromptPack(pack)) {
    throw new Error("predeclared calibration prompt pack hash mismatch");
  }
  const prompts = Array.isArray(pack.prompts) ? pack.prompts : [];
  if (prompts.length !== 1) {
    throw new Error("009 calibration prompt pack must contain exactly one predeclared prompt");
  }
  for (const prompt of prompts) {
    const safePrompt = objectOrEmpty(prompt);
    if (!text(safePrompt.prompt_id, "") || !text(safePrompt.user_text_hash, "")) {
      throw new Error("predeclared calibration prompt requires prompt_id and user_text_hash");
    }
  }
  return pack;
}

function assertRowsMatchPredeclaredPromptPack(rows, predeclaredPromptPack) {
  const pack = normalizePredeclaredPromptPack(predeclaredPromptPack);
  if (!pack) {
    return {
      predeclaredPromptPack: null,
      selection_policy_status: "predeclared_prompt_pack_not_provided",
      post_hoc_selection_status: "not_checked",
    };
  }
  const safeRows = Array.isArray(rows) ? rows : [];
  if (safeRows.length !== pack.prompts.length) {
    throw new Error("predeclared calibration prompt pack requires exactly one captured matching row");
  }
  const prompt = objectOrEmpty(pack.prompts[0]);
  const row = objectOrEmpty(safeRows[0]);
  const publicInputs = objectOrEmpty(row.public_inputs);
  if (text(row.prompt_id, "") !== text(prompt.prompt_id, "")) {
    throw new Error("captured calibration row prompt_id does not match predeclared prompt");
  }
  if (text(publicInputs.user_text_hash, "") !== text(prompt.user_text_hash, "")) {
    throw new Error("captured calibration row user_text_hash does not match predeclared prompt");
  }
  return {
    predeclaredPromptPack: pack,
    selection_policy_status: "deterministic_predeclared_single_prompt_consumed",
    post_hoc_selection_status: "absent",
  };
}

function sourceHashFor(row) {
  const safe = objectOrEmpty(row);
  return text(safe.row_hash, hashValue(safe));
}

function traceRecordHashFor(row) {
  const safe = objectOrEmpty(row);
  const creatureState = objectOrEmpty(safe.creature_state);
  const adapterOutput = objectOrEmpty(safe.adapter_output);
  return text(creatureState.trace_record_hash, text(adapterOutput.backend_trace_record_hash, ""));
}

function rowSplit(row) {
  const safe = objectOrEmpty(row);
  return text(safe.split_id, text(objectOrEmpty(safe.public_inputs).split, ""));
}

function dimensionValues(rows, dimension) {
  return uniqueSorted(rows.map((row) => {
    const safe = objectOrEmpty(row);
    const publicInputs = objectOrEmpty(safe.public_inputs);
    if (dimension === "prompt_ids") return safe.prompt_id;
    if (dimension === "user_text_hashes") return publicInputs.user_text_hash;
    if (dimension === "source_row_hashes") return sourceHashFor(safe);
    if (dimension === "turn_ids") return safe.turn_id;
    if (dimension === "trace_record_hashes") return traceRecordHashFor(safe);
    if (dimension === "capture_run_ids") return safe.run_id;
    return "";
  }));
}

function overlap(leftValues, rightValues) {
  const right = new Set(rightValues);
  return leftValues.filter((value) => right.has(value));
}

function buildDisjointness(calibrationRows, heldoutRows, dimensions) {
  const result = {};
  for (const dimension of dimensions) {
    const calibration = dimensionValues(calibrationRows, dimension);
    const heldout = dimensionValues(heldoutRows, dimension);
    const shared = overlap(calibration, heldout);
    result[dimension] = {
      status: shared.length ? "fail" : "pass",
      calibration,
      heldout,
      overlap: shared,
    };
  }
  return result;
}

function disjointnessStatus(disjointness) {
  return Object.values(disjointness).every((item) => item.status === "pass") ? "pass" : "fail";
}

function overlapPositiveControlStatus(calibrationRows, heldoutRows) {
  if (!heldoutRows.length) {
    return "fail";
  }
  const injected = [...calibrationRows, heldoutRows[0]];
  return disjointnessStatus(buildDisjointness(
    injected,
    heldoutRows,
    CONTENT_PARTITION_DIMENSIONS,
  )) === "fail" ? "pass" : "fail";
}

function buildSplitPartitionManifest({
  calibrationRows,
  heldoutRows,
  predeclaredPromptPack = null,
  producerFunction = "buildSplitPartitionManifest",
} = {}) {
  const safeCalibrationRows = Array.isArray(calibrationRows) ? calibrationRows : [];
  const safeHeldoutRows = Array.isArray(heldoutRows) ? heldoutRows : [];
  if (!safeCalibrationRows.length) {
    throw new Error("at least one calibration row is required");
  }
  if (!safeHeldoutRows.length) {
    throw new Error("at least one heldout row is required");
  }

  const predeclared = assertRowsMatchPredeclaredPromptPack(safeCalibrationRows, predeclaredPromptPack);
  const contentDisjointness = buildDisjointness(
    safeCalibrationRows,
    safeHeldoutRows,
    CONTENT_PARTITION_DIMENSIONS,
  );
  const provenanceDistinctness = buildDisjointness(
    safeCalibrationRows,
    safeHeldoutRows,
    PROVENANCE_DISTINCTNESS_DIMENSIONS,
  );
  const turnIdProvenance = buildDisjointness(
    safeCalibrationRows,
    safeHeldoutRows,
    INFORMATIONAL_PROVENANCE_DIMENSIONS,
  );
  const contentDisjointnessStatus = disjointnessStatus(contentDisjointness);
  const provenanceDistinctnessStatus = disjointnessStatus(provenanceDistinctness);
  const partitionDisjointnessStatus =
    contentDisjointnessStatus === "pass" && provenanceDistinctnessStatus === "pass" ? "pass" : "fail";
  const disjointness = {
    ...contentDisjointness,
    ...provenanceDistinctness,
  };
  const manifestBase = {
    schema_version: "ego_desktop.joi_real_loop_g_ablation_split_partition_manifest.v0",
    claim_ceiling: CLAIM_CEILING,
    producer_function: producerFunction,
    partition_protocol_id: PARTITION_PROTOCOL_ID,
    content_partition_dimensions: [...CONTENT_PARTITION_DIMENSIONS],
    provenance_distinctness_dimensions: [...PROVENANCE_DISTINCTNESS_DIMENSIONS],
    informational_provenance_dimensions: [...INFORMATIONAL_PROVENANCE_DIMENSIONS],
    partition_dimensions: [
      ...CONTENT_PARTITION_DIMENSIONS,
      ...PROVENANCE_DISTINCTNESS_DIMENSIONS,
    ],
    predeclared_calibration_prompt_pack_hash: predeclared.predeclaredPromptPack
      ? predeclared.predeclaredPromptPack.prompt_pack_hash
      : "",
    predeclared_selection_policy: predeclared.predeclaredPromptPack
      ? predeclared.predeclaredPromptPack.selection_policy
      : "",
    selection_policy_status: predeclared.selection_policy_status,
    post_hoc_selection_status: predeclared.post_hoc_selection_status,
    calibration_prompt_pack_hashes: uniqueSorted(safeCalibrationRows.map((row) => row.prompt_pack_hash)),
    heldout_prompt_pack_hashes: uniqueSorted(safeHeldoutRows.map((row) => row.prompt_pack_hash)),
    calibration_source_row_hashes: dimensionValues(safeCalibrationRows, "source_row_hashes"),
    heldout_source_row_hashes: dimensionValues(safeHeldoutRows, "source_row_hashes"),
    calibration_capture_run_ids: dimensionValues(safeCalibrationRows, "capture_run_ids"),
    heldout_capture_run_ids: dimensionValues(safeHeldoutRows, "capture_run_ids"),
    content_disjointness: contentDisjointness,
    provenance_distinctness: provenanceDistinctness,
    turn_id_provenance: turnIdProvenance,
    disjointness,
    content_disjointness_status: contentDisjointnessStatus,
    provenance_distinctness_status: provenanceDistinctnessStatus,
    turn_id_provenance_status: "informational_only_not_content_disjointness_gate",
    partition_disjointness_status: partitionDisjointnessStatus,
    overlap_positive_control_status: overlapPositiveControlStatus(safeCalibrationRows, safeHeldoutRows),
  };
  const manifest = {
    ...manifestBase,
    partition_protocol_hash: hashValue({
      partition_protocol_id: PARTITION_PROTOCOL_ID,
      content_partition_dimensions: CONTENT_PARTITION_DIMENSIONS,
      provenance_distinctness_dimensions: PROVENANCE_DISTINCTNESS_DIMENSIONS,
      predeclared_calibration_prompt_pack_hash: manifestBase.predeclared_calibration_prompt_pack_hash,
      selection_policy_status: manifestBase.selection_policy_status,
      disjointness,
      content_disjointness: contentDisjointness,
      provenance_distinctness: provenanceDistinctness,
      calibration_prompt_pack_hashes: manifestBase.calibration_prompt_pack_hashes,
      heldout_prompt_pack_hashes: manifestBase.heldout_prompt_pack_hashes,
    }),
  };
  if (partitionDisjointnessStatus !== "pass") {
    throw new Error(`split partition overlap: ${JSON.stringify(disjointness)}`);
  }
  if (manifest.overlap_positive_control_status !== "pass") {
    throw new Error("split overlap positive control did not fire");
  }
  return manifest;
}

function rejectSyntheticCalibrationInput(row) {
  const safe = objectOrEmpty(row);
  if (
    text(safe.calibration_reference_kind, "") === "synthetic_reference"
    || text(safe.adapter_seed && safe.adapter_seed.calibration_reference_kind, "") === "synthetic_reference"
    || /calibration_reference/i.test(text(safe.schema_version, "")) && text(safe.calibration_reference_kind, "") !== CAPTURED_REFERENCE_KIND
  ) {
    throw new Error("synthetic calibration reference is not allowed");
  }
}

function assertCalibrationRows(rows) {
  for (const row of rows) {
    rejectSyntheticCalibrationInput(row);
    if (rowSplit(row) !== "calibration") {
      throw new Error("calibration split row is required");
    }
  }
}

function buildAdapterSeedFromCalibrationRow(row) {
  const safe = objectOrEmpty(row);
  const adapterOutput = objectOrEmpty(safe.adapter_output);
  return {
    schema_version: "ego_desktop.joi_real_loop_off_static_replay_adapter_seed.v0",
    expression_name: text(adapterOutput.expression_name, text(objectOrEmpty(safe.chat_turn).expression_name, "")),
    adapter_status: "recomputed_off_static_replay_heldout",
    output_authority: "none",
    live2d_parameter_samples: Array.isArray(safe.live2d_parameter_samples)
      ? safe.live2d_parameter_samples.map((sample) => JSON.parse(JSON.stringify(sample)))
      : [],
    seed_source: CAPTURED_REFERENCE_KIND,
    calibration_reference_kind: CAPTURED_REFERENCE_KIND,
  };
}

function buildCapturedCalibrationReference({
  calibrationRows,
  heldoutRows,
  predeclaredPromptPack = null,
  sourceTracePath = "",
  producerFunction = "buildCapturedCalibrationReference",
} = {}) {
  const safeCalibrationRows = Array.isArray(calibrationRows) ? calibrationRows : [];
  const safeHeldoutRows = Array.isArray(heldoutRows) ? heldoutRows : [];
  assertCalibrationRows(safeCalibrationRows);
  const predeclared = assertRowsMatchPredeclaredPromptPack(safeCalibrationRows, predeclaredPromptPack);
  const manifest = buildSplitPartitionManifest({
    calibrationRows: safeCalibrationRows,
    heldoutRows: safeHeldoutRows,
    predeclaredPromptPack,
    producerFunction: "buildCapturedCalibrationReference.partition",
  });
  const sourceRow = safeCalibrationRows[0];
  const adapterOutput = objectOrEmpty(sourceRow.adapter_output);
  const creatureState = objectOrEmpty(sourceRow.creature_state);
  const baseReference = {
    schema_version: "ego_desktop.joi_real_loop_captured_calibration_reference.v0",
    claim_ceiling: CLAIM_CEILING,
    producer_function: producerFunction,
    calibration_reference_kind: CAPTURED_REFERENCE_KIND,
    calibration_reference_source: FIXED_OUTPUT_SOURCE,
    reference_pack_id: "egodesktop_gablation_009_captured_calibration_reference_v0",
    split_id: "calibration",
    source_trace_path: String(sourceTracePath || ""),
    source_row_hash: sourceHashFor(sourceRow),
    source_trace_record_hash: traceRecordHashFor(sourceRow),
    source_prompt_id: text(sourceRow.prompt_id, ""),
    source_prompt_pack_hash: text(sourceRow.prompt_pack_hash, ""),
    source_adapter_output_hash: hashValue(adapterOutput),
    source_expression_name: text(adapterOutput.expression_name, ""),
    source_hashes: objectOrEmpty(sourceRow.source_hashes),
    predeclared_calibration_prompt_pack_hash: predeclared.predeclaredPromptPack
      ? predeclared.predeclaredPromptPack.prompt_pack_hash
      : "",
    selection_policy_status: manifest.selection_policy_status,
    post_hoc_selection_status: manifest.post_hoc_selection_status,
    partition_protocol_hash: manifest.partition_protocol_hash,
    partition_disjointness_status: manifest.partition_disjointness_status,
    content_disjointness_status: manifest.content_disjointness_status,
    provenance_distinctness_status: manifest.provenance_distinctness_status,
    turn_id_provenance_status: manifest.turn_id_provenance_status,
    split_partition_manifest_hash: hashValue(manifest),
    adapter_seed: buildAdapterSeedFromCalibrationRow(sourceRow),
    provenance_only_forbidden_from_heldout_d: [...PROVENANCE_ONLY_FORBIDDEN_FROM_HELDOUT_D],
    captured_source_field_hashes: {
      state_digest_hash: hashValue(objectOrEmpty(creatureState.state_digest)),
      viability_state_hash: hashValue(objectOrEmpty(creatureState.viability_state)),
      subject_context_hash: text(creatureState.subject_context_hash, ""),
      llm_meta_hash: text(creatureState.llm_meta_hash, ""),
      bot_text_hash: text(objectOrEmpty(sourceRow.chat_turn).bot_text_hash, ""),
      public_user_text_hash: text(objectOrEmpty(sourceRow.public_inputs).user_text_hash, ""),
    },
  };
  return {
    ...baseReference,
    reference_pack_hash: hashValue(baseReference),
  };
}

function loadCalibrationReference(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function renderCalibrationReferenceReport(report) {
  return [
    "# EgoDesktop Joi Real-Loop G-ABLATION Captured Calibration Reference",
    "",
    `- status: \`${report.status}\``,
    `- claim_ceiling: \`${CLAIM_CEILING}\``,
    `- calibration_reference_path: \`${report.calibration_reference_path}\``,
    `- split_partition_manifest_path: \`${report.split_partition_manifest_path}\``,
    `- calibration_reference_kind: \`${report.calibration_reference_kind}\``,
    `- calibration_reference_source: \`${report.calibration_reference_source}\``,
    `- predeclared_calibration_prompt_pack_hash: \`${report.predeclared_calibration_prompt_pack_hash || ""}\``,
    `- selection_policy_status: \`${report.selection_policy_status || ""}\``,
    `- post_hoc_selection_status: \`${report.post_hoc_selection_status || ""}\``,
    `- content_disjointness_status: \`${report.content_disjointness_status || ""}\``,
    `- provenance_distinctness_status: \`${report.provenance_distinctness_status || ""}\``,
    `- turn_id_provenance_status: \`${report.turn_id_provenance_status || ""}\``,
    `- partition_disjointness_status: \`${report.partition_disjointness_status}\``,
    `- overlap_positive_control_status: \`${report.overlap_positive_control_status}\``,
    `- synthetic_fallback_positive_control_status: \`${report.synthetic_fallback_positive_control_status}\``,
    "",
    "## Current Meaning",
    "",
    "This artifact records a captured calibration reference for a later offline static replay heldout row. It is not a",
    "baseline comparison, attribution verdict, route decision, product result, or runtime integration proof.",
    "",
  ].join("\n");
}

function writeCalibrationReference({
  calibrationRowsPath,
  heldoutRowsPath,
  predeclaredPromptPackPath = "",
  outDir,
  runId = "egodesktop_gablation_009_captured_calibration_reference",
} = {}) {
  if (!calibrationRowsPath) {
    throw new Error("calibrationRowsPath is required");
  }
  if (!heldoutRowsPath) {
    throw new Error("heldoutRowsPath is required");
  }
  if (!outDir) {
    throw new Error("outDir is required");
  }
  const resolvedCalibrationRowsPath = path.resolve(calibrationRowsPath);
  const resolvedHeldoutRowsPath = path.resolve(heldoutRowsPath);
  const resolvedOutDir = path.resolve(outDir);
  const calibrationRows = readJsonlRows(resolvedCalibrationRowsPath);
  const heldoutRows = readJsonlRows(resolvedHeldoutRowsPath);
  const resolvedPredeclaredPromptPackPath = predeclaredPromptPackPath
    ? path.resolve(predeclaredPromptPackPath)
    : "";
  const predeclaredPromptPack = resolvedPredeclaredPromptPackPath
    ? normalizePredeclaredPromptPack(loadCalibrationReference(resolvedPredeclaredPromptPackPath))
    : null;
  const manifest = buildSplitPartitionManifest({
    calibrationRows,
    heldoutRows,
    predeclaredPromptPack,
    producerFunction: "writeCalibrationReference.partition",
  });
  const reference = buildCapturedCalibrationReference({
    calibrationRows,
    heldoutRows,
    predeclaredPromptPack,
    sourceTracePath: resolvedCalibrationRowsPath,
    producerFunction: "writeCalibrationReference",
  });
  const partitionPath = path.join(resolvedOutDir, "partition", "SPLIT_PARTITION_MANIFEST.json");
  const referencePath = path.join(resolvedOutDir, "calibration_reference.json");
  writeJson(partitionPath, manifest);
  writeJson(referencePath, reference);

  let syntheticFallbackPositiveControlStatus = "fail";
  try {
    buildCapturedCalibrationReference({
      calibrationRows: [{ schema_version: "synthetic", calibration_reference_kind: "synthetic_reference" }],
      heldoutRows,
      sourceTracePath: "synthetic-positive-control",
    });
  } catch (_error) {
    syntheticFallbackPositiveControlStatus = "pass";
  }

  const report = {
    schema_version: "ego_desktop.joi_real_loop_captured_calibration_reference_builder_report.v0",
    status: "captured_calibration_reference_written",
    claim_ceiling: CLAIM_CEILING,
    producer_function: "writeCalibrationReference",
    run_id: String(runId || ""),
    calibration_rows_path: resolvedCalibrationRowsPath,
    heldout_rows_path: resolvedHeldoutRowsPath,
    predeclared_calibration_prompt_pack_path: resolvedPredeclaredPromptPackPath,
    predeclared_calibration_prompt_pack_hash: manifest.predeclared_calibration_prompt_pack_hash,
    calibration_reference_path: referencePath,
    split_partition_manifest_path: partitionPath,
    calibration_reference_hash: hashValue(reference),
    split_partition_manifest_hash: hashValue(manifest),
    calibration_source_row_hash: reference.source_row_hash,
    heldout_source_row_hashes: manifest.heldout_source_row_hashes,
    calibration_reference_kind: reference.calibration_reference_kind,
    calibration_reference_source: reference.calibration_reference_source,
    partition_protocol_hash: manifest.partition_protocol_hash,
    partition_disjointness_status: manifest.partition_disjointness_status,
    content_disjointness_status: manifest.content_disjointness_status,
    provenance_distinctness_status: manifest.provenance_distinctness_status,
    turn_id_provenance_status: manifest.turn_id_provenance_status,
    selection_policy_status: manifest.selection_policy_status,
    post_hoc_selection_status: manifest.post_hoc_selection_status,
    overlap_positive_control_status: manifest.overlap_positive_control_status,
    synthetic_fallback_positive_control_status: syntheticFallbackPositiveControlStatus,
    scoring_run_authorized: false,
    verdict_authorized: false,
  };
  writeJson(path.join(resolvedOutDir, "calibration_reference_report.json"), report);
  fs.writeFileSync(
    path.join(resolvedOutDir, "CALIBRATION_REFERENCE_REPORT.md"),
    renderCalibrationReferenceReport(report),
    "utf8",
  );
  return report;
}

module.exports = {
  CAPTURED_REFERENCE_KIND,
  CLAIM_CEILING,
  CONTENT_PARTITION_DIMENSIONS,
  FIXED_OUTPUT_SOURCE,
  INFORMATIONAL_PROVENANCE_DIMENSIONS,
  PREDECLARED_SELECTION_POLICY,
  PROVENANCE_DISTINCTNESS_DIMENSIONS,
  PROVENANCE_ONLY_FORBIDDEN_FROM_HELDOUT_D,
  buildCapturedCalibrationReference,
  buildPredeclaredCalibrationPromptPack,
  buildSplitPartitionManifest,
  hashPredeclaredCalibrationPromptPack,
  loadCalibrationReference,
  normalizePredeclaredPromptPack,
  readJsonlRows,
  sourceHashFor,
  traceRecordHashFor,
  writeCalibrationReference,
  writePredeclaredCalibrationPromptPack,
};
