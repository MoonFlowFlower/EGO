const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");

const {
  CLAIM_CEILING: HARNESS_CLAIM_CEILING,
  buildJoiRealLoopGAblationContract,
  buildJoiRealLoopTraceRow,
  hashValue,
  validateNoAuthorityFields,
} = require("./joiRealLoopGAblationHarness");

const CLAIM_CEILING = "egodesktop_real_loop_g_ablation_trace_runner_contract_only";
const DEFAULT_IDLE_PARAMS = Object.freeze(["ParamMouthOpenY", "ParamJawOpen"]);

function sha256Text(text) {
  return crypto.createHash("sha256").update(String(text || "")).digest("hex");
}

function sha256File(filePath) {
  try {
    return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
  } catch (_error) {
    return "";
  }
}

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function writeJson(filePath, payload) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, JSON.stringify(payload, null, 2), "utf8");
}

function appendJsonLine(filePath, payload) {
  ensureDir(path.dirname(filePath));
  fs.appendFileSync(filePath, `${JSON.stringify(payload)}\n`, "utf8");
}

function contractBlockStatus(contract) {
  if (!contract.enabled) {
    return "disabled_default_off";
  }
  if (contract.blockers.includes("llm_mode_not_replay_locked")) {
    return "blocked_missing_llm_replay_contract";
  }
  if (contract.status !== "ready_for_explicit_harness_run") {
    return "blocked_missing_ego_authorization";
  }
  return "";
}

function sourceHashesFor(repoRoot, overrides) {
  if (overrides && typeof overrides === "object") {
    return { ...overrides };
  }
  const root = repoRoot || path.resolve(__dirname, "..", "..");
  return {
    harness_hash: sha256File(path.join(__dirname, "joiRealLoopGAblationHarness.js")),
    trace_runner_hash: sha256File(__filename),
    main_js_hash: sha256File(path.join(__dirname, "main.js")),
    repo_root_hash: sha256Text(path.resolve(root)),
  };
}

function normalizeTurn(turn, fallbackUserText) {
  const safeTurn = turn && typeof turn === "object" ? turn : {};
  const botText = String(safeTurn.bot_text || safeTurn.reply_text || "");
  return {
    status: String(safeTurn.status || ""),
    expression_name: String(safeTurn.expression_name || ""),
    bot_text: botText,
    bot_text_hash: safeTurn.bot_text_hash || hashValue(botText),
    pspc_scenario_id: String(safeTurn.pspc_scenario_id || safeTurn.pspc_reply_preview_style || ""),
    user_text_hash: hashValue(String(safeTurn.user_text || fallbackUserText || "")),
  };
}

function parameterSamplesFrom(value) {
  if (!value || typeof value !== "object") {
    return [];
  }
  if (Array.isArray(value)) {
    return value.map((item, index) => ({ sample_id: String(index), ...item }));
  }
  return Object.entries(value).map(([id, sample]) => ({
    id,
    value: sample,
  }));
}

function placeholderCreatureState(condition) {
  return {
    schema_version: "ego_desktop.joi_trace_runner.placeholder_state.v0",
    state_source: "not_connected_in_trace_runner_v0",
    condition,
    claim_ceiling: CLAIM_CEILING,
  };
}

function placeholderAdapterOutput() {
  return {
    source: "joi_real_loop_trace_runner_v0",
    adapter_status: "not_connected_trace_runner_v0",
    output_authority: "none",
    claim_ceiling: CLAIM_CEILING,
  };
}

function normalizeEntrypointProvenance(value) {
  const safe = value && typeof value === "object" ? value : {};
  if (safe.status === "ipc_event_observed") {
    return {
      schema_version: "ego_desktop.joi_real_loop_entrypoint_provenance.v0",
      claim_ceiling: CLAIM_CEILING,
      status: "ipc_event_observed",
      entrypoint_name: String(safe.entrypoint_name || "window.egoDesktop.sendChatTurn"),
      ipc_channel: String(safe.ipc_channel || "ego-desktop:chat-turn"),
      ipc_handler: String(safe.ipc_handler || "ipcMain.handle"),
      preload_bridge_name: String(safe.preload_bridge_name || "contextBridge.egoDesktop.sendChatTurn"),
      event_source: String(safe.event_source || "main_process_ipc_event"),
      web_contents_id: Number(safe.web_contents_id || 0),
      frame_routing_id: Number(safe.frame_routing_id || 0),
      frame_process_id: Number(safe.frame_process_id || 0),
      frame_url_hash: String(safe.frame_url_hash || ""),
      direct_call_negative_control:
        "absent when createJoiRealLoopTraceRunner.recordChatTurn is invoked without the main-process IPC event",
    };
  }
  return {
    schema_version: "ego_desktop.joi_real_loop_entrypoint_provenance.v0",
    claim_ceiling: CLAIM_CEILING,
    status: "absent_direct_record_chat_turn_or_legacy_row",
    entrypoint_name: "",
    ipc_channel: "",
    ipc_handler: "",
    preload_bridge_name: "",
    event_source: "not_observed",
    direct_call_negative_control: "positive_control_for_missing_ipc_event_boundary",
  };
}

function buildJoiRealLoopBackendAdapterOutput(payload = {}) {
  const desktopTurn = payload.desktopTurn && typeof payload.desktopTurn === "object" ? payload.desktopTurn : {};
  const backend = payload.backend && typeof payload.backend === "object" ? payload.backend : {};
  const snapshot = backend.joi_real_loop_trace_snapshot && typeof backend.joi_real_loop_trace_snapshot === "object"
    ? backend.joi_real_loop_trace_snapshot
    : {};
  const traceRecordHash = String(snapshot.trace_record_hash || "");
  const hasBackendSnapshot = snapshot.state_source === "ego_operator_runtime_trace_store" && traceRecordHash;
  return {
    schema_version: "ego_desktop.joi_real_loop_backend_adapter_output.v0",
    source: "ego_desktop_chat_turn_result_boundary",
    adapter_status: hasBackendSnapshot
      ? "connected_real_backend_trace_snapshot"
      : "backend_trace_snapshot_absent",
    output_authority: "none",
    expression_name: String(desktopTurn.expression_name || ""),
    chat_turn_status: String(desktopTurn.status || ""),
    backend_status: String(backend.status || desktopTurn.backend_status || ""),
    backend_reason: String(backend.reason || desktopTurn.backend_reason || ""),
    backend_trace_record_hash: traceRecordHash,
    backend_trace_state_source: String(snapshot.state_source || ""),
    llm_trace_id: String(backend.joi_real_loop_llm_trace_id || ""),
    side_effect_boundary: {
      side_effects_executed: Boolean(desktopTurn.side_effects_executed || backend.side_effects_executed),
      memory_written: Boolean(desktopTurn.memory_write || backend.memory_write),
      tools_used: Boolean(desktopTurn.tool_use || backend.tool_use),
      messages_sent: Boolean(desktopTurn.message_send || backend.message_send),
      files_written: Boolean(desktopTurn.file_write || backend.file_write),
      network_used: Boolean(desktopTurn.network_call || backend.network_call),
    },
    claim_ceiling: CLAIM_CEILING,
  };
}

function renderTraceRunnerReport(summary) {
  const safe = summary && typeof summary === "object" ? summary : {};
  return [
    "# EgoDesktop Joi Real-Loop G-ABLATION Trace Runner Report",
    "",
    `- status: \`${safe.status || "unknown"}\``,
    `- claim_ceiling: \`${CLAIM_CEILING}\``,
    `- trace_dir: \`${safe.traceDir || ""}\``,
    `- trace_row_count: \`${Number(safe.traceRowCount || 0)}\``,
    "",
    "## Current Meaning",
    "",
    "This is trace-runner contract only. It can record bounded local trace artifacts when the explicit experiment",
    "contract is enabled, but it does not prove real-loop effect, product benefit, stable user benefit, durable memory",
    "efficacy, runtime integration safety, agency, real emotion, subjectivity, consciousness, alive status, Bar-2",
    "specialness, or route advancement.",
    "",
    "## Next Minimal Action",
    "",
    "Add callable baseline/replay evaluation only after trace rows are produced from the explicit real-loop path.",
    "",
  ].join("\n");
}

function createJoiRealLoopTraceRunner(env, options = {}) {
  const contract = buildJoiRealLoopGAblationContract(env);
  const traceDir = contract.trace_dir ? path.resolve(contract.trace_dir) : "";
  const blockedStatus = contractBlockStatus(contract);
  const sourceHashes = sourceHashesFor(options.repoRoot, options.sourceHashes);
  const kernelAdoptionHook = typeof options.kernelAdoptionHook === "function" ? options.kernelAdoptionHook : null;
  let traceRowCount = 0;
  let eventCounter = 0;

  function disabledOrBlockedResult() {
    if (!blockedStatus) {
      return null;
    }
    return {
      status: blockedStatus,
      contract_status: contract.status,
      blockers: [...contract.blockers],
      trace_written: false,
      claim_ceiling: CLAIM_CEILING,
    };
  }

  function writeReport(status) {
    if (!traceDir) {
      return;
    }
    const report = {
      schema_version: "ego_desktop.joi_real_loop_trace_runner_report.v0",
      status,
      claim_ceiling: CLAIM_CEILING,
      harness_claim_ceiling: HARNESS_CLAIM_CEILING,
      trace_dir: traceDir,
      trace_row_count: traceRowCount,
      contract,
      what_this_proves: "default-off local trace-runner artifact collection only",
      what_this_does_not_prove:
        "does not prove real-loop effect, product benefit, stable user benefit, durable memory efficacy, runtime integration safety, agency, real emotion, subjectivity, consciousness, alive status, Bar-2 specialness, or route advancement",
    };
    writeJson(path.join(traceDir, "trace_runner_report.json"), report);
    fs.writeFileSync(
      path.join(traceDir, "TRACE_RUNNER_REPORT.md"),
      renderTraceRunnerReport({ status, traceDir, traceRowCount }),
      "utf8",
    );
  }

  function recordRendererReady(payload = {}) {
    const blocked = disabledOrBlockedResult();
    if (blocked) {
      return blocked;
    }
    const rendererPayload = payload.rendererPayload && typeof payload.rendererPayload === "object"
      ? payload.rendererPayload
      : {};
    const record = {
      schema_version: "ego_desktop.joi_real_loop_renderer_ready.v0",
      claim_ceiling: CLAIM_CEILING,
      model_loaded: Boolean(rendererPayload.modelLoaded),
      parameter_samples: rendererPayload.parameterSamples || {},
      visual_fit_pass: Boolean(rendererPayload.visualFitPass),
      renderer_idle_excluded: true,
      renderer_idle_params_excluded_from_d: [...DEFAULT_IDLE_PARAMS],
      source_hashes: sourceHashes,
    };
    writeJson(path.join(traceDir, "renderer_ready.json"), record);
    writeReport("renderer_ready_recorded");
    return {
      status: "renderer_ready_recorded",
      trace_written: true,
      path: path.join(traceDir, "renderer_ready.json"),
      claim_ceiling: CLAIM_CEILING,
    };
  }

  function recordChatTurn(payload = {}) {
    const blocked = disabledOrBlockedResult();
    if (blocked) {
      return blocked;
    }
    const userText = String(payload.userText || (payload.turn && payload.turn.user_text) || "");
    const condition = contract.condition;
    const creatureState = payload.creatureState || placeholderCreatureState(condition);
    const adapterOutput = payload.adapterOutput || placeholderAdapterOutput();
    const entrypointProvenance = normalizeEntrypointProvenance(payload.entrypointProvenance);
    const publicInputs = {
      user_text_hash: hashValue(userText),
      condition,
      prompt_pack: contract.prompt_pack,
      split: contract.split,
      llm_mode: contract.llm_mode,
      desktop_session_context_hash: hashValue(payload.desktopSessionContext || {}),
      desktop_recovery_context_hash: hashValue(payload.desktopRecoveryContext || {}),
      entrypoint_provenance_hash: hashValue(entrypointProvenance),
      entrypoint_provenance: entrypointProvenance,
    };
    const replayInputs = payload.replayInputs || {
      serialized_state_hash: hashValue(creatureState),
      observation_hash: hashValue(publicInputs),
      replay_policy: "trace_runner_v0_collect_only",
    };
    const rendererReady = payload.rendererReady && typeof payload.rendererReady === "object"
      ? payload.rendererReady
      : {};
    eventCounter += 1;
    const row = buildJoiRealLoopTraceRow({
      runId: String(env.JOI_REAL_LOOP_RUN_ID || "trace_runner_v0_run"),
      conditionId: condition,
      turnId: String(payload.turnId || `turn_${eventCounter}`),
      tickId: String(payload.tickId || `tick_${eventCounter}`),
      seed: String(env.JOI_REAL_LOOP_SEED || "trace_runner_v0_seed"),
      sourceHashes,
      promptId: String(payload.promptId || `prompt_${hashValue(userText).slice(0, 12)}`),
      promptPackHash: contract.prompt_pack,
      splitId: contract.split,
      llmReplayId: String(payload.llmReplayId || env.JOI_REAL_LOOP_LLM_REPLAY_ID || "none"),
      chatTurn: normalizeTurn(payload.turn, userText),
      creatureState,
      adapterOutput,
      publicInputs,
      sameAccessReproducerId: String(payload.sameAccessReproducerId || ""),
      baselineSplit: String(payload.baselineSplit || contract.split),
      live2dParameterSamples: parameterSamplesFrom(
        payload.live2dParameterSamples || rendererReady.parameterSamples,
      ),
      rendererIdleParams: payload.rendererIdleParams || [...DEFAULT_IDLE_PARAMS],
      outputEvent: payload.outputEvent || {
        order: eventCounter,
        timestamp_ms: Date.now(),
      },
      replayInputs,
    });
    if (kernelAdoptionHook) {
      const kernelAdoptionBlock = kernelAdoptionHook({ contract, eventCounter, payload, row });
      if (kernelAdoptionBlock && typeof kernelAdoptionBlock === "object") {
        row.kernel_adoption_v0 = validateNoAuthorityFields(
          kernelAdoptionBlock,
          "kernel_adoption_v0",
        );
      }
    }
    appendJsonLine(path.join(traceDir, "trace_rows.jsonl"), row);
    traceRowCount += 1;
    const hasIpcEntrypoint = entrypointProvenance.status === "ipc_event_observed";
    const verdictLabel = payload.creatureState && hasIpcEntrypoint
      ? "blocked_unreplayable_runtime_trace"
      : "blocked_missing_real_loop_entrypoint";
    writeReport(verdictLabel);
    return {
      status: "trace_row_written",
      verdict_label: verdictLabel,
      trace_written: true,
      row_hash: row.row_hash,
      path: path.join(traceDir, "trace_rows.jsonl"),
      claim_ceiling: CLAIM_CEILING,
    };
  }

  return {
    claim_ceiling: CLAIM_CEILING,
    contract,
    enabled: contract.enabled,
    ready: !blockedStatus,
    trace_dir: traceDir,
    recordChatTurn,
    recordRendererReady,
  };
}

module.exports = {
  CLAIM_CEILING,
  DEFAULT_IDLE_PARAMS,
  buildJoiRealLoopBackendAdapterOutput,
  createJoiRealLoopTraceRunner,
  normalizeEntrypointProvenance,
  renderTraceRunnerReport,
};
