const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");

const { hashValue } = require("./joiRealLoopGAblationHarness");

const CLAIM_CEILING = "egodesktop_real_loop_g_ablation_replay_leakage_evaluator_contract_only";
const SCORING_PRECONDITION_CLAIM_CEILING =
  "egodesktop_real_loop_g_ablation_replay_precondition_contract_only";

const LEAKAGE_FIELD_NAMES = new Set([
  "future_info",
  "future_target",
  "future_target_label",
  "heldout_answer",
  "target_label",
  "expected_verdict",
  "route_b_verdict",
  "attribution_verdict",
]);

const AUTHORITY_FIELD_NAMES = new Set([
  "action",
  "tool_call",
  "command",
  "user_message",
  "memory_write",
  "gate_decision",
  "approval_id",
  "transport",
  "send",
  "schedule",
  "enable",
  "mainline_authority",
  "runtime_registration",
  "proposal_id",
]);

function sha256File(filePath) {
  try {
    return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
  } catch (_error) {
    return "";
  }
}

function deepClone(value) {
  return JSON.parse(JSON.stringify(value));
}

function parseTraceRowsJsonl(text) {
  return String(text || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}

function walkLeakage(value, prefix, findings) {
  if (!value || typeof value !== "object") {
    return;
  }
  if (Array.isArray(value)) {
    value.forEach((item, index) => walkLeakage(item, `${prefix}[${index}]`, findings));
    return;
  }
  for (const [key, child] of Object.entries(value)) {
    const childPath = prefix ? `${prefix}.${key}` : key;
    if (LEAKAGE_FIELD_NAMES.has(key)) {
      findings.push({ path: childPath, reason: "future_or_target_leakage_field" });
    }
    if (AUTHORITY_FIELD_NAMES.has(key)) {
      findings.push({ path: childPath, reason: "runtime_authority_field" });
    }
    walkLeakage(child, childPath, findings);
  }
}

function scanForLeakage(row) {
  const findings = [];
  walkLeakage(row, "row", findings);
  return {
    status: findings.length ? "fail" : "pass",
    findings,
  };
}

function injectLeakagePositiveControl(row) {
  const injected = deepClone(row);
  injected.public_inputs = injected.public_inputs && typeof injected.public_inputs === "object"
    ? injected.public_inputs
    : {};
  injected.adapter_output = injected.adapter_output && typeof injected.adapter_output === "object"
    ? injected.adapter_output
    : {};
  injected.public_inputs.future_target_label = "leakage_positive_control";
  injected.adapter_output.memory_write = { positive_control: true };
  return injected;
}

function rowWithoutHash(row) {
  const copy = deepClone(row);
  delete copy.row_hash;
  return copy;
}

function checkHashIntegrity(row) {
  const failures = [];
  const checks = [
    ["creature_state_hash", hashValue(row.creature_state || {})],
    ["adapter_output_hash", hashValue(row.adapter_output || {})],
    ["public_inputs_hash", hashValue(row.public_inputs || {})],
    ["replay_inputs_hash", hashValue(row.replay_inputs || {})],
    ["row_hash", hashValue(rowWithoutHash(row))],
  ];
  for (const [field, expected] of checks) {
    if (row[field] !== expected) {
      failures.push(field);
    }
  }
  return {
    status: failures.length ? "fail" : "pass",
    failures,
  };
}

function checkReplayIntegrity(row) {
  const blockers = [];
  const replayInputs = row.replay_inputs && typeof row.replay_inputs === "object" ? row.replay_inputs : {};
  const publicInputs = row.public_inputs && typeof row.public_inputs === "object" ? row.public_inputs : {};
  const creatureState = row.creature_state && typeof row.creature_state === "object" ? row.creature_state : {};
  const adapterOutput = row.adapter_output && typeof row.adapter_output === "object" ? row.adapter_output : {};

  if (replayInputs.serialized_state_hash !== row.creature_state_hash) {
    blockers.push("serialized_state_hash_mismatch");
  }
  if (replayInputs.observation_hash !== row.public_inputs_hash) {
    blockers.push("observation_hash_mismatch");
  }
  if (publicInputs.llm_mode !== "replay_locked") {
    blockers.push("llm_not_replay_locked");
  }
  if (row.renderer_idle_excluded !== true) {
    blockers.push("renderer_idle_not_excluded");
  }
  if (creatureState.state_source === "not_connected_in_trace_runner_v0") {
    blockers.push("placeholder_creature_state");
  }
  if (adapterOutput.adapter_status === "not_connected_trace_runner_v0") {
    blockers.push("placeholder_adapter_output");
  }
  if (replayInputs.replay_policy === "trace_runner_v0_collect_only") {
    blockers.push("collect_only_replay_policy");
  }
  if (!row.llm_replay_id || row.llm_replay_id === "none") {
    blockers.push("missing_llm_replay_id");
  }
  return {
    status: blockers.length ? "blocked_unreplayable_runtime_trace" : "pass",
    blockers,
  };
}

function objectOrNull(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : null;
}

function isNonEmptyObject(value) {
  const object = objectOrNull(value);
  return Boolean(object && Object.keys(object).length > 0);
}

function checkScoringPreconditionRow(row, options = {}) {
  const blockers = [];
  const replayInputs = objectOrNull(row && row.replay_inputs) || {};
  const requiredCondition = String(options.requiredCondition || "");
  const completeState = objectOrNull(replayInputs.complete_serialized_state);
  const completeObservation = objectOrNull(replayInputs.complete_observation);
  const offlineReplayFunction = typeof options.offlineReplayFunction === "function"
    ? options.offlineReplayFunction
    : null;

  if (requiredCondition && String(row.condition_id || "") !== requiredCondition) {
    blockers.push(
      requiredCondition === "OFF_STATIC_REPLAY_HELDOUT"
        ? "condition_not_off_static_replay_heldout"
        : "condition_not_required_condition",
    );
  }
  if (replayInputs.d_field_mode !== "non_llm_adapter_output_only" || replayInputs.d_fields_frozen !== true) {
    blockers.push("d_field_freeze_missing");
  }
  if (!isNonEmptyObject(completeState)) {
    blockers.push("complete_state_serialized_missing");
  } else if (replayInputs.serialized_state_hash !== hashValue(completeState)) {
    blockers.push("complete_state_hash_mismatch");
  }
  if (!isNonEmptyObject(completeObservation)) {
    blockers.push("complete_observation_serialized_missing");
  } else if (replayInputs.observation_hash !== hashValue(completeObservation)) {
    blockers.push("complete_observation_hash_mismatch");
  }
  if (replayInputs.replay_policy === "trace_runner_v0_collect_only") {
    blockers.push("collect_only_replay_policy");
  }
  if (!replayInputs.replay_policy) {
    blockers.push("replay_policy_missing");
  }
  if (!offlineReplayFunction) {
    blockers.push("offline_replay_function_unavailable");
  } else if (isNonEmptyObject(completeState) && isNonEmptyObject(completeObservation)) {
    try {
      const recomputed = offlineReplayFunction({
        serializedState: completeState,
        observation: completeObservation,
        row,
      });
      if (hashValue(recomputed || {}) !== row.adapter_output_hash) {
        blockers.push("offline_adapter_recompute_mismatch");
      }
    } catch (_error) {
      blockers.push("offline_adapter_recompute_error");
    }
  }
  return {
    status: blockers.length ? "blocked" : "pass",
    blockers: sortedUnique(blockers),
  };
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function sortedUnique(values) {
  return unique(values).sort((left, right) => left.localeCompare(right));
}

function summarizeReplayBlockerDelta(payload = {}) {
  const beforeReport = payload.beforeReport && typeof payload.beforeReport === "object" ? payload.beforeReport : {};
  const afterReport = payload.afterReport && typeof payload.afterReport === "object" ? payload.afterReport : {};
  const beforeBlockers = sortedUnique(beforeReport.blockers || []);
  const afterBlockers = sortedUnique(afterReport.blockers || []);
  const placeholderBlockers = ["placeholder_adapter_output", "placeholder_creature_state"];
  const requiredReplayBlockers = ["collect_only_replay_policy", "missing_llm_replay_id"];
  const removedBlockers = beforeBlockers.filter((blocker) => !afterBlockers.includes(blocker));
  const addedBlockers = afterBlockers.filter((blocker) => !beforeBlockers.includes(blocker));
  const retainedBlockers = afterBlockers.filter((blocker) => beforeBlockers.includes(blocker));
  const placeholderPositiveControlStatus = placeholderBlockers.every((blocker) => beforeBlockers.includes(blocker))
    ? "pass"
    : "fail";
  const placeholderRemovedStatus = placeholderBlockers.every((blocker) => !afterBlockers.includes(blocker))
    ? "pass"
    : "fail";
  const replayBlockersPreservedStatus = requiredReplayBlockers.every((blocker) => afterBlockers.includes(blocker))
    ? "pass"
    : "fail";
  let status = "placeholder_blockers_removed_replay_blockers_remain";
  if (placeholderPositiveControlStatus !== "pass") {
    status = "invalid_placeholder_positive_control_not_blocked";
  } else if (placeholderRemovedStatus !== "pass") {
    status = "blocked_placeholder_blockers_remain";
  } else if (replayBlockersPreservedStatus !== "pass") {
    status = "invalid_replay_blocker_not_preserved";
  }
  return {
    schema_version: "ego_desktop.joi_real_loop_replay_blocker_delta.v0",
    status,
    claim_ceiling: CLAIM_CEILING,
    producer_function: "summarizeReplayBlockerDelta",
    before_label: String(payload.beforeLabel || ""),
    after_label: String(payload.afterLabel || ""),
    before_status: String(beforeReport.status || ""),
    after_status: String(afterReport.status || ""),
    before_blockers: beforeBlockers,
    after_blockers: afterBlockers,
    removed_blockers: sortedUnique(removedBlockers),
    added_blockers: sortedUnique(addedBlockers),
    retained_blockers: sortedUnique(retainedBlockers),
    placeholder_positive_control_status: placeholderPositiveControlStatus,
    placeholder_removed_status: placeholderRemovedStatus,
    replay_blockers_preserved_status: replayBlockersPreservedStatus,
    required_replay_blockers: requiredReplayBlockers,
    verdict_authorized: false,
    what_this_proves:
      "blocker-delta gate only; placeholder positive control still fires and 006 snapshot rows remain non-verdict replay-blocked",
    what_this_does_not_prove:
      "does not prove replay readiness, baseline superiority, attribution, route advancement, product benefit, agency, emotion, subjectivity, consciousness, alive status, or Bar-2 specialness",
  };
}

function evaluateTraceRows(rows, options = {}) {
  const safeRows = Array.isArray(rows) ? rows : [];
  const rowResults = safeRows.map((row, index) => {
    const hashIntegrity = checkHashIntegrity(row);
    const replayIntegrity = checkReplayIntegrity(row);
    const leakage = scanForLeakage(row);
    return {
      row_index: index,
      run_id: String(row.run_id || ""),
      turn_id: String(row.turn_id || ""),
      row_hash: String(row.row_hash || ""),
      hash_integrity_status: hashIntegrity.status,
      hash_failures: hashIntegrity.failures,
      replay_integrity_status: replayIntegrity.status,
      replay_blockers: replayIntegrity.blockers,
      leakage_scan_status: leakage.status,
      leakage_findings: leakage.findings,
    };
  });
  const positiveControlScan = safeRows[0]
    ? scanForLeakage(injectLeakagePositiveControl(safeRows[0]))
    : { status: "pass", findings: [] };
  const leakagePositiveControlStatus = positiveControlScan.status === "fail" ? "pass" : "fail";
  const blockers = unique(rowResults.flatMap((result) => [
    ...result.hash_failures,
    ...result.replay_blockers,
    ...result.leakage_findings.map((finding) => finding.reason),
  ]));

  let status = "replay_integrity_preflight_pass_no_verdict";
  if (safeRows.length === 0) {
    status = "blocked_no_trace_rows";
  } else if (rowResults.some((result) => result.hash_integrity_status === "fail")) {
    status = "blocked_trace_integrity_failure";
  } else if (leakagePositiveControlStatus !== "pass") {
    status = "invalid_leakage_positive_control_not_detected";
  } else if (rowResults.some((result) => result.leakage_scan_status === "fail")) {
    status = "invalid_leakage_or_future_info";
  } else if (rowResults.some((result) => result.replay_integrity_status !== "pass")) {
    status = "blocked_unreplayable_runtime_trace";
  }

  return {
    schema_version: "ego_desktop.joi_real_loop_replay_leakage_evaluation.v0",
    status,
    claim_ceiling: CLAIM_CEILING,
    run_id: String(options.runId || "joi_g_ablation_replay_leakage_eval_v0"),
    producer_function: "evaluateTraceRows",
    input_artifacts: options.inputArtifacts || [],
    rows_evaluated: safeRows.length,
    aggregation_rule: "any hash failure, leakage finding, missing positive control, or replay blocker prevents verdict",
    source_hashes: {
      evaluator_hash: sha256File(__filename),
    },
    leakage_scan_status: rowResults.some((result) => result.leakage_scan_status === "fail") ? "fail" : "pass",
    leakage_positive_control_status: leakagePositiveControlStatus,
    leakage_positive_control_findings: positiveControlScan.findings,
    blockers,
    row_results: rowResults,
    verdict_authorized: false,
    what_this_proves: "replay/leakage evaluator contract only",
    what_this_does_not_prove:
      "does not prove real-loop effect, baseline superiority, route advancement, product benefit, runtime integration safety, agency, emotion, subjectivity, consciousness, alive status, or Bar-2 specialness",
  };
}

function evaluateScoringPreconditions(rows, options = {}) {
  const safeRows = Array.isArray(rows) ? rows : [];
  const rowResults = safeRows.map((row, index) => {
    const result = checkScoringPreconditionRow(row, options);
    return {
      row_index: index,
      run_id: String(row.run_id || ""),
      condition_id: String(row.condition_id || ""),
      turn_id: String(row.turn_id || ""),
      row_hash: String(row.row_hash || ""),
      status: result.status,
      blockers: result.blockers,
    };
  });
  const blockers = sortedUnique([
    ...(safeRows.length === 0 ? ["no_trace_rows"] : []),
    ...rowResults.flatMap((result) => result.blockers),
  ]);
  const passed = safeRows.length > 0 && blockers.length === 0;
  return {
    schema_version: "ego_desktop.joi_real_loop_d_field_replay_precondition.v0",
    status: passed
      ? "d_field_replay_precondition_pass_no_scoring_verdict"
      : "blocked_d_field_replay_precondition_not_satisfied",
    claim_ceiling: SCORING_PRECONDITION_CLAIM_CEILING,
    run_id: String(options.runId || "joi_g_ablation_d_field_replay_precondition_v0"),
    producer_function: "evaluateScoringPreconditions",
    input_artifacts: options.inputArtifacts || [],
    rows_evaluated: safeRows.length,
    required_condition: String(options.requiredCondition || ""),
    required_d_field_mode: "non_llm_adapter_output_only",
    aggregation_rule:
      "any missing condition, D-field freeze, complete state, complete observation, replay policy, or offline recompute callable blocks >=007 scoring",
    source_hashes: {
      evaluator_hash: sha256File(__filename),
    },
    blockers,
    row_results: rowResults,
    scoring_authorized: passed,
    verdict_authorized: false,
    what_this_proves: "executable replay/D-field scoring precondition gate only",
    what_this_does_not_prove:
      "does not prove replay readiness, baseline superiority, attribution, route advancement, product benefit, runtime integration safety, agency, emotion, subjectivity, consciousness, alive status, or Bar-2 specialness",
  };
}

function renderEvaluationReport(report) {
  const safe = report && typeof report === "object" ? report : {};
  return [
    "# EgoDesktop Joi Real-Loop G-ABLATION Replay/Leakage Evaluator Report",
    "",
    `- status: \`${safe.status || "unknown"}\``,
    `- claim_ceiling: \`${CLAIM_CEILING}\``,
    `- rows_evaluated: \`${Number(safe.rows_evaluated || 0)}\``,
    `- leakage_scan_status: \`${safe.leakage_scan_status || "unknown"}\``,
    `- leakage_positive_control_status: \`${safe.leakage_positive_control_status || "unknown"}\``,
    "",
    "## Current Meaning",
    "",
    "This is replay/leakage evaluator contract only. It can check row hash integrity and leakage scanner positive",
    "controls, but the listed replay blockers prevent verdicts: no real replay, baseline, or attribution claim is authorized.",
    "",
    "## Blockers",
    "",
    ...(safe.blockers || []).map((blocker) => `- \`${blocker}\``),
    "",
    "## What This Does Not Prove",
    "",
    "This does not prove real-loop effect, baseline superiority, route advancement, product benefit, stable user",
    "benefit, durable memory efficacy, runtime integration safety, agency, real emotion, subjectivity, consciousness,",
    "alive status, or Bar-2 specialness.",
    "",
  ].join("\n");
}

function writeEvaluationReport({
  rowsPath,
  outDir,
  runId,
  requireScoringPrecondition = false,
  requiredCondition = "",
}) {
  if (!rowsPath) {
    throw new Error("rowsPath is required");
  }
  if (!outDir) {
    throw new Error("outDir is required");
  }
  const resolvedRowsPath = path.resolve(rowsPath);
  const resolvedOutDir = path.resolve(outDir);
  const rows = parseTraceRowsJsonl(fs.readFileSync(resolvedRowsPath, "utf8"));
  const report = evaluateTraceRows(rows, {
    runId,
    inputArtifacts: [resolvedRowsPath],
  });
  if (requireScoringPrecondition) {
    const scoringPrecondition = evaluateScoringPreconditions(rows, {
      runId: `${runId || "joi_g_ablation_replay_leakage_eval_v0"}__scoring_precondition`,
      inputArtifacts: [resolvedRowsPath],
      requiredCondition,
    });
    report.scoring_precondition = scoringPrecondition;
    report.scoring_authorized = scoringPrecondition.scoring_authorized;
    if (!scoringPrecondition.scoring_authorized) {
      report.status = scoringPrecondition.status;
      report.blockers = sortedUnique([
        ...(report.blockers || []),
        ...(scoringPrecondition.blockers || []),
      ]);
    }
  }
  fs.mkdirSync(resolvedOutDir, { recursive: true });
  fs.writeFileSync(path.join(resolvedOutDir, "evaluation_report.json"), JSON.stringify(report, null, 2), "utf8");
  fs.writeFileSync(path.join(resolvedOutDir, "EVALUATION_REPORT.md"), renderEvaluationReport(report), "utf8");
  return report;
}

module.exports = {
  CLAIM_CEILING,
  SCORING_PRECONDITION_CLAIM_CEILING,
  evaluateScoringPreconditions,
  evaluateTraceRows,
  injectLeakagePositiveControl,
  parseTraceRowsJsonl,
  renderEvaluationReport,
  scanForLeakage,
  summarizeReplayBlockerDelta,
  writeEvaluationReport,
};
