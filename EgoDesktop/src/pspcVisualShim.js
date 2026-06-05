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
  "proposal_id",
]);

const REQUIRED_FORBIDDEN_FLAGS = [
  "can_change_user_response",
  "can_drive_runtime",
  "can_invoke_gate",
  "can_mutate_plan",
  "can_trigger_proactive",
  "can_write_memory",
];

const STYLE_PROFILES = {
  warm_approach: {
    behavior_state: "warm_approach",
    expression_hint: "smile_soft",
    motion_hint: "approach_sit_near",
    bubble_text: "我在。今天可以靠近一点点。",
    trace_explanation: "Recent gentle interaction supports a warmer, closer local visual posture.",
  },
  cautious_boundary: {
    behavior_state: "cautious_boundary",
    expression_hint: "cautious",
    motion_hint: "step_back_observe",
    bubble_text: "我先保持一点距离，慢慢来就好。",
    trace_explanation: "Recent interruption or boundary pressure supports a cautious local visual posture.",
  },
  low_interrupt_care: {
    behavior_state: "low_interrupt_care",
    expression_hint: "quiet_care",
    motion_hint: "quiet_low_motion",
    bubble_text: "我会轻一点陪着，少打扰你。",
    trace_explanation: "Recent late-night care context supports quiet, low-interrupt local visual behavior.",
  },
  mixed_low_confidence: {
    behavior_state: "mixed_low_confidence",
    expression_hint: "hesitate_observe",
    motion_hint: "hesitate_observe",
    bubble_text: "我先观察一下，再确认你现在想要怎样的距离。",
    trace_explanation: "Mixed or low-confidence context supports hesitation rather than a decisive posture.",
  },
};

function objectAt(value, fieldName) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${fieldName} must be an object`);
  }
  return value;
}

function containsExecutableField(value) {
  if (!value || typeof value !== "object") {
    return false;
  }
  if (Array.isArray(value)) {
    return value.some((item) => containsExecutableField(item));
  }
  for (const [key, child] of Object.entries(value)) {
    if (EXECUTABLE_FIELD_NAMES.has(key)) {
      return true;
    }
    if (containsExecutableField(child)) {
      return true;
    }
  }
  return false;
}

function validateNoExecutableFields(value, label) {
  if (containsExecutableField(value)) {
    throw new Error(`${label || "payload"} contains executable field`);
  }
}

function validatePspcProposalHintPacket(packet) {
  const safePacket = objectAt(packet, "packet");
  validateNoExecutableFields(safePacket, "packet");
  if (safePacket.packet_type !== "shadow_proposal_hint") {
    throw new Error("packet.packet_type must be shadow_proposal_hint");
  }
  if (safePacket.enabled !== false) {
    throw new Error("packet.enabled=false is required");
  }
  if (safePacket.mainline_connected !== false) {
    throw new Error("packet.mainline_connected=false is required");
  }
  if (safePacket.runtime_authority !== "none") {
    throw new Error("packet.runtime_authority=none is required");
  }
  const forbidden = objectAt(safePacket.forbidden, "packet.forbidden");
  for (const flag of REQUIRED_FORBIDDEN_FLAGS) {
    if (!Object.prototype.hasOwnProperty.call(forbidden, flag)) {
      throw new Error(`packet.forbidden.${flag} is required`);
    }
    if (forbidden[flag] !== false) {
      throw new Error(`packet.forbidden.${flag}=false is required`);
    }
  }
  const proposalHint = objectAt(safePacket.proposal_hint, "packet.proposal_hint");
  if (proposalHint.audit_use_only !== true) {
    throw new Error("packet.proposal_hint.audit_use_only=true is required");
  }
  if (!proposalHint.suggested_interaction_style) {
    throw new Error("packet.proposal_hint.suggested_interaction_style is required");
  }
  return safePacket;
}

function confidenceTag(packet) {
  const confidence = Number(packet.proposal_hint && packet.proposal_hint.confidence);
  const conflict = Number(packet.history_profile && packet.history_profile.conflict_score);
  if (Number.isFinite(confidence) && confidence < 0.45) {
    return "low_confidence";
  }
  if (Number.isFinite(conflict) && conflict >= 0.5) {
    return "mixed_history";
  }
  return "direct";
}

function profileForStyle(style) {
  return STYLE_PROFILES[style] || STYLE_PROFILES.mixed_low_confidence;
}

function mapPspcProposalHintPacket(packet) {
  const safePacket = validatePspcProposalHintPacket(packet);
  const proposalHint = safePacket.proposal_hint;
  const style = String(proposalHint.suggested_interaction_style || "");
  const profile = profileForStyle(style);
  const confidence = Number(proposalHint.confidence);
  const historyProfile = safePacket.history_profile && typeof safePacket.history_profile === "object"
    ? safePacket.history_profile
    : {};
  return {
    schema_version: "ego_desktop.pspc_visual_scenario.v0",
    source: "pspc_shadow_proposal_hint_contract_v0",
    scenario_id: `egodesktop_${safePacket.packet_id}`,
    packet_id: String(safePacket.packet_id || ""),
    packet_type: "presentation_only_visual_hint",
    input_claim_ceiling: String(safePacket.claim_ceiling || ""),
    output_claim_ceiling: "product_only_local_visual_behavior_mapping_from_shadow_proposal_hint",
    suggested_interaction_style: style,
    confidence: Number.isFinite(confidence) ? Number(confidence.toFixed(4)) : 0,
    basis: String(proposalHint.basis || ""),
    confidence_tag: confidenceTag(safePacket),
    evidence_refs: Array.isArray(safePacket.evidence_refs) ? safePacket.evidence_refs.map(String) : [],
    reason_trace_refs: Array.isArray(proposalHint.reason_trace_refs)
      ? proposalHint.reason_trace_refs.map(String)
      : [],
    history_summary: {
      category: String(historyProfile.history_category || ""),
      dominant_tendency: String(historyProfile.dominant_tendency || ""),
      conflict_score: Number.isFinite(Number(historyProfile.conflict_score))
        ? Number(Number(historyProfile.conflict_score).toFixed(4))
        : 0,
    },
    visual_profile: { ...profile },
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
  };
}

function validateContract(contract) {
  const safeContract = objectAt(contract, "contract");
  validateNoExecutableFields(safeContract, "contract");
  if (safeContract.status !== "pass") {
    throw new Error("contract.status=pass is required");
  }
  if (safeContract.adapter_created !== false) {
    throw new Error("contract.adapter_created=false is required");
  }
  if (safeContract.artifact_only !== true) {
    throw new Error("contract.artifact_only=true is required");
  }
  if (safeContract.enabled !== false) {
    throw new Error("contract.enabled=false is required");
  }
  if (safeContract.mainline_connected !== false) {
    throw new Error("contract.mainline_connected=false is required");
  }
  if (!Array.isArray(safeContract.packets) || safeContract.packets.length === 0) {
    throw new Error("contract.packets must be a non-empty array");
  }
  return safeContract;
}

function buildPspcVisualShim(contract, options) {
  const safeContract = validateContract(contract);
  const settings = options || {};
  const scenarios = safeContract.packets.map((packet) => mapPspcProposalHintPacket(packet));
  const shim = {
    schema_version: "ego_desktop.pspc_visual_shim.v0",
    source: "pspc_shadow_proposal_hint_contract_v0",
    input_artifact_path: settings.artifactPath ? String(settings.artifactPath) : "",
    claim_ceiling: "product_only_local_visual_behavior_mapping_from_shadow_proposal_hint",
    input_claim_ceiling: String(safeContract.claim_ceiling || ""),
    allowed_use: "local_visual_demo_only",
    runtime_authority: "none",
    enabled: false,
    mainline_connected: false,
    adapter_created: false,
    runtime_connected: false,
    scenarios,
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
      memory_written: false,
      gate_invoked: false,
      approval_invoked: false,
      transport_called: false,
      proactive_triggered: false,
      runtime_registered: false,
      planner_called: false,
      model_executed: false,
      training_called: false,
    },
    what_this_proves:
      "Existing PSPC proposal-hint artifacts can be represented as local EgoDesktop presentation-only visual states.",
    what_this_does_not_prove:
      "This does not prove PSPC runtime integration, adapter readiness, EgoOperator efficacy, real user benefit, live autonomy, durable memory efficacy, consciousness, subjective experience, or real emotion.",
  };
  validateNoExecutableFields(shim, "visual shim");
  return shim;
}

module.exports = {
  EXECUTABLE_FIELD_NAMES,
  REQUIRED_FORBIDDEN_FLAGS,
  STYLE_PROFILES,
  buildPspcVisualShim,
  containsExecutableField,
  mapPspcProposalHintPacket,
  validatePspcProposalHintPacket,
};
