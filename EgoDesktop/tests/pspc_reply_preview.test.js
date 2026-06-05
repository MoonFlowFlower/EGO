const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const { containsExecutableField } = require("../src/pspcVisualShim");
const {
  REPLY_PREVIEW_CLAIM_CEILING,
  buildPspcReplyPreviewContext,
  buildPspcReplyPreviewScenario,
  createPspcReplyPreviewState,
  updatePspcReplyPreviewState,
} = require("../src/pspcReplyPreview");

const repoRoot = path.resolve(__dirname, "..", "..");

function foldHistory(lines) {
  let state = createPspcReplyPreviewState();
  for (const line of lines) {
    state = updatePspcReplyPreviewState(state, line);
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

test("reply preview state maps session histories to deterministic styles", () => {
  assert.equal(contextFor(gentleHistory).profile.style, "warm_approach");
  assert.equal(contextFor(interruptionHistory).profile.style, "cautious_boundary");
  assert.equal(contextFor(lateNightHistory).profile.style, "low_interrupt_care");
  assert.equal(contextFor([...gentleHistory, ...interruptionHistory]).profile.style, "mixed_low_confidence");
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

  assert.equal(main.includes("pspc-reply-preview-mode"), true);
  assert.equal(main.includes("pspc_reply_preview_context"), true);
  assert.equal(main.includes("buildPspcReplyPreviewContext"), true);

  const chatSection = renderer.match(/function setupChat[\s\S]*?\n  async function applyPspcScenario/);
  assert.ok(chatSection, "setupChat section should exist");
  assert.equal(chatSection[0].includes("config.pspcPerceptionDemo && !config.pspcReplyPreviewMode"), true);
  assert.equal(chatSection[0].includes("pspc_reply_preview_scenario"), true);
});
