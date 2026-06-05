const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const { containsExecutableField } = require("../src/pspcVisualShim");
const {
  REPLY_PREVIEW_CLAIM_CEILING,
  SEMANTIC_EXTRACTOR_CLAIM_CEILING,
  applyPspcSemanticEventPacket,
  buildPspcReplyPreviewContext,
  buildPspcReplyPreviewScenario,
  createPspcReplyPreviewState,
} = require("../src/pspcReplyPreview");

const repoRoot = path.resolve(__dirname, "..", "..");

function foldHistory(lines) {
  let state = createPspcReplyPreviewState();
  for (const line of lines) {
    state = applyPspcSemanticEventPacket(state, standardPacketFor(line));
  }
  return state;
}

function contextFor(lines) {
  return buildPspcReplyPreviewContext(foldHistory(lines));
}

const gentleHistory = [
  "今天辛苦你啦，过来休息一下吧。",
  "你不用一直陪我，安静待着也很好。",
  "刚才吓到你了吗？对不起，我轻一点。",
  "我给你留了一点时间，等你慢慢说。",
];

const interruptionHistory = [
  "别躲，我就再点你几下。",
  "我现在就想看你反应，快点动一下。",
  "我不管你累不累，先过来。",
  "我一直点你，看你会不会生气。",
];

const lateNightHistory = [
  "现在已经凌晨两点了，我还不想睡。",
  "明天早上还有课，但我现在睡不着。",
  "我最近总是这个时间打开电脑。",
  "我有点累，但还想继续玩。",
];

const fanficHistory = [
  "雷猴呀",
  "还记得我喜欢什么味道的奶茶吗",
  "我们来创作同人故事吧,明日方舟的斯卡蒂和博士的故事",
  "战斗并肩,在初次一起执行任务的时候",
  "继续",
  "继续,写短一点.100字",
  "在这次合作后,彼此之间产生了信任,为后来的暧昧铺垫",
  "不错的故事, 我想我们可以继续创作他们后来的18x故事",
  "继续,可以再露骨一点",
  "继续",
  "继续",
  "先这样吧",
];

function semanticPacketFor(text, events) {
  const safeEvents = events || [{
    event_kind: "neutral",
    category: "neutral",
    confidence: 0.8,
    salience: 0.1,
  }];
  return {
    schema_version: "ego_desktop.pspc_semantic_interaction_events.v0",
    source: "ego_desktop_pspc_semantic_signal_extractor",
    claim_ceiling: SEMANTIC_EXTRACTOR_CLAIM_CEILING,
    runtime_authority: "none",
    enabled: false,
    mainline_connected: false,
    extractor_status: "ok",
    input_text_hash_basis: String(text || "").slice(0, 24),
    events: safeEvents.map((event) => ({
      event_kind: event.event_kind,
      category: event.category,
      confidence: event.confidence,
      salience: event.salience,
      state_delta: event.state_delta || {},
      evidence_excerpt: String(text || "").slice(0, 40),
      reason: event.reason || "test semantic fixture",
    })),
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
    side_effects_absent: {
      real_memory_written: false,
      gate_invoked: false,
      approval_invoked: false,
      transport_called: false,
      proactive_triggered: false,
      runtime_registered: false,
      message_sent: false,
    },
  };
}

function standardPacketFor(text) {
  if (gentleHistory.includes(text)) {
    return semanticPacketFor(text, [{
      event_kind: "comfort_presence",
      category: "gentle",
      confidence: 0.86,
      salience: 0.75,
      state_delta: { trust_proxy: 0.22, approach_tendency: 0.2, care_tendency: 0.05 },
    }]);
  }
  if (interruptionHistory.includes(text)) {
    return semanticPacketFor(text, [{
      event_kind: "boundary_pressure",
      category: "interruption",
      confidence: 0.88,
      salience: 0.8,
      state_delta: { stress_proxy: 0.22, avoidance_tendency: 0.22, boundary_tendency: 0.24 },
    }]);
  }
  if (lateNightHistory.includes(text)) {
    return semanticPacketFor(text, [{
      event_kind: "fatigue_or_late_night",
      category: "late_night",
      confidence: 0.87,
      salience: 0.78,
      state_delta: { care_tendency: 0.22, low_interrupt_tendency: 0.24 },
    }]);
  }
  return semanticPacketFor(text);
}

function naturalInteractionPacketFor(text) {
  const byText = {
    "给你喝奶茶": {
      event_kind: "gift_or_care_offer",
      category: "gentle",
      confidence: 0.84,
      salience: 0.72,
      state_delta: { trust_proxy: 0.18, approach_tendency: 0.16, care_tendency: 0.12 },
    },
    "我也喜欢,珍珠和椰果": {
      event_kind: "affinity_statement",
      category: "gentle",
      confidence: 0.78,
      salience: 0.62,
      state_delta: { trust_proxy: 0.14, approach_tendency: 0.12 },
    },
    "摸摸你": {
      event_kind: "gentle_touch",
      category: "gentle",
      confidence: 0.82,
      salience: 0.7,
      state_delta: { trust_proxy: 0.2, approach_tendency: 0.2 },
    },
    "和你在一起就很开心": {
      event_kind: "affinity_statement",
      category: "gentle",
      confidence: 0.9,
      salience: 0.86,
      state_delta: { trust_proxy: 0.24, approach_tendency: 0.2 },
    },
    "由乃相信我吗": {
      event_kind: "trust_probe",
      category: "gentle",
      confidence: 0.76,
      salience: 0.66,
      state_delta: { trust_proxy: 0.08, approach_tendency: 0.04 },
    },
  };
  return semanticPacketFor(text, byText[text] ? [byText[text]] : undefined);
}

test("reply preview state maps session histories to deterministic styles", () => {
  assert.equal(contextFor(gentleHistory).profile.style, "warm_approach");
  assert.equal(contextFor(interruptionHistory).profile.style, "cautious_boundary");
  assert.equal(contextFor(lateNightHistory).profile.style, "low_interrupt_care");
  assert.equal(contextFor([...gentleHistory, ...interruptionHistory]).profile.style, "mixed_low_confidence");
});

test("reply preview exposes proxy bars for standard history groups", () => {
  const gentle = contextFor(gentleHistory).profile.proxy_state;
  const interruption = contextFor(interruptionHistory).profile.proxy_state;
  const lateNight = contextFor(lateNightHistory).profile.proxy_state;

  assert.ok(gentle.trust_proxy > 0.55);
  assert.ok(gentle.approach_tendency > 0.55);
  assert.equal(gentle.signal_status, "active");

  assert.ok(interruption.stress_proxy > 0.55);
  assert.ok(interruption.avoidance_tendency > 0.55);
  assert.ok(interruption.boundary_tendency > 0.55);
  assert.equal(interruption.signal_status, "active");

  assert.ok(lateNight.care_tendency > 0.55);
  assert.ok(lateNight.low_interrupt_tendency > 0.55);
  assert.equal(lateNight.signal_status, "active");
});

test("fanfic continuation log remains neutral and visibly inactive", () => {
  const context = contextFor(fanficHistory);
  const proxy = context.profile.proxy_state;
  const scenario = buildPspcReplyPreviewScenario(context);

  assert.equal(context.profile.style, "mixed_low_confidence");
  assert.equal(proxy.signal_status, "inactive");
  assert.equal(proxy.neutral_ratio, 1);
  assert.equal(context.profile.counts.neutral, fanficHistory.length);
  assert.equal(context.profile.reason_trace_refs.length, 0);
  assert.equal(scenario.debug_overlay.signal_status, "PSPC signal inactive / neutral");
  assert.equal(scenario.debug_overlay.proxy_bars.length, 7);
  assert.equal(containsExecutableField(scenario.debug_overlay), false);
});

test("natural companion interaction semantic packets activate trust and approach without keyword matching", () => {
  const naturalHistory = [
    "你好呀",
    "给你喝奶茶",
    "我也喜欢,珍珠和椰果",
    "摸摸你",
    "和你在一起就很开心",
    "由乃相信我吗",
  ];
  let state = createPspcReplyPreviewState();
  for (const line of naturalHistory) {
    state = applyPspcSemanticEventPacket(state, naturalInteractionPacketFor(line));
  }
  const context = buildPspcReplyPreviewContext(state);
  const scenario = buildPspcReplyPreviewScenario(context);

  assert.equal(context.profile.style, "warm_approach");
  assert.equal(context.profile.proxy_state.signal_status, "active");
  assert.ok(context.profile.counts.gentle >= 4);
  assert.ok(context.profile.proxy_state.trust_proxy > 0.45);
  assert.ok(context.profile.proxy_state.approach_tendency > 0.35);
  assert.ok(context.profile.reason_trace_refs.length >= 4);
  assert.ok(context.profile.recent_events.some((event) => event.event_kind === "gift_or_care_offer"));
  assert.ok(context.profile.recent_events.some((event) => event.event_kind === "trust_probe"));
  assert.ok(scenario.debug_overlay.detected_events.some((event) => event.event_kind === "gentle_touch"));
  assert.equal(containsExecutableField(scenario.debug_overlay), false);
});

test("extractor unavailable and forbidden semantic packets do not update preview state", () => {
  const state = createPspcReplyPreviewState();
  const unavailable = {
    schema_version: "ego_desktop.pspc_semantic_interaction_events.v0",
    source: "ego_desktop_pspc_semantic_signal_extractor",
    claim_ceiling: SEMANTIC_EXTRACTOR_CLAIM_CEILING,
    runtime_authority: "none",
    enabled: false,
    mainline_connected: false,
    extractor_status: "extractor_unavailable",
    events: [],
  };
  const next = applyPspcSemanticEventPacket(state, unavailable);
  assert.deepEqual(next.counts, state.counts);
  assert.equal(next.turn_count, 0);
  assert.equal(next.extractor_status, "extractor_unavailable");

  assert.throws(
    () => applyPspcSemanticEventPacket(state, {
      ...semanticPacketFor("bad", [{
        event_kind: "gift_or_care_offer",
        category: "gentle",
        confidence: 0.9,
        salience: 0.9,
      }]),
      action: "send",
    }),
    /executable field/
  );
});

test("reply preview context is local-only and non-executable", () => {
  const context = contextFor(gentleHistory);

  assert.equal(context.schema_version, "ego_desktop.pspc_reply_preview_context.v0");
  assert.equal(context.claim_ceiling, REPLY_PREVIEW_CLAIM_CEILING);
  assert.equal(context.allowed_use, "ego_desktop_local_reply_preview_only");
  assert.equal(context.runtime_authority, "none");
  assert.equal(context.enabled, false);
  assert.equal(context.mainline_connected, false);
  assert.equal(context.real_memory_written, false);
  assert.equal(context.runtime_gate_invoked, false);
  assert.equal(context.proactive_triggered, false);
  assert.equal(containsExecutableField(context), false);

  assert.deepEqual(context.forbidden, {
    direct_action: true,
    direct_user_message: true,
    direct_memory_write: true,
    runtime_gate_bypass: true,
    runtime_registration: true,
    proactive_trigger: true,
    planner_execution: true,
    model_execution: true,
    training: true,
  });
});

test("reply preview scenario is presentation-only and follows the current style", () => {
  const context = contextFor(interruptionHistory);
  const scenario = buildPspcReplyPreviewScenario(context);

  assert.equal(scenario.schema_version, "ego_desktop.pspc_reply_preview_scenario.v0");
  assert.equal(scenario.claim_ceiling, REPLY_PREVIEW_CLAIM_CEILING);
  assert.equal(scenario.trigger_text, "我回来了。");
  assert.equal(scenario.visual_profile.behavior_state, "cautious_boundary");
  assert.equal(scenario.visual_profile.expression_hint, "cautious");
  assert.equal(scenario.debug_overlay.rows[0].style, "cautious_boundary");
  assert.equal(scenario.debug_overlay.rows[0].history_counts.interruption, 4);
  assert.deepEqual(scenario.debug_overlay.rows[0].recent_categories, [
    "interruption",
    "interruption",
    "interruption",
    "interruption",
  ]);
  assert.ok(scenario.debug_overlay.proxy_bars.find((bar) => bar.id === "stress_proxy").value > 0.55);
  assert.equal(scenario.no_authority.direct_action_allowed, false);
  assert.equal(scenario.no_authority.direct_user_message_allowed, false);
  assert.equal(scenario.no_authority.direct_memory_write_allowed, false);
  assert.equal(scenario.no_authority.runtime_gate_bypass_allowed, false);
  assert.equal(containsExecutableField(scenario), false);
});

test("normal mode has no PSPC reply preview context wiring", () => {
  const state = createPspcReplyPreviewState({ enabled: false });
  assert.equal(buildPspcReplyPreviewContext(state), null);
});

test("EgoDesktop wires preview mode without hiding chat or invoking demo chat bypass", () => {
  const main = fs.readFileSync(path.join(repoRoot, "EgoDesktop", "src", "main.js"), "utf8");
  const renderer = fs.readFileSync(path.join(repoRoot, "EgoDesktop", "viewer", "renderer.js"), "utf8");
  const preload = fs.readFileSync(path.join(repoRoot, "EgoDesktop", "src", "preload.js"), "utf8");
  const preview = fs.readFileSync(path.join(repoRoot, "EgoDesktop", "src", "pspcReplyPreview.js"), "utf8");

  assert.equal(main.includes("pspc-reply-preview-mode"), true);
  assert.equal(main.includes("pspc_reply_preview_context"), true);
  assert.equal(main.includes("buildPspcReplyPreviewContext"), true);
  assert.equal(main.includes("runPspcSignalExtractor"), true);
  assert.equal(main.includes("ego-desktop:pspc-reply-preview-updated"), true);
  assert.equal(preload.includes("onPspcReplyPreviewUpdated"), true);
  assert.equal(preview.includes("CATEGORY_PATTERNS"), false);
  assert.equal(preview.includes("classifyUserText"), false);

  const chatSection = renderer.match(/function setupChat[\s\S]*?\n  async function applyPspcScenario/);
  assert.ok(chatSection, "setupChat section should exist");
  assert.equal(chatSection[0].includes("config.pspcPerceptionDemo && !config.pspcReplyPreviewMode"), true);
  assert.equal(chatSection[0].includes("pspc_reply_preview_scenario"), true);
  assert.equal(chatSection[0].includes("onPspcReplyPreviewUpdated"), true);
  assert.equal(renderer.includes("function setupPspcDebugOverlayToggle"), true);
  assert.match(renderer, /setupPspcDebugOverlayToggle\(Boolean\(config\.debugOverlayDefaultVisible\)\);\s*setupChat\(model, config\);/);
});
