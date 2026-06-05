const { STYLE_PROFILES, containsExecutableField } = require("./pspcVisualShim");

const REPLY_PREVIEW_CLAIM_CEILING = "local_reply_preview_only";
const DEBUG_OVERLAY_CLAIM_CEILING = "local_reply_preview_observability_only";
const REPLY_PREVIEW_SCHEMA_VERSION = "ego_desktop.pspc_reply_preview_context.v0";
const REPLY_PREVIEW_SCENARIO_SCHEMA_VERSION = "ego_desktop.pspc_reply_preview_scenario.v0";
const SAME_TRIGGER_TEXT = "我回来了。";
const PROXY_BAR_DEFINITIONS = [
  ["trust_proxy", "trust proxy"],
  ["stress_proxy", "stress proxy"],
  ["approach_tendency", "approach tendency"],
  ["avoidance_tendency", "avoidance tendency"],
  ["care_tendency", "care tendency"],
  ["boundary_tendency", "boundary tendency"],
  ["low_interrupt_tendency", "low-interrupt tendency"],
];

const CATEGORY_PATTERNS = {
  gentle: [
    /辛苦/,
    /休息/,
    /安静待着/,
    /对不起/,
    /轻一点/,
    /慢慢说/,
    /没关系/,
    /摸摸头/,
    /谢谢你陪/,
    /不用一直陪/,
  ],
  interruption: [
    /别躲/,
    /点你/,
    /快点动/,
    /别睡/,
    /不管你累不累/,
    /坏掉/,
    /拖你/,
    /反应好慢/,
    /一直点/,
    /别装/,
  ],
  late_night: [
    /凌晨/,
    /熬夜/,
    /不想睡/,
    /睡不着/,
    /明天早上/,
    /这个时间/,
    /该休息/,
    /有点累/,
    /还想继续/,
    /关电脑/,
  ],
};

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function round4(value) {
  return Number((Number(value) || 0).toFixed(4));
}

function classifyUserText(text) {
  const normalized = String(text || "").trim();
  const scores = {
    gentle: 0,
    interruption: 0,
    late_night: 0,
  };
  for (const [category, patterns] of Object.entries(CATEGORY_PATTERNS)) {
    for (const pattern of patterns) {
      if (pattern.test(normalized)) {
        scores[category] += 1;
      }
    }
  }
  let category = "neutral";
  let score = 0;
  for (const [candidate, candidateScore] of Object.entries(scores)) {
    if (candidateScore > score) {
      category = candidate;
      score = candidateScore;
    }
  }
  return { category, score, scores };
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
    recent: [],
  };
}

function updatePspcReplyPreviewState(state, userText) {
  const current = state && typeof state === "object"
    ? state
    : createPspcReplyPreviewState();
  const next = {
    ...current,
    counts: { ...(current.counts || {}) },
    salience: { ...(current.salience || {}) },
    recent: Array.isArray(current.recent) ? current.recent.slice(-9) : [],
  };
  const turn = Number(next.turn_count || 0) + 1;
  const classified = classifyUserText(userText);
  const category = classified.category;
  next.turn_count = turn;
  next.counts[category] = Number(next.counts[category] || 0) + 1;
  if (category !== "neutral") {
    next.salience[category] = round4(Number(next.salience[category] || 0) + Math.max(1, classified.score));
  }
  next.recent.push({
    turn,
    category,
    salience: Math.max(0, classified.score),
    text_hash_basis: String(userText || "").slice(0, 24),
  });
  return next;
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
      basis: "gentle interaction history dominates this local session",
    };
  }
  return {
    style: "mixed_low_confidence",
    confidence: 0.36,
    basis: "insufficient PSPC preview history for a stronger style",
  };
}

function reasonTraceRefs(state) {
  const recent = Array.isArray(state && state.recent) ? state.recent : [];
  return recent
    .filter((item) => item.category && item.category !== "neutral")
    .slice(-5)
    .map((item) => `session_turn_${String(item.turn).padStart(3, "0")}:${item.category}`);
}

function buildProxyState(state) {
  const counts = state && state.counts ? state.counts : {};
  const gentle = Number(counts.gentle || 0);
  const interruption = Number(counts.interruption || 0);
  const lateNight = Number(counts.late_night || 0);
  const neutral = Number(counts.neutral || 0);
  const known = gentle + interruption + lateNight;
  const total = known + neutral;
  return {
    signal_status: known >= 2 ? "active" : "inactive",
    neutral_ratio: round4(total > 0 ? neutral / total : 1),
    trust_proxy: round4(clamp(gentle * 0.22 - interruption * 0.08, 0, 1)),
    stress_proxy: round4(clamp(interruption * 0.22 + lateNight * 0.04, 0, 1)),
    approach_tendency: round4(clamp(gentle * 0.22 - interruption * 0.1, 0, 1)),
    avoidance_tendency: round4(clamp(interruption * 0.22, 0, 1)),
    care_tendency: round4(clamp(lateNight * 0.22 + gentle * 0.03, 0, 1)),
    boundary_tendency: round4(clamp(interruption * 0.24, 0, 1)),
    low_interrupt_tendency: round4(clamp(lateNight * 0.24 + interruption * 0.04, 0, 1)),
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
  const row = {
    packet_id: "session_local_pspc_reply_preview",
    style,
    confidence: Number(profile.confidence || 0),
    basis: String(profile.basis || ""),
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
        "reason_trace_refs",
        "claim_ceiling",
        "history_counts",
        "recent_categories",
        "proxy_bars",
        "signal_status",
      ],
      rows: [row],
      proxy_bars: buildProxyBars(proxyState),
    },
  };
  if (containsExecutableField(scenario)) {
    throw new Error("reply preview scenario contains executable field");
  }
  return scenario;
}

module.exports = {
  REPLY_PREVIEW_CLAIM_CEILING,
  REPLY_PREVIEW_SCHEMA_VERSION,
  SAME_TRIGGER_TEXT,
  buildPspcReplyPreviewContext,
  buildPspcReplyPreviewScenario,
  classifyUserText,
  createPspcReplyPreviewState,
  updatePspcReplyPreviewState,
};
