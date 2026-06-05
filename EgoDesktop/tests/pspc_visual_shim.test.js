const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const {
  buildPspcVisualShim,
  mapPspcProposalHintPacket,
  validatePspcProposalHintPacket,
  containsExecutableField,
} = require("../src/pspcVisualShim");

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

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

test("maps all PSPC proposal-hint packets into local visual states", () => {
  const contract = readContract();
  const shim = buildPspcVisualShim(contract, { artifactPath: contractPath });

  assert.equal(shim.schema_version, "ego_desktop.pspc_visual_shim.v0");
  assert.equal(shim.claim_ceiling, "product_only_local_visual_behavior_mapping_from_shadow_proposal_hint");
  assert.equal(shim.runtime_authority, "none");
  assert.equal(shim.enabled, false);
  assert.equal(shim.mainline_connected, false);
  assert.equal(shim.scenarios.length, 7);
  assert.equal(containsExecutableField(shim), false);

  const byPacketId = Object.fromEntries(shim.scenarios.map((scenario) => [scenario.packet_id, scenario]));
  assert.equal(byPacketId.proposal_hint_001.visual_profile.behavior_state, "warm_approach");
  assert.equal(byPacketId.proposal_hint_002.visual_profile.behavior_state, "cautious_boundary");
  assert.equal(byPacketId.proposal_hint_003.visual_profile.behavior_state, "low_interrupt_care");
  assert.equal(byPacketId.proposal_hint_001.visual_profile.motion_hint, "approach_sit_near");
  assert.equal(byPacketId.proposal_hint_002.visual_profile.motion_hint, "step_back_observe");
  assert.equal(byPacketId.proposal_hint_003.visual_profile.motion_hint, "quiet_low_motion");

  for (const scenario of shim.scenarios) {
    assert.equal(scenario.no_authority.direct_action_allowed, false);
    assert.equal(scenario.no_authority.direct_user_message_allowed, false);
    assert.equal(scenario.no_authority.direct_memory_write_allowed, false);
    assert.equal(scenario.no_authority.runtime_gate_bypass_allowed, false);
    assert.equal(scenario.no_authority.proactive_trigger_allowed, false);
    assert.equal(containsExecutableField(scenario), false);
  }
});

test("rejects PSPC packets that carry runtime authority or executable fields", () => {
  const packet = readContract().packets[0];

  assert.doesNotThrow(() => validatePspcProposalHintPacket(packet));
  assert.doesNotThrow(() => mapPspcProposalHintPacket(packet));

  const enabledPacket = clone(packet);
  enabledPacket.enabled = true;
  assert.throws(() => validatePspcProposalHintPacket(enabledPacket), /enabled=false/);

  const mainlinePacket = clone(packet);
  mainlinePacket.mainline_connected = true;
  assert.throws(() => validatePspcProposalHintPacket(mainlinePacket), /mainline_connected=false/);

  const missingForbidden = clone(packet);
  delete missingForbidden.forbidden.can_write_memory;
  assert.throws(() => validatePspcProposalHintPacket(missingForbidden), /forbidden.can_write_memory/);

  const unsafeForbidden = clone(packet);
  unsafeForbidden.forbidden.can_drive_runtime = true;
  assert.throws(() => validatePspcProposalHintPacket(unsafeForbidden), /forbidden.can_drive_runtime/);

  const executablePacket = clone(packet);
  executablePacket.action = "approach_user";
  assert.throws(() => validatePspcProposalHintPacket(executablePacket), /executable field/);
});

test("PSPC visual shim source stays presentation-only", () => {
  const source = fs.readFileSync(path.join(repoRoot, "EgoDesktop", "src", "pspcVisualShim.js"), "utf8");

  assert.equal(source.includes("ego_operator_desktop_turn"), false);
  assert.equal(source.includes("runEgoOperatorDesktopTurn"), false);
  assert.equal(source.includes("sendChatTurn"), false);
  assert.equal(/\bspawn\b/.test(source), false);
  assert.equal(source.includes("writeMemory"), false);
  assert.equal(source.includes("invokeGate"), false);
});

test("viewer PSPC demo controls do not route through chat turn", () => {
  const html = fs.readFileSync(path.join(repoRoot, "EgoDesktop", "viewer", "index.html"), "utf8");
  const renderer = fs.readFileSync(path.join(repoRoot, "EgoDesktop", "viewer", "renderer.js"), "utf8");

  assert.equal(html.includes("pspc-demo-panel"), true);
  assert.equal(html.includes("pspc-scenario-select"), true);
  assert.equal(html.includes("pspc-bubble"), true);
  assert.equal(renderer.includes("config.pspcVisualShim"), true);

  const demoSection = renderer.match(/function setupPspcVisualShim[\s\S]*?\n  function rendererResolution/);
  assert.ok(demoSection, "setupPspcVisualShim section should exist");
  assert.equal(demoSection[0].includes("sendChatTurn"), false);
  assert.equal(demoSection[0].includes("synthesizeSpeech"), false);
});
