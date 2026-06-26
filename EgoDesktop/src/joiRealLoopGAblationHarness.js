const crypto = require("node:crypto");

const CLAIM_CEILING = "egodesktop_real_loop_g_ablation_harness_contract_only";
const SCHEMA_VERSION = "ego_desktop.joi_real_loop_g_ablation_harness.v0";

const EXECUTABLE_FIELD_NAMES = new Set([
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

const REQUIRED_EXPERIMENT_FLAGS = Object.freeze([
  "JOI_REAL_LOOP_CONDITION",
  "JOI_REAL_LOOP_TRACE_DIR",
  "JOI_REAL_LOOP_LLM_MODE",
  "JOI_REAL_LOOP_PROMPT_PACK",
  "JOI_REAL_LOOP_SPLIT",
]);

const REQUIRED_CONDITIONS = Object.freeze([
  "CREATURE_ON",
  "CREATURE_FROZEN",
  "OFF_STATE_FLAT",
  "OFF_REACTIVE_ONLY",
  "OFF_STATIC_REPLAY_SAME_PACK",
  "OFF_STATIC_REPLAY_HELDOUT",
  "OFF_SHUFFLED_STATE",
  "CURRENT_SHIM",
  "SAME_ACCESS_REPRODUCER_BATTERY",
  "LLM_REPLAY_LOCKED",
]);

const DIAGNOSTIC_CONDITIONS = Object.freeze([
  "ZERO_OUTPUT",
  "RANDOM_STATE",
  "LEAK_INJECTED_POSCTRL",
]);

const ALLOWED_VERDICTS = Object.freeze([
  "blocked_missing_ego_authorization",
  "blocked_missing_llm_replay_contract",
  "blocked_missing_real_loop_entrypoint",
  "blocked_unreplayable_runtime_trace",
  "invalid_leakage_or_future_info",
  "invalid_baseline_parity_or_privileged_state_leak",
  "invalid_renderer_idle_drives_metric",
  "invalid_llm_unlocked_confounds_metric",
  "invalid_metric_uses_same_pack_static_replay_as_positive_evidence",
  "real_loop_g_ablation_fail_no_creature_effect",
  "real_loop_g_ablation_baseline_saturated_stop",
  "real_loop_g_ablation_partial_causal_path_only",
  "real_loop_causal_path_attribution_pass",
]);

const SAME_ACCESS_REPRODUCER_FAMILIES = Object.freeze([
  "ema_history",
  "hysteresis_history",
  "logistic_short_context",
  "linear_short_context",
  "current_turn_reactive",
  "fixed_shim_template",
]);

const STATIC_REPLAY_POLICIES = Object.freeze({
  OFF_STATIC_REPLAY_SAME_PACK: Object.freeze({
    role: "diagnostic_closure_floor",
    input_policy: "same_prompt_pack_exact_output_schedule",
    can_support_positive_verdict: false,
  }),
  OFF_STATIC_REPLAY_HELDOUT: Object.freeze({
    role: "decisive_input_blind_replay_floor",
    input_policy: "calibration_reference_schedule_evaluated_on_heldout_pack",
    can_support_positive_verdict: false,
  }),
});

function normalizeEnv(env) {
  const source = env && typeof env === "object" ? env : {};
  const normalized = {};
  for (const [key, value] of Object.entries(source)) {
    normalized[String(key)] = value === undefined || value === null ? "" : String(value).trim();
  }
  return normalized;
}

function allConditions() {
  return [...REQUIRED_CONDITIONS, ...DIAGNOSTIC_CONDITIONS];
}

function stableValue(value) {
  if (Array.isArray(value)) {
    return value.map((item) => stableValue(item));
  }
  if (value && typeof value === "object") {
    return Object.keys(value).sort().reduce((acc, key) => {
      acc[key] = stableValue(value[key]);
      return acc;
    }, {});
  }
  return value;
}

function hashValue(value) {
  return crypto
    .createHash("sha256")
    .update(JSON.stringify(stableValue(value)))
    .digest("hex");
}

function containsExecutableField(value) {
  if (!value || typeof value !== "object") {
    return false;
  }
  if (Array.isArray(value)) {
    return value.some((item) => containsExecutableField(item));
  }
  return Object.entries(value).some(([key, child]) => (
    EXECUTABLE_FIELD_NAMES.has(key) || containsExecutableField(child)
  ));
}

function validateNoAuthorityFields(value, label) {
  if (containsExecutableField(value)) {
    throw new Error(`${label || "payload"} contains runtime authority field`);
  }
  return value;
}

function missingRequiredFlags(env) {
  return REQUIRED_EXPERIMENT_FLAGS.filter((key) => !env[key]);
}

function buildJoiRealLoopGAblationContract(env) {
  const safeEnv = normalizeEnv(env);
  const enabled = safeEnv.JOI_REAL_LOOP_G_ABLATION === "1";
  const missing = enabled ? missingRequiredFlags(safeEnv) : [];
  const condition = enabled ? safeEnv.JOI_REAL_LOOP_CONDITION : "";
  const knownCondition = !condition || allConditions().includes(condition);
  const llmReplayLocked = !enabled || safeEnv.JOI_REAL_LOOP_LLM_MODE === "replay_locked";
  const ready = enabled && missing.length === 0 && knownCondition && llmReplayLocked;

  let status = "disabled_default_off";
  const blockers = [];
  if (enabled && missing.length > 0) {
    status = "blocked_invalid_contract";
    blockers.push("missing_required_experiment_flags");
  }
  if (enabled && !knownCondition) {
    status = "blocked_invalid_contract";
    blockers.push("unknown_condition");
  }
  if (enabled && !llmReplayLocked) {
    status = "blocked_invalid_contract";
    blockers.push("llm_mode_not_replay_locked");
  }
  if (ready) {
    status = "ready_for_explicit_harness_run";
  }

  return {
    schema_version: SCHEMA_VERSION,
    contract_type: "default_off_real_loop_g_ablation_contract",
    claim_ceiling: CLAIM_CEILING,
    enabled,
    status,
    blockers,
    missing_required_flags: missing,
    condition,
    trace_dir: enabled ? safeEnv.JOI_REAL_LOOP_TRACE_DIR : "",
    llm_mode: enabled ? safeEnv.JOI_REAL_LOOP_LLM_MODE : "",
    prompt_pack: enabled ? safeEnv.JOI_REAL_LOOP_PROMPT_PACK : "",
    split: enabled ? safeEnv.JOI_REAL_LOOP_SPLIT : "",
    runtime_authority: "none",
    mainline_connected: false,
    adapter_registered: false,
    default_behavior_unchanged_when_disabled: true,
    no_authority: {
      direct_action_allowed: false,
      direct_user_message_allowed: false,
      direct_memory_write_allowed: false,
      runtime_gate_bypass_allowed: false,
      runtime_registration_allowed: false,
      proactive_trigger_allowed: false,
      planner_execution_allowed: false,
      model_execution_allowed: false,
      training_allowed: false,
    },
    required_conditions: [...REQUIRED_CONDITIONS],
    diagnostic_conditions: [...DIAGNOSTIC_CONDITIONS],
    required_experiment_flags: ["JOI_REAL_LOOP_G_ABLATION", ...REQUIRED_EXPERIMENT_FLAGS],
  };
}

function requireObject(value, label) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${label} must be an object`);
  }
  return value;
}

function requireText(value, label) {
  const text = String(value || "").trim();
  if (!text) {
    throw new Error(`${label} is required`);
  }
  return text;
}

function buildJoiRealLoopTraceRow(payload) {
  const input = requireObject(payload, "trace payload");
  const conditionId = requireText(input.conditionId, "conditionId");
  if (!allConditions().includes(conditionId)) {
    throw new Error(`conditionId is unknown: ${conditionId}`);
  }

  const chatTurn = requireObject(input.chatTurn, "chatTurn");
  const creatureState = validateNoAuthorityFields(
    requireObject(input.creatureState, "creatureState"),
    "creatureState",
  );
  const adapterOutput = validateNoAuthorityFields(
    requireObject(input.adapterOutput, "adapterOutput"),
    "adapterOutput",
  );
  const publicInputs = validateNoAuthorityFields(
    requireObject(input.publicInputs, "publicInputs"),
    "publicInputs",
  );
  const replayInputs = validateNoAuthorityFields(
    requireObject(input.replayInputs, "replayInputs"),
    "replayInputs",
  );

  const rendererIdleParams = Array.isArray(input.rendererIdleParams)
    ? input.rendererIdleParams.map((item) => String(item))
    : [];
  const row = {
    schema_version: "ego_desktop.joi_real_loop_trace_row.v0",
    claim_ceiling: CLAIM_CEILING,
    run_id: requireText(input.runId, "runId"),
    condition_id: conditionId,
    turn_id: requireText(input.turnId, "turnId"),
    tick_id: requireText(input.tickId, "tickId"),
    seed: requireText(input.seed, "seed"),
    source_hashes: requireObject(input.sourceHashes, "sourceHashes"),
    prompt_id: requireText(input.promptId, "promptId"),
    prompt_pack_hash: requireText(input.promptPackHash, "promptPackHash"),
    split_id: requireText(input.splitId, "splitId"),
    llm_replay_id: input.llmReplayId === undefined ? "none" : String(input.llmReplayId || "none"),
    chat_turn: {
      status: String(chatTurn.status || ""),
      expression_name: String(chatTurn.expression_name || ""),
      bot_text_hash: chatTurn.bot_text_hash || hashValue(String(chatTurn.bot_text || "")),
      pspc_scenario_id: String(chatTurn.pspc_scenario_id || ""),
    },
    creature_state_hash: hashValue(creatureState),
    creature_state: creatureState,
    adapter_output_hash: hashValue(adapterOutput),
    adapter_output: adapterOutput,
    public_inputs_hash: hashValue(publicInputs),
    public_inputs: publicInputs,
    same_access_reproducer_id: String(input.sameAccessReproducerId || ""),
    baseline_split: String(input.baselineSplit || input.splitId || ""),
    live2d_parameter_samples: Array.isArray(input.live2dParameterSamples)
      ? input.live2dParameterSamples.map((item) => stableValue(item))
      : [],
    renderer_idle_params_excluded_from_d: rendererIdleParams,
    renderer_idle_excluded: true,
    output_event: requireObject(input.outputEvent, "outputEvent"),
    replay_inputs_hash: hashValue(replayInputs),
    replay_inputs: replayInputs,
  };
  return {
    ...row,
    row_hash: hashValue(row),
  };
}

function buildBaselineEvaluationPlan() {
  return {
    schema_version: "ego_desktop.joi_real_loop_baseline_plan.v0",
    claim_ceiling: CLAIM_CEILING,
    static_replay_policies: STATIC_REPLAY_POLICIES,
    same_access_reproducer_battery: {
      selection_rule: "report_best_or_closest_reproducer_on_heldout_split",
      parity_requirement: "same public inputs as creature adapter; privileged gaps are invalid, not attribution",
      families: [...SAME_ACCESS_REPRODUCER_FAMILIES],
    },
    gates: [
      "flat_movement_is_necessary_not_sufficient",
      "same_pack_static_replay_is_diagnostic_only",
      "heldout_static_replay_equivalence_means_baseline_saturation",
      "best_same_access_reproducer_equivalence_means_baseline_saturation",
      "privileged_state_gap_means_invalid_parity_or_leakage",
      "renderer_idle_cannot_drive_metric",
      "llm_output_must_be_replay_locked_or_excluded",
    ],
  };
}

function decideJoiRealLoopVerdict(signals) {
  const safe = signals && typeof signals === "object" ? signals : {};
  if (safe.missingEgoAuthorization) {
    return "blocked_missing_ego_authorization";
  }
  if (safe.missingLlmReplayContract) {
    return "blocked_missing_llm_replay_contract";
  }
  if (safe.missingRealLoopEntrypoint) {
    return "blocked_missing_real_loop_entrypoint";
  }
  if (safe.unreplayableRuntimeTrace) {
    return "blocked_unreplayable_runtime_trace";
  }
  if (safe.leakageOrFutureInfo) {
    return "invalid_leakage_or_future_info";
  }
  if (safe.privilegedStateGap) {
    return "invalid_baseline_parity_or_privileged_state_leak";
  }
  if (safe.samePackReplayUsedAsPositiveEvidence) {
    return "invalid_metric_uses_same_pack_static_replay_as_positive_evidence";
  }
  if (safe.rendererIdleDrivesMetric) {
    return "invalid_renderer_idle_drives_metric";
  }
  if (safe.llmUnlockedConfoundsMetric) {
    return "invalid_llm_unlocked_confounds_metric";
  }
  if (!safe.creatureEffectPresent) {
    return "real_loop_g_ablation_fail_no_creature_effect";
  }
  if (safe.heldoutStaticReplayEquivalent || safe.sameAccessBestEquivalent) {
    return "real_loop_g_ablation_baseline_saturated_stop";
  }
  if (safe.partialCausalPathOnly) {
    return "real_loop_g_ablation_partial_causal_path_only";
  }
  return "real_loop_causal_path_attribution_pass";
}

module.exports = {
  ALLOWED_VERDICTS,
  CLAIM_CEILING,
  DIAGNOSTIC_CONDITIONS,
  REQUIRED_CONDITIONS,
  REQUIRED_EXPERIMENT_FLAGS,
  SAME_ACCESS_REPRODUCER_FAMILIES,
  STATIC_REPLAY_POLICIES,
  allConditions,
  buildBaselineEvaluationPlan,
  buildJoiRealLoopGAblationContract,
  buildJoiRealLoopTraceRow,
  decideJoiRealLoopVerdict,
  hashValue,
  validateNoAuthorityFields,
};
