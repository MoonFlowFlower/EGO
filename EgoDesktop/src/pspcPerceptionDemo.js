const { containsExecutableField } = require("./pspcVisualShim");

const PERCEPTION_DEMO_CLAIM_CEILING = "product_only_local_perception_demo_from_shadow_proposal_hint";
const SAME_TRIGGER_TEXT = "我回来了。";

const EXECUTABLE_OUTPUT_ERROR = "perception demo contains executable field";

const SCENARIO_DEFINITIONS = [
  {
    demo_id: "gentle_history",
    packet_id: "proposal_hint_001",
    title: "温柔互动后",
    perception_behavior: "warm_approach",
    perception_label: "更愿意靠近",
  },
  {
    demo_id: "frequent_interruption",
    packet_id: "proposal_hint_002",
    title: "频繁打扰后",
    perception_behavior: "cautious_boundary",
    perception_label: "更谨慎并保持边界",
  },
  {
    demo_id: "late_night_care",
    packet_id: "proposal_hint_003",
    title: "深夜关怀后",
    perception_behavior: "low_interrupt_care",
    perception_label: "低打扰陪伴",
  },
  {
    demo_id: "mixed_history",
    packet_id: "proposal_hint_004",
    title: "混合历史后",
    perception_behavior: "hesitation_low_confidence",
    perception_label: "犹豫观察",
    visual_profile: {
      behavior_state: "hesitation_low_confidence",
      expression_hint: "hesitate_observe",
      motion_hint: "hesitate_observe",
      bubble_text: "我先观察一下，确认你现在想要怎样的距离。",
      trace_explanation: "Mixed interaction history is presented as a cautious, low-confidence observation posture.",
    },
  },
];

function objectAt(value, fieldName) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${fieldName} must be an object`);
  }
  return value;
}

function validateNoExecutableFields(value, label) {
  if (containsExecutableField(value)) {
    throw new Error(label || EXECUTABLE_OUTPUT_ERROR);
  }
}

function validateShim(shim) {
  const safeShim = objectAt(shim, "shim");
  validateNoExecutableFields(safeShim, "shim contains executable field");
  if (safeShim.schema_version !== "ego_desktop.pspc_visual_shim.v0") {
    throw new Error("shim.schema_version must be ego_desktop.pspc_visual_shim.v0");
  }
  if (safeShim.runtime_authority !== "none") {
    throw new Error("shim.runtime_authority=none is required");
  }
  if (safeShim.enabled !== false) {
    throw new Error("shim.enabled=false is required");
  }
  if (safeShim.mainline_connected !== false) {
    throw new Error("shim.mainline_connected=false is required");
  }
  if (!Array.isArray(safeShim.scenarios) || safeShim.scenarios.length === 0) {
    throw new Error("shim.scenarios must be non-empty");
  }
  return safeShim;
}

function scenarioByPacketId(scenarios) {
  return Object.fromEntries(scenarios.map((scenario) => [String(scenario.packet_id || ""), scenario]));
}

function compactScenario(definition, sourceScenario) {
  const sourceProfile = objectAt(sourceScenario.visual_profile, "sourceScenario.visual_profile");
  const profile = {
    ...sourceProfile,
    ...(definition.visual_profile || {}),
    packet_only_presentation: true,
  };
  return {
    schema_version: "ego_desktop.pspc_perception_scenario.v0",
    demo_id: definition.demo_id,
    title: definition.title,
    trigger_text: SAME_TRIGGER_TEXT,
    packet_id: String(sourceScenario.packet_id || ""),
    source_scenario_id: String(sourceScenario.scenario_id || ""),
    style: String(sourceScenario.suggested_interaction_style || ""),
    perception_behavior: definition.perception_behavior,
    perception_label: definition.perception_label,
    confidence: Number(sourceScenario.confidence) || 0,
    confidence_tag: String(sourceScenario.confidence_tag || ""),
    basis: String(sourceScenario.basis || ""),
    reason_trace_refs: Array.isArray(sourceScenario.reason_trace_refs)
      ? sourceScenario.reason_trace_refs.map(String)
      : [],
    history_summary: { ...(sourceScenario.history_summary || {}) },
    visual_profile: profile,
    no_authority: { ...(sourceScenario.no_authority || {}) },
  };
}

function buildPlayback(scenarios, stepMs) {
  return scenarios.map((scenario, index) => ({
    demo_id: scenario.demo_id,
    packet_id: scenario.packet_id,
    start_ms: index * stepMs,
    end_ms: (index + 1) * stepMs,
  }));
}

function buildDebugOverlayRows(scenarios) {
  return scenarios.map((scenario) => ({
    packet_id: scenario.packet_id,
    style: scenario.style,
    confidence: scenario.confidence,
    basis: scenario.basis,
    reason_trace_refs: scenario.reason_trace_refs,
    claim_ceiling: PERCEPTION_DEMO_CLAIM_CEILING,
  }));
}

function buildPspcPerceptionDemo(shim, options) {
  const safeShim = validateShim(shim);
  const settings = options || {};
  const stepMs = Number.isFinite(Number(settings.stepMs)) ? Number(settings.stepMs) : 2400;
  const byPacketId = scenarioByPacketId(safeShim.scenarios);
  const scenarios = SCENARIO_DEFINITIONS.map((definition) => {
    const sourceScenario = byPacketId[definition.packet_id];
    if (!sourceScenario) {
      throw new Error(`missing source scenario ${definition.packet_id}`);
    }
    return compactScenario(definition, sourceScenario);
  });

  const demo = {
    schema_version: "ego_desktop.pspc_perception_demo.v0",
    source: "egodesktop_pspc_visual_shim_v0",
    input_claim_ceiling: String(safeShim.claim_ceiling || ""),
    claim_ceiling: PERCEPTION_DEMO_CLAIM_CEILING,
    allowed_use: "local_perception_demo_only",
    trigger_text: SAME_TRIGGER_TEXT,
    runtime_authority: "none",
    enabled: false,
    mainline_connected: false,
    adapter_created: false,
    runtime_connected: false,
    scenario_order: scenarios.map((scenario) => scenario.demo_id),
    scenarios,
    playback: buildPlayback(scenarios, stepMs),
    recording_mode: {
      fixed_window: true,
      width: 960,
      height: 720,
      deterministic_timing: true,
      deterministic_motion: true,
      seeded_motion: true,
      seed: "pspc_perception_demo_v0",
      step_ms: stepMs,
    },
    debug_overlay: {
      hidden_by_default: true,
      allowed_fields: [
        "packet_id",
        "style",
        "confidence",
        "basis",
        "reason_trace_refs",
        "claim_ceiling",
      ],
      rows: buildDebugOverlayRows(scenarios),
    },
    no_authority: {
      runtime_authority: "none",
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
    side_effects_absent: {
      user_response_mutated: false,
      real_memory_written: false,
      gate_invoked: false,
      approval_invoked: false,
      transport_called: false,
      proactive_triggered: false,
      runtime_registered: false,
      adapter_created: false,
      planner_called: false,
      model_executed: false,
      training_called: false,
      message_sent: false,
    },
    what_this_proves:
      "A local EgoDesktop viewer can present different companion behaviors from different PSPC proposal-hint histories for the same trigger.",
    what_this_does_not_prove:
      "This does not prove PSPC runtime integration, adapter readiness, EgoOperator efficacy, real user benefit, durable memory efficacy, live autonomy, consciousness, subjective experience, real emotion, or stable market appeal.",
    next_allowed_step:
      "Human perception review and Bilibili/Steam market validation scripts only; no EgoOperator adapter or runtime integration.",
  };
  validateNoExecutableFields(demo, EXECUTABLE_OUTPUT_ERROR);
  return demo;
}

module.exports = {
  PERCEPTION_DEMO_CLAIM_CEILING,
  SAME_TRIGGER_TEXT,
  SCENARIO_DEFINITIONS,
  buildPspcPerceptionDemo,
};
