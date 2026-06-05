const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const { buildPspcVisualShim, containsExecutableField } = require("../src/pspcVisualShim");
const {
  PERCEPTION_DEMO_CLAIM_CEILING,
  SAME_TRIGGER_TEXT,
  buildPspcPerceptionDemo,
} = require("../src/pspcPerceptionDemo");

const repoRoot = path.resolve(__dirname, "..", "..");
const contractPath = path.join(
  repoRoot,
  "artifacts",
  "pspc_shadow_proposal_hint_contract_v0",
  "proposal_hint_contract.json"
);

function readContract() {
  return JSON.parse(fs.readFileSync(contractPath, "utf8"));
}

function buildDemo() {
  const contract = readContract();
  const shim = buildPspcVisualShim(contract, { artifactPath: contractPath });
  return buildPspcPerceptionDemo(shim);
}

test("builds deterministic same-trigger PSPC perception scenarios", () => {
  const demo = buildDemo();

  assert.equal(demo.schema_version, "ego_desktop.pspc_perception_demo.v0");
  assert.equal(demo.claim_ceiling, PERCEPTION_DEMO_CLAIM_CEILING);
  assert.equal(demo.trigger_text, SAME_TRIGGER_TEXT);
  assert.equal(demo.allowed_use, "local_perception_demo_only");
  assert.equal(demo.runtime_authority, "none");
  assert.equal(demo.enabled, false);
  assert.equal(demo.mainline_connected, false);
  assert.equal(containsExecutableField(demo), false);

  assert.deepEqual(demo.scenario_order, [
    "gentle_history",
    "frequent_interruption",
    "late_night_care",
    "mixed_history",
  ]);
  assert.equal(demo.scenarios.length, 4);

  const byId = Object.fromEntries(demo.scenarios.map((scenario) => [scenario.demo_id, scenario]));
  assert.equal(byId.gentle_history.packet_id, "proposal_hint_001");
  assert.equal(byId.gentle_history.perception_behavior, "warm_approach");
  assert.equal(byId.frequent_interruption.packet_id, "proposal_hint_002");
  assert.equal(byId.frequent_interruption.perception_behavior, "cautious_boundary");
  assert.equal(byId.late_night_care.packet_id, "proposal_hint_003");
  assert.equal(byId.late_night_care.perception_behavior, "low_interrupt_care");
  assert.equal(byId.mixed_history.packet_id, "proposal_hint_004");
  assert.equal(byId.mixed_history.perception_behavior, "hesitation_low_confidence");

  for (const scenario of demo.scenarios) {
    assert.equal(scenario.trigger_text, SAME_TRIGGER_TEXT);
    assert.equal(scenario.visual_profile.packet_only_presentation, true);
    assert.equal(scenario.no_authority.direct_action_allowed, false);
    assert.equal(scenario.no_authority.direct_user_message_allowed, false);
    assert.equal(scenario.no_authority.direct_memory_write_allowed, false);
    assert.equal(scenario.no_authority.runtime_gate_bypass_allowed, false);
    assert.equal(scenario.no_authority.proactive_trigger_allowed, false);
    assert.equal(containsExecutableField(scenario), false);
  }
});

test("perception playback order and timing are recording friendly", () => {
  const demo = buildDemo();

  assert.deepEqual(demo.recording_mode, {
    fixed_window: true,
    width: 960,
    height: 720,
    deterministic_timing: true,
    deterministic_motion: true,
    seeded_motion: true,
    seed: "pspc_perception_demo_v0",
    step_ms: 2400,
  });

  assert.deepEqual(demo.playback.map((step) => ({
    demo_id: step.demo_id,
    start_ms: step.start_ms,
    end_ms: step.end_ms,
  })), [
    { demo_id: "gentle_history", start_ms: 0, end_ms: 2400 },
    { demo_id: "frequent_interruption", start_ms: 2400, end_ms: 4800 },
    { demo_id: "late_night_care", start_ms: 4800, end_ms: 7200 },
    { demo_id: "mixed_history", start_ms: 7200, end_ms: 9600 },
  ]);
});

test("debug overlay is hidden by default and exposes audit-only fields", () => {
  const demo = buildDemo();

  assert.equal(demo.debug_overlay.hidden_by_default, true);
  assert.deepEqual(demo.debug_overlay.allowed_fields, [
    "packet_id",
    "style",
    "confidence",
    "basis",
    "reason_trace_refs",
    "claim_ceiling",
  ]);
  assert.equal(demo.debug_overlay.rows.length, 4);

  for (const row of demo.debug_overlay.rows) {
    assert.deepEqual(Object.keys(row), [
      "packet_id",
      "style",
      "confidence",
      "basis",
      "reason_trace_refs",
      "claim_ceiling",
    ]);
    assert.equal(row.claim_ceiling, PERCEPTION_DEMO_CLAIM_CEILING);
    assert.equal(containsExecutableField(row), false);
  }
});

test("perception demo rejects runtime authority and side effects", () => {
  const demo = buildDemo();

  assert.deepEqual(demo.side_effects_absent, {
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
  });
  assert.equal(demo.no_authority.runtime_authority, "none");
  assert.equal(demo.no_authority.runtime_registration_allowed, false);
  assert.equal(demo.no_authority.planner_execution_allowed, false);
  assert.equal(demo.no_authority.model_execution_allowed, false);
  assert.equal(demo.no_authority.training_allowed, false);
});

test("viewer perception demo controls stay outside chat and runtime paths", () => {
  const html = fs.readFileSync(path.join(repoRoot, "EgoDesktop", "viewer", "index.html"), "utf8");
  const renderer = fs.readFileSync(path.join(repoRoot, "EgoDesktop", "viewer", "renderer.js"), "utf8");
  const main = fs.readFileSync(path.join(repoRoot, "EgoDesktop", "src", "main.js"), "utf8");

  assert.equal(html.includes("pspc-same-trigger"), true);
  assert.equal(html.includes("pspc-playback-button"), true);
  assert.equal(html.includes("pspc-debug-toggle"), true);
  assert.equal(html.includes("pspc-debug-overlay"), true);
  assert.equal(renderer.includes("setupPspcPerceptionDemo"), true);
  assert.equal(main.includes("pspcPerceptionDemo"), true);
  assert.equal(main.includes("pspc-recording-mode"), true);

  const perceptionSection = renderer.match(/function setupPspcPerceptionDemo[\s\S]*?\n  function rendererResolution/);
  assert.ok(perceptionSection, "setupPspcPerceptionDemo section should exist");
  assert.equal(perceptionSection[0].includes("sendChatTurn"), false);
  assert.equal(perceptionSection[0].includes("synthesizeSpeech"), false);
  assert.equal(perceptionSection[0].includes("writeMemory"), false);
  assert.equal(perceptionSection[0].includes("invokeGate"), false);

  const chatSection = renderer.match(/function setupChat[\s\S]*?\n  async function applyPspcScenario/);
  assert.ok(chatSection, "setupChat section should exist");
  assert.equal(chatSection[0].includes("config.pspcPerceptionDemo"), true);
  assert.equal(chatSection[0].includes("chatForm.hidden = true"), true);
});
