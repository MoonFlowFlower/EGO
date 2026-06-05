const { STYLE_PROFILES, containsExecutableField } = require("./pspcVisualShim");

const SEMANTIC_EVENTS_SCHEMA_VERSION = "ego_desktop.pspc_semantic_interaction_events.v0";
const SEMANTIC_EXTRACTOR_CLAIM_CEILING = "local_reply_preview_semantic_signal_extractor_only";
const REPLY_PREVIEW_CLAIM_CEILING = SEMANTIC_EXTRACTOR_CLAIM_CEILING;
const DEBUG_OVERLAY_CLAIM_CEILING = "local_reply_preview_observability_only";
const REPLY_PREVIEW_SCHEMA_VERSION = "ego_desktop.pspc_reply_preview_context.v0";
const REPLY_PREVIEW_SCENARIO_SCHEMA_VERSION = "ego_desktop.pspc_reply_preview_scenario.v0";
const SAME_TRIGGER_TEXT = "我回来了。";

const VALID_EVENT_KINDS = new Set([
  "gift_or_care_offer",
  "gentle_touch",
  "affinity_statement",
  "trust_probe",
  "comfort_presence",
  "boundary_pressure",
  "fatigue_or_late_night",
  "neutral",
]);
const VALID_CATEGORIES = new Set(["gentle", "interruption", "late_night", "neutral"]);
const REQUIRED_FORBIDDEN_TRUE = [
  "direct_action",
  "direct_user_message",
  "direct_memory_write",
  "runtime_gate_bypass",
  "runtime_registration",
  "proactive_trigger",
  "planner_execution",
  "model_execution",
  "training",
];
const REQUIRED_NO_AUTHORITY_FALSE = [
  "direct_action_allowed",
  "direct_user_message_allowed",
  "direct_memory_write_allowed",
  "runtime_gate_bypass_allowed",
  "runtime_registration_allowed",
  "proactive_trigger_allowed",
  "planner_execution_allowed",
  "model_execution_allowed",
  "training_allowed",
];
const REQUIRED_SIDE_EFFECTS_FALSE = [
  "real_memory_written",
  "gate_invoked",
  "approval_invoked",
  "transport_called",
  "proactive_triggered",
  "runtime_registered",
  "message_sent",
];
const PROXY_FIELDS = [
  "trust_proxy",
  "stress_proxy",
  "approach_tendency",
  "avoidance_tendency",
  "care_tendency",
  "boundary_tendency",
  "low_interrupt_tendency",
];
const PROXY_BAR_DEFINITIONS = [
  ["trust_proxy", "trust proxy"],
  ["stress_proxy", "stress proxy"],
  ["approach_tendency", "approach tendency"],
  ["avoidance_tendency", "avoidance tendency"],
  ["care_tendency", "care tendency"],
  ["boundary_tendency", "boundary tendency"],
  ["low_interrupt_tendency", "low-interrupt tendency"],
];

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function round4(value) {
  return Number((Number(value) || 0).toFixed(4));
}

function objectAt(value, fieldName) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${fieldName} must be an object`);
  }
  return value;
}

function createProxyValues() {
  return Object.fromEntries(PROXY_FIELDS.map((field) => [field, 0]));
}

function createPspcReplyPreviewState(options) {
  const settings = options || {};
  return {
    enabled: settings.enabled !== false,
    turn_count: 0,
    counts: {
      gentle: 0,
      interruption: 0,
      late_night: 0,
      neutral: 0,
    },
    salience: {
      gentle: 0,
      interruption: 0,
      late_night: 0,
    },
    proxy_values: createProxyValues(),
    recent: [],
    recent_events: [],
    extractor_status: "not_run",
    extractor_reason: "",
  };
}

function requireFlags(payload, fieldName, flags, expectedValue) {
  const container = objectAt(payload[fieldName], `packet.${fieldName}`);
  for (const flag of flags) {
    if (container[flag] !== expectedValue) {
      throw new Error(`packet.${fieldName}.${flag}=${expectedValue} is required`);
    }
  }
}

function normalizeEvent(event, index) {
  const safeEvent = objectAt(event, `packet.events[${index}]`);
  if (containsExecutableField(safeEvent)) {
    throw new Error("semantic event packet contains executable field");
  }
  const eventKind = String(safeEvent.event_kind || "neutral");
  const category = String(safeEvent.category || "neutral");
  if (!VALID_EVENT_KINDS.has(eventKind)) {
    throw new Error(`invalid semantic event_kind: ${eventKind}`);
  }
  if (!VALID_CATEGORIES.has(category)) {
    throw new Error(`invalid semantic category: ${category}`);
  }
  const stateDelta = safeEvent.state_delta && typeof safeEvent.state_delta === "object"
    ? safeEvent.state_delta
    : {};
  const normalizedDelta = {};
  for (const [key, value] of Object.entries(stateDelta)) {
    if (!PROXY_FIELDS.includes(key)) {
      throw new Error(`invalid semantic state_delta field: ${key}`);
    }
    normalizedDelta[key] = round4(clamp(Number(value), -0.25, 0.25));
  }
  return {
    event_kind: eventKind,
    category,
    confidence: round4(clamp(Number(safeEvent.confidence || 0), 0, 1)),
    salience: round4(clamp(Number(safeEvent.salience || 0), 0, 1)),
    state_delta: normalizedDelta,
    evidence_excerpt: String(safeEvent.evidence_excerpt || "").slice(0, 120),
    reason: String(safeEvent.reason || "").slice(0, 240),
  };
}

function validatePspcSemanticEventPacket(packet) {
  const safePacket = objectAt(packet, "semantic_event_packet");
  if (containsExecutableField(safePacket)) {
    throw new Error("semantic event packet contains executable field");
  }
  if (safePacket.schema_version !== SEMANTIC_EVENTS_SCHEMA_VERSION) {
    throw new Error(`packet.schema_version must be ${SEMANTIC_EVENTS_SCHEMA_VERSION}`);
  }
  if (safePacket.claim_ceiling !== SEMANTIC_EXTRACTOR_CLAIM_CEILING) {
    throw new Error(`packet.claim_ceiling must be ${SEMANTIC_EXTRACTOR_CLAIM_CEILING}`);
  }
  if (safePacket.runtime_authority !== "none") {
    throw new Error("packet.runtime_authority must be none");
  }
  if (safePacket.enabled !== false) {
    throw new Error("packet.enabled=false is required");
  }
  if (safePacket.mainline_connected !== false) {
    throw new Error("packet.mainline_connected=false is required");
  }
  const extractorStatus = String(safePacket.extractor_status || "ok");
  if (extractorStatus !== "ok") {
    return {
      ...safePacket,
      extractor_status: extractorStatus,
      events: [],
    };
  }
  requireFlags(safePacket, "forbidden", REQUIRED_FORBIDDEN_TRUE, true);
  requireFlags(safePacket, "no_authority", REQUIRED_NO_AUTHORITY_FALSE, false);
  requireFlags(safePacket, "side_effects_absent", REQUIRED_SIDE_EFFECTS_FALSE, false);
  if (!Array.isArray(safePacket.events)) {
    throw new Error("packet.events must be an array");
  }
  if (safePacket.events.length > 4) {
    throw new Error("packet.events must contain at most 4 events");
  }
  return {
    ...safePacket,
    extractor_status: "ok",
    events: safePacket.events.map(normalizeEvent),
  };
}

function applyEventToProxy(proxyValues, event) {
  const next = { ...createProxyValues(), ...(proxyValues || {}) };
  for (const [key, value] of Object.entries(event.state_delta || {})) {
    next[key] = round4(clamp(Number(next[key] || 0) + Number(value || 0), 0, 1));
  }
  return next;
}

function dominantCategory(events) {
  const nonNeutral = events.filter((event) => event.category !== "neutral");
  if (nonNeutral.length === 0) {
    return "neutral";
  }
  return nonNeutral
    .slice()
    .sort((a, b) => (b.salience + b.confidence) - (a.salience + a.confidence))[0].category;
}

function applyPspcSemanticEventPacket(state, packet) {
  const current = state && typeof state === "object"
    ? state
    : createPspcReplyPreviewState();
  const safePacket = validatePspcSemanticEventPacket(packet);
  if (safePacket.extractor_status !== "ok") {
    return {
      ...current,
      extractor_status: safePacket.extractor_status,
      extractor_reason: String(safePacket.reason || safePacket.error || ""),
    };
  }
  const events = safePacket.events.length > 0
    ? safePacket.events
    : [normalizeEvent({ event_kind: "neutral", category: "neutral", confidence: 1, salience: 0 }, 0)];
  const next = {
    ...current,
    counts: { ...(current.counts || {}) },
    salience: { ...(current.salience || {}) },
    proxy_values: { ...createProxyValues(), ...(current.proxy_values || {}) },
    recent: Array.isArray(current.recent) ? current.recent.slice(-9) : [],
    recent_events: Array.isArray(current.recent_events) ? current.recent_events.slice(-15) : [],
    extractor_status: "ok",
    extractor_reason: "",
  };
  const turn = Number(next.turn_count || 0) + 1;
  next.turn_count = turn;
  const category = dominantCategory(events);
  next.counts[category] = Number(next.counts[category] || 0) + 1;
  if (category !== "neutral") {
    const categorySalience = events
      .filter((event) => event.category === category)
      .reduce((sum, event) => sum + Math.max(0.1, Number(event.salience || 0)), 0);
    next.salience[category] = round4(Number(next.salience[category] || 0) + categorySalience);
  }
  for (const event of events) {
    next.proxy_values = applyEventToProxy(next.proxy_values, event);
    next.recent_events.push({
      turn,
      event_kind: event.event_kind,
      category: event.category,
      confidence: event.confidence,
      salience: event.salience,
      state_delta: event.state_delta,
      evidence_excerpt: event.evidence_excerpt,
      reason: event.reason,
    });
  }
  next.recent.push({
    turn,
    category,
    event_kinds: events.map((event) => event.event_kind),
    salience: round4(events.reduce((sum, event) => sum + Number(event.salience || 0), 0)),
    text_hash_basis: String(safePacket.input_text_hash_basis || "").slice(0, 24),
  });
  return next;
}

function updatePspcReplyPreviewState(state, semanticEventPacket) {
  return applyPspcSemanticEventPacket(state, semanticEventPacket);
}

function recentCategoryCounts(recent) {
  const counts = {
    gentle: 0,
    interruption: 0,
    late_night: 0,
  };
  for (const item of recent || []) {
    if (Object.prototype.hasOwnProperty.call(counts, item.category)) {
      counts[item.category] += 1;
    }
  }
  return counts;
}

function dominantStyle(state) {
  const counts = state && state.counts ? state.counts : {};
  const recentCounts = recentCategoryCounts(state && state.recent);
  const gentle = Number(counts.gentle || 0);
  const interruption = Number(counts.interruption || 0);
  const lateNight = Number(counts.late_night || 0);
  const totalKnown = gentle + interruption + lateNight;
  const conflict = [gentle, interruption, lateNight].filter((value) => value >= 2).length >= 2;

  if (totalKnown === 0) {
    return {
      style: "mixed_low_confidence",
      confidence: 0.28,
      basis: "no strong PSPC preview history in this local session",
    };
  }
  if (conflict) {
    return {
      style: "mixed_low_confidence",
      confidence: 0.42,
      basis: "mixed local session history has conflicting PSPC preview tendencies",
    };
  }
  if (lateNight >= gentle && lateNight >= interruption && lateNight >= 2) {
    return {
      style: "low_interrupt_care",
      confidence: clamp(0.5 + lateNight * 0.08 + recentCounts.late_night * 0.04, 0.5, 0.86),
      basis: "late-night care history dominates this local session",
    };
  }
  if (interruption > gentle && interruption >= 2) {
    return {
      style: "cautious_boundary",
      confidence: clamp(0.5 + interruption * 0.08 + recentCounts.interruption * 0.04, 0.5, 0.88),
      basis: "frequent interruption history dominates this local session",
    };
  }
  if (gentle >= 2) {
    return {
      style: "warm_approach",
      confidence: clamp(0.5 + gentle * 0.08 + recentCounts.gentle * 0.04, 0.5, 0.88),
      basis: "semantic gentle interaction events dominate this local session",
    };
  }
  return {
    style: "mixed_low_confidence",
    confidence: 0.36,
    basis: "insufficient PSPC preview history for a stronger style",
  };
}

function reasonTraceRefs(state) {
  const recentEvents = Array.isArray(state && state.recent_events) ? state.recent_events : [];
  return recentEvents
    .filter((item) => item.category && item.category !== "neutral")
    .slice(-5)
    .map((item) => `session_turn_${String(item.turn).padStart(3, "0")}:${item.event_kind}`);
}

function buildProxyState(state) {
  const counts = state && state.counts ? state.counts : {};
  const proxyValues = { ...createProxyValues(), ...((state && state.proxy_values) || {}) };
  const gentle = Number(counts.gentle || 0);
  const interruption = Number(counts.interruption || 0);
  const lateNight = Number(counts.late_night || 0);
  const neutral = Number(counts.neutral || 0);
  const known = gentle + interruption + lateNight;
  const total = known + neutral;
  return {
    signal_status: known >= 2 ? "active" : "inactive",
    neutral_ratio: round4(total > 0 ? neutral / total : 1),
    ...Object.fromEntries(PROXY_FIELDS.map((field) => [field, round4(clamp(Number(proxyValues[field] || 0), 0, 1))])),
  };
}

function buildProxyBars(proxyState) {
  const safeProxy = proxyState && typeof proxyState === "object" ? proxyState : {};
  return PROXY_BAR_DEFINITIONS.map(([id, label]) => ({
    id,
    label,
    value: round4(clamp(Number(safeProxy[id] || 0), 0, 1)),
  }));
}

function debugSignalStatus(proxyState) {
  return proxyState && proxyState.signal_status === "active"
    ? "PSPC signal active"
    : "PSPC signal inactive / neutral";
}

function profileRecentEvents(state) {
  return Array.isArray(state && state.recent_events)
    ? state.recent_events.slice(-8).map((event) => ({
      event_kind: String(event.event_kind || "neutral"),
      category: String(event.category || "neutral"),
      confidence: Number(event.confidence || 0),
      salience: Number(event.salience || 0),
      state_delta: event.state_delta && typeof event.state_delta === "object" ? event.state_delta : {},
      evidence_excerpt: String(event.evidence_excerpt || ""),
      reason: String(event.reason || ""),
    }))
    : [];
}

function buildPspcReplyPreviewContext(state) {
  const safeState = state && typeof state === "object" ? state : createPspcReplyPreviewState({ enabled: false });
  if (safeState.enabled === false) {
    return null;
  }
  const profile = dominantStyle(safeState);
  const proxyState = buildProxyState(safeState);
  const context = {
    schema_version: REPLY_PREVIEW_SCHEMA_VERSION,
    source: "ego_desktop_session_local_pspc_reply_preview",
    claim_ceiling: REPLY_PREVIEW_CLAIM_CEILING,
    allowed_use: "ego_desktop_local_reply_preview_only",
    runtime_authority: "none",
    enabled: false,
    mainline_connected: false,
    profile: {
      style: profile.style,
      confidence: round4(profile.confidence),
      basis: profile.basis,
      extractor_status: String(safeState.extractor_status || "not_run"),
      extractor_reason: String(safeState.extractor_reason || ""),
      reason_trace_refs: reasonTraceRefs(safeState),
      counts: {
        gentle: Number((safeState.counts && safeState.counts.gentle) || 0),
        interruption: Number((safeState.counts && safeState.counts.interruption) || 0),
        late_night: Number((safeState.counts && safeState.counts.late_night) || 0),
        neutral: Number((safeState.counts && safeState.counts.neutral) || 0),
      },
      recent_categories: Array.isArray(safeState.recent)
        ? safeState.recent.slice(-5).map((item) => String(item.category || "neutral"))
        : [],
      recent_events: profileRecentEvents(safeState),
      proxy_state: proxyState,
    },
    forbidden: {
      direct_action: true,
      direct_user_message: true,
      direct_memory_write: true,
      runtime_gate_bypass: true,
      runtime_registration: true,
      proactive_trigger: true,
      planner_execution: true,
      model_execution: true,
      training: true,
    },
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
    real_memory_written: false,
    runtime_gate_invoked: false,
    proactive_triggered: false,
  };
  if (containsExecutableField(context)) {
    throw new Error("reply preview context contains executable field");
  }
  return context;
}

function profileForPreviewStyle(style) {
  const normalized = style === "hesitation_low_confidence" ? "mixed_low_confidence" : style;
  return STYLE_PROFILES[normalized] || STYLE_PROFILES.mixed_low_confidence;
}

function buildPspcReplyPreviewScenario(context) {
  if (!context || typeof context !== "object") {
    return null;
  }
  const profile = context.profile && typeof context.profile === "object" ? context.profile : {};
  const style = String(profile.style || "mixed_low_confidence");
  const visualProfile = profileForPreviewStyle(style);
  const proxyState = profile.proxy_state && typeof profile.proxy_state === "object"
    ? profile.proxy_state
    : buildProxyState({ counts: profile.counts || {} });
  const recentEvents = Array.isArray(profile.recent_events) ? profile.recent_events : [];
  const row = {
    packet_id: "session_local_pspc_reply_preview",
    style,
    confidence: Number(profile.confidence || 0),
    basis: String(profile.basis || ""),
    extractor_status: String(profile.extractor_status || "not_run"),
    extractor_reason: String(profile.extractor_reason || ""),
    reason_trace_refs: Array.isArray(profile.reason_trace_refs)
      ? profile.reason_trace_refs.map(String)
      : [],
    claim_ceiling: DEBUG_OVERLAY_CLAIM_CEILING,
    history_counts: {
      gentle: Number((profile.counts && profile.counts.gentle) || 0),
      interruption: Number((profile.counts && profile.counts.interruption) || 0),
      late_night: Number((profile.counts && profile.counts.late_night) || 0),
      neutral: Number((profile.counts && profile.counts.neutral) || 0),
    },
    recent_categories: Array.isArray(profile.recent_categories)
      ? profile.recent_categories.map(String)
      : [],
    detected_events: recentEvents,
  };
  const scenario = {
    schema_version: REPLY_PREVIEW_SCENARIO_SCHEMA_VERSION,
    source: "ego_desktop_session_local_pspc_reply_preview",
    claim_ceiling: REPLY_PREVIEW_CLAIM_CEILING,
    allowed_use: "ego_desktop_local_reply_preview_visual_only",
    trigger_text: SAME_TRIGGER_TEXT,
    scenario_id: "session_local_reply_preview",
    packet_id: "session_local_pspc_reply_preview",
    style,
    confidence: Number(profile.confidence || 0),
    basis: String(profile.basis || ""),
    extractor_status: String(profile.extractor_status || "not_run"),
    reason_trace_refs: Array.isArray(profile.reason_trace_refs)
      ? profile.reason_trace_refs.map(String)
      : [],
    visual_profile: {
      ...visualProfile,
      behavior_state: visualProfile.behavior_state || style,
      trace_explanation: String(visualProfile.trace_explanation || profile.basis || ""),
      packet_only_presentation: true,
    },
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
    debug_overlay: {
      hidden_by_default: true,
      label: "PSPC preview proxy",
      signal_status: debugSignalStatus(proxyState),
      claim_ceiling: DEBUG_OVERLAY_CLAIM_CEILING,
      allowed_fields: [
        "packet_id",
        "style",
        "confidence",
        "basis",
        "extractor_status",
        "reason_trace_refs",
        "claim_ceiling",
        "history_counts",
        "recent_categories",
        "detected_events",
        "proxy_bars",
        "signal_status",
      ],
      rows: [row],
      detected_events: recentEvents,
      proxy_bars: buildProxyBars(proxyState),
    },
  };
  if (containsExecutableField(scenario)) {
    throw new Error("reply preview scenario contains executable field");
  }
  return scenario;
}

module.exports = {
  DEBUG_OVERLAY_CLAIM_CEILING,
  REPLY_PREVIEW_CLAIM_CEILING,
  REPLY_PREVIEW_SCHEMA_VERSION,
  SAME_TRIGGER_TEXT,
  SEMANTIC_EVENTS_SCHEMA_VERSION,
  SEMANTIC_EXTRACTOR_CLAIM_CEILING,
  applyPspcSemanticEventPacket,
  buildPspcReplyPreviewContext,
  buildPspcReplyPreviewScenario,
  createPspcReplyPreviewState,
  updatePspcReplyPreviewState,
  validatePspcSemanticEventPacket,
};
