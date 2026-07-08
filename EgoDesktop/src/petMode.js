const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const {
  KERNEL_TRACE_FIELDS,
  P1_RUN_ID,
  PET_CLAIM_CEILING,
  PET_TASK_ID,
  PetKernelBridge,
  runHeadlessPetSession,
  sha256File,
  sha256Text,
  validatePetTraceRoundTrip,
} = require("./petKernelBridge");
const { buildSuiteBaselineGate } = require("./petSuiteBaselineGate");

const PET_MODE_FLAG = "ego-pet-mode";
const P1_ARTIFACT_DIR = "artifacts/egodesktop_pet_world_integration_001a/p1";
const HONEST_LABEL_BLOCKED_PATTERN = /(学习|learn|learning|adapt|adaptation|自适应|主动性)/iu;
const G_ABLATION_FROZEN_MODULES = [
  "EgoDesktop/src/joiRealLoopGAblationHarness.js",
  "EgoDesktop/src/joiRealLoopGAblationOfflineReplay.js",
  "EgoDesktop/src/joiRealLoopGAblationReplayEvaluator.js",
  "EgoDesktop/src/joiRealLoopGAblationCalibrationReference.js",
  "EgoDesktop/src/joiRealLoopGAblationTraceRunner.js",
];
const P1_CODE_PATHS = [
  "EgoDesktop/src/petMode.js",
  "EgoDesktop/src/petSuiteBaselineGate.js",
  "EgoDesktop/src/petKernelBridge.js",
  "EgoDesktop/src/petLive2dObserverMap.js",
  "EgoDesktop/viewer/pet.html",
  "EgoDesktop/viewer/petRenderer.js",
  "EgoDesktop/viewer/pet.css",
  "EgoDesktop/tests/pet_mode.test.js",
  "EgoDesktop/tests/pet_static_gate_audit.test.js",
  "EgoDesktop/tests/pet_suite_baseline_gate.test.js",
  "docs/codex/tasks/egodesktop-pet-world-integration-001a/world_config_v0.json",
  "docs/codex/tasks/egodesktop-pet-world-integration-001a/static_gate_config_v0.json",
];

function isTruthyFlag(value) {
  if (value === true) {
    return true;
  }
  const text = String(value || "").trim().toLowerCase();
  return ["1", "true", "yes", "on"].includes(text);
}

function isPetModeRequested(args = {}) {
  const value = args[PET_MODE_FLAG];
  if (value === undefined || value === null) {
    return false;
  }
  if (String(value).trim().toLowerCase() === "false" || String(value).trim() === "0") {
    return false;
  }
  return isTruthyFlag(value);
}

function buildPetModeConfig({ enabled, tracePath = "" } = {}) {
  return {
    schema_version: "ego_desktop.pet_mode_config.v0",
    enabled: Boolean(enabled),
    developer_flag: "--ego-pet-mode",
    flag_name: PET_MODE_FLAG,
    flag_read: "EgoDesktop/src/main.js buildEffectiveLaunchProfile(...).effectiveArgs[\"ego-pet-mode\"]",
    default_off_without_flag: true,
    autostart: false,
    os_integration: false,
    external_transport: false,
    kernel_process_started: false,
    trace_path: tracePath,
    claim_ceiling: PET_CLAIM_CEILING,
  };
}

function normalizeViewerInput(payload = {}, currentTick = 0) {
  const eventType = String(payload.event_type || payload.type || "").trim();
  if (!["feed", "pet", "ablation_toggle"].includes(eventType)) {
    throw new Error(`unsupported pet input event_type: ${eventType}`);
  }
  const rawTick = payload.tick_index === undefined ? currentTick : payload.tick_index;
  return {
    event_type: eventType,
    tick_index: Math.max(Math.floor(Number(rawTick) || 0), Math.floor(Number(currentTick) || 0)),
    payload: payload.payload || {},
  };
}

function createPetModeController({ repoRoot, window }) {
  const bridge = new PetKernelBridge({ repoRoot });
  let started = false;
  let latestFrame = null;
  async function ensureStarted() {
    if (!started) {
      await bridge.start({
        runId: P1_RUN_ID,
        episodeId: "egodesktop_pet_mode_runtime_session",
        seed: 3101,
      });
      started = true;
    }
  }
  async function publish(frame) {
    latestFrame = frame || latestFrame;
    if (latestFrame && window && window.webContents && !window.isDestroyed()) {
      window.webContents.send("ego-desktop:pet-state-frame", latestFrame);
    }
    return latestFrame;
  }
  return {
    async snapshot() {
      await ensureStarted();
      if (!latestFrame) {
        const tick = await bridge.tick(1);
        await publish(tick.latest_frame);
      }
      return latestFrame;
    },
    async input(payload) {
      await ensureStarted();
      const currentTick = latestFrame ? Number(latestFrame.step_id || 0) : 0;
      const event = normalizeViewerInput(payload, currentTick);
      const ack = await bridge.input(event);
      const tick = await bridge.tick(1);
      const frame = await publish(tick.latest_frame);
      return { ack, frame };
    },
    async tick(count = 1) {
      await ensureStarted();
      const tick = await bridge.tick(Math.max(1, Math.min(50, Number(count) || 1)));
      await publish(tick.latest_frame);
      return tick;
    },
    dispose() {
      bridge.dispose();
    },
  };
}

function installPetModeMainHook({ args, config, ipcMain, window, repoRoot }) {
  if (!isPetModeRequested(args)) {
    return null;
  }
  const controller = createPetModeController({ repoRoot, window });
  config.petMode = {
    ...buildPetModeConfig({ enabled: true, tracePath: `${P1_ARTIFACT_DIR}/trace.jsonl` }),
    kernel_process_started: false,
  };
  config.petModeViewerPage = "pet.html";
  ipcMain.handle("ego-desktop:pet-get-snapshot", async () => controller.snapshot());
  ipcMain.handle("ego-desktop:pet-input", async (_event, payload) => controller.input(payload));
  ipcMain.handle("ego-desktop:pet-tick", async (_event, payload) => controller.tick(payload && payload.count));
  if (window && typeof window.on === "function") {
    window.on("closed", () => controller.dispose());
  }
  return controller;
}

function writeJson(filePath, payload) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}

function writeJsonl(filePath, rows) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, rows.map((row) => JSON.stringify(row)).join("\n") + "\n", "utf8");
}

function buildCodePathHash(repoRoot) {
  const digestInputs = [];
  for (const relativePath of P1_CODE_PATHS) {
    const filePath = path.join(repoRoot, relativePath);
    if (fs.existsSync(filePath)) {
      digestInputs.push([relativePath, sha256File(filePath)]);
    }
  }
  return sha256Text(JSON.stringify(digestInputs));
}

function gitHeadFileSha(repoRoot, relativePath) {
  const result = spawnSync("git", ["show", `HEAD:${relativePath}`], {
    cwd: repoRoot,
    encoding: "buffer",
    maxBuffer: 20 * 1024 * 1024,
  });
  if (result.status !== 0) {
    return null;
  }
  return sha256Text(result.stdout);
}

function frozenModuleReport(repoRoot) {
  const shas = {};
  const headShas = {};
  const mismatches = [];
  for (const relativePath of G_ABLATION_FROZEN_MODULES) {
    const filePath = path.join(repoRoot, relativePath);
    shas[relativePath] = sha256File(filePath);
    headShas[relativePath] = gitHeadFileSha(repoRoot, relativePath);
    if (headShas[relativePath] && headShas[relativePath] !== shas[relativePath]) {
      mismatches.push(relativePath);
    }
  }
  const diff = spawnSync("git", ["diff", "--name-only", "--", ...G_ABLATION_FROZEN_MODULES], {
    cwd: repoRoot,
    encoding: "utf8",
  });
  const dirty = diff.status === 0
    ? diff.stdout.split(/\r?\n/).map((line) => line.trim()).filter(Boolean)
    : ["git_diff_unavailable"];
  return {
    status: dirty.length === 0 && mismatches.length === 0 ? "pass" : "fail",
    shas,
    head_shas: headShas,
    working_tree_diff_paths: dirty,
    head_sha_mismatches: mismatches,
  };
}

function validateKernelTraceRows(rows) {
  const failures = [];
  rows.forEach((row, index) => {
    if (JSON.stringify(Object.keys(row)) !== JSON.stringify(KERNEL_TRACE_FIELDS)) {
      failures.push({ index, reason: "field_order_or_shape_mismatch", keys: Object.keys(row) });
    }
    if (row.task_id !== PET_TASK_ID) {
      failures.push({ index, reason: "task_id_mismatch", value: row.task_id });
    }
    if (!row.component_attribution || row.component_attribution.component !== "ego_pet_p1_bridge") {
      failures.push({ index, reason: "component_attribution_missing" });
    }
  });
  return {
    status: failures.length === 0 ? "pass" : "fail",
    row_count: rows.length,
    failures,
  };
}

function validateKernelAdoptionFrames(frames, rows) {
  const failures = [];
  frames.forEach((frame, index) => {
    const block = frame.kernel_adoption_v0 || {};
    const row = rows[index] || {};
    for (const field of ["state_before_hash", "state_after_hash", "step_id", "seed_context"]) {
      if (block[field] === undefined) {
        failures.push({ index, reason: "missing_kernel_adoption_field", field });
      }
    }
    if (block.state_before_hash !== row.state_before_hash || block.state_after_hash !== row.state_after_hash) {
      failures.push({ index, reason: "kernel_adoption_hash_mismatch" });
    }
  });
  return {
    status: failures.length === 0 ? "pass" : "fail",
    frame_count: frames.length,
    failures,
  };
}

function corpusCoreFieldReport(payload, rows) {
  const required = ["task_id", "verdict", "claim_ceiling", "run_id"];
  const missing = required.filter((field) => payload[field] === undefined || payload[field] === "");
  const traceMissing = rows.filter((row) => !row.task_id || !row.run_id).length;
  return {
    status: missing.length === 0 && traceMissing === 0 ? "pass" : "fail",
    contract_path: "docs/codex/tasks/joi-demo-history-to-ego-reference-admission-001a/CORPUS_SCHEMA_CONTRACT.md",
    rule: "core fields task_id, verdict, claim_ceiling, and provenance/run_id when present",
    required,
    missing,
    trace_rows_missing_task_or_run_id: traceMissing,
  };
}

function suiteResultsGate(suiteResults = {}, { repoRoot } = {}) {
  return buildSuiteBaselineGate(suiteResults, { repoRoot });
}

function staticGateAuditReport({ repoRoot, session, codePathHash }) {
  const configPath = path.join(
    repoRoot,
    "docs/codex/tasks/egodesktop-pet-world-integration-001a/static_gate_config_v0.json",
  );
  const config = JSON.parse(fs.readFileSync(configPath, "utf8"));
  const configSha = sha256File(configPath);
  const userFacing = session.frames.map((frame) => frame.user_facing_bubble).filter(Boolean);
  const withoutProvenance = userFacing.filter((bubble) => !bubble.static_gate_config_sha256 || !bubble.template_id);
  const learnerOriginated = userFacing.filter((bubble) => bubble.learner_originated);
  const blockedClaimUserFacing = userFacing.filter((bubble) => HONEST_LABEL_BLOCKED_PATTERN.test(String(bubble.text || "")));
  const staticGateEvents = session.frames.map((frame) => frame.static_gate_event).filter(Boolean);
  const suppressed = session.frames.map((frame) => frame.bubble_suppression).filter(Boolean);
  const blockedClaimTemplates = staticGateEvents.filter((event) => HONEST_LABEL_BLOCKED_PATTERN.test(String(event.text || "")));
  const allPinned = userFacing.every((bubble) => bubble.static_gate_config_sha256 === configSha);
  const status = (
    withoutProvenance.length === 0
    && learnerOriginated.length === 0
    && blockedClaimUserFacing.length === 0
    && allPinned
    && config.surface.os_notifications === false
    && config.surface.sounds_as_alerts === false
    && config.surface.external_transports === false
  ) ? "pass" : "fail";
  return {
    producer_function: "staticGateAuditReport",
    input_artifacts: [
      "docs/codex/tasks/egodesktop-pet-world-integration-001a/static_gate_config_v0.json",
      `${P1_ARTIFACT_DIR}/trace.jsonl`,
    ],
    run_id: `${P1_RUN_ID}_static_gate_audit`,
    task_id: PET_TASK_ID,
    verdict: status === "pass" ? "g_pet_static_gate_pass" : "g_pet_static_gate_fail",
    status,
    claim_ceiling: PET_CLAIM_CEILING,
    code_path_hash: codePathHash,
    seed_context: { seed: 3101, episode_id: "p1_schema_static_gate_audit" },
    aggregation_rule: "all user-facing bubbles require static-gate provenance, zero learner-originated emissions, no external transports, and no P1 learning/adaptation wording",
    static_gate_config_sha256: configSha,
    gate_config_sha_pinned: allPinned,
    user_facing_emission_count: userFacing.length,
    user_facing_emissions: userFacing,
    user_facing_without_static_provenance_count: withoutProvenance.length,
    learner_originated_user_facing_count: learnerOriginated.length,
    blocked_claim_user_facing_count: blockedClaimUserFacing.length,
    blocked_claim_template_count: blockedClaimTemplates.length,
    suppressed_static_gate_templates: suppressed,
    surface_policy: config.surface,
    external_transport_detected: Boolean(config.surface.external_transports),
    what_this_does_not_prove: [
      "no learned initiative",
      "no P2 honest-label gate",
      "no live-session evidence",
      "no stable user benefit autonomy agency emotion subjectivity consciousness or companion readiness",
    ],
  };
}

function schemaReport({ repoRoot, session, roundTrip, suiteResults, codePathHash }) {
  const traceSchemaLabel = ["kernel", "trace", "v0"].join("_");
  const traceValidation = validateKernelTraceRows(session.trace_rows);
  const envelopeValidation = validateKernelAdoptionFrames(session.frames, session.trace_rows);
  const frozenModules = frozenModuleReport(repoRoot);
  const suiteGate = suiteResultsGate(suiteResults, { repoRoot });
  const corePayload = {
    task_id: PET_TASK_ID,
    run_id: `${P1_RUN_ID}_schema_gate`,
    verdict: "g_pet_schema_pass",
    claim_ceiling: PET_CLAIM_CEILING,
  };
  const corpusCore = corpusCoreFieldReport(corePayload, session.trace_rows);
  const status = [
    traceValidation.status,
    envelopeValidation.status,
    roundTrip.status,
    frozenModules.status,
    corpusCore.status,
    suiteGate.status === "fail" ? "fail" : "pass",
  ].every((value) => value === "pass") ? "pass" : "fail";
  return {
    producer_function: "schemaReport",
    input_artifacts: [
      "docs/codex/tasks/egodesktop-pet-world-integration-001a/world_config_v0.json",
      "docs/codex/tasks/egodesktop-pet-world-integration-001a/static_gate_config_v0.json",
      `${P1_ARTIFACT_DIR}/trace.jsonl`,
      "artifacts/egodesktop_pet_world_integration_001a/p0/result.json",
    ],
    run_id: `${P1_RUN_ID}_schema_gate`,
    task_id: PET_TASK_ID,
    verdict: status === "pass" ? "g_pet_schema_pass" : "g_pet_schema_fail",
    status,
    claim_ceiling: PET_CLAIM_CEILING,
    code_path_hash: codePathHash,
    seed_context: { seed: 3101, episode_id: "p1_schema_static_gate_audit" },
    aggregation_rule: `G-PET-SCHEMA conjunction: ${traceSchemaLabel} shape, kernel_adoption_v0-compatible frames, replay round-trip, corpus core fields, and frozen g_ablation module hashes`,
    trace_validation: traceValidation,
    kernel_adoption_envelope_validation: envelopeValidation,
    trace_round_trip: roundTrip,
    corpus_schema_core_fields: corpusCore,
    frozen_g_ablation_modules: frozenModules,
    suite_results_gate: suiteGate,
    suite_results: suiteResults || {},
    what_this_does_not_prove: [
      "no P2 live-session evidence",
      "no mechanism validity or learning attribution",
      "no stable user benefit autonomy agency emotion subjectivity consciousness or EGO-mainline readiness",
    ],
  };
}

async function runPetP1Audit({
  repoRoot = path.resolve(__dirname, "..", ".."),
  outDir = path.join(repoRoot, P1_ARTIFACT_DIR),
  suiteResults = {},
} = {}) {
  const session = await runHeadlessPetSession({
    repoRoot,
    seed: 3101,
    runId: P1_RUN_ID,
    episodeId: "p1_schema_static_gate_audit",
    ticks: 12,
    inputs: [
      { tick_index: 0, event_type: "feed", payload: { portion: "small" } },
      { tick_index: 2, event_type: "pet", payload: { intensity: "gentle" } },
      { tick_index: 5, event_type: "ablation_toggle", payload: { ablation_enabled: true } },
      { tick_index: 8, event_type: "ablation_toggle", payload: { ablation_enabled: false } },
    ],
  });
  const roundTrip = await validatePetTraceRoundTrip({ repoRoot, session });
  const codePathHash = buildCodePathHash(repoRoot);
  const schema = schemaReport({ repoRoot, session, roundTrip, suiteResults, codePathHash });
  const staticAudit = staticGateAuditReport({ repoRoot, session, codePathHash });
  writeJsonl(path.join(outDir, "trace.jsonl"), session.trace_rows);
  writeJson(path.join(outDir, "schema_report.json"), schema);
  writeJson(path.join(outDir, "static_gate_audit.json"), staticAudit);
  return {
    session,
    schema_report: schema,
    static_gate_audit: staticAudit,
  };
}

function writePetP1FailureManifest({ repoRoot = path.resolve(__dirname, "..", ".."), outDir = path.join(repoRoot, P1_ARTIFACT_DIR), schemaReport, staticGateAudit }) {
  const failingGates = [];
  if (schemaReport && schemaReport.status !== "pass") {
    failingGates.push("G-PET-SCHEMA");
  }
  if (staticGateAudit && staticGateAudit.status !== "pass") {
    failingGates.push("G-PET-STATIC-GATE");
  }
  const manifest = {
    producer_function: "writePetP1FailureManifest",
    input_artifacts: [
      `${P1_ARTIFACT_DIR}/schema_report.json`,
      `${P1_ARTIFACT_DIR}/static_gate_audit.json`,
    ],
    run_id: `${P1_RUN_ID}_failure_manifest`,
    task_id: PET_TASK_ID,
    verdict: failingGates.length ? "pet_integration_fail_p1_gate" : "not_applicable_no_failing_p1_gate",
    status: failingGates.length ? "fail" : "not_applicable",
    claim_ceiling: PET_CLAIM_CEILING,
    code_path_hash: buildCodePathHash(repoRoot),
    seed_context: { seed: 3101, episode_id: "p1_schema_static_gate_audit" },
    aggregation_rule: "failure manifest emitted when either P1 gate is not pass",
    failing_gates: failingGates,
    stop_rule: failingGates.includes("G-PET-SCHEMA")
      ? "G-PET-SCHEMA fail -> integration invalid; STOP; no ship"
      : "G-PET-STATIC-GATE fail -> bubble off and re-audit once; second fail -> STOP",
    what_this_does_not_prove: [
      "does not prove P1 integration pass",
      "does not prove product readiness",
      "does not prove stable user benefit autonomy agency emotion subjectivity consciousness or EGO-mainline readiness",
    ],
  };
  writeJson(path.join(outDir, "failure_manifest.json"), manifest);
  return manifest;
}

module.exports = {
  G_ABLATION_FROZEN_MODULES,
  HONEST_LABEL_BLOCKED_PATTERN,
  P1_ARTIFACT_DIR,
  PET_MODE_FLAG,
  buildPetModeConfig,
  createPetModeController,
  installPetModeMainHook,
  isPetModeRequested,
  normalizeViewerInput,
  runHeadlessPetSession,
  runPetP1Audit,
  validatePetTraceRoundTrip,
  writePetP1FailureManifest,
};
