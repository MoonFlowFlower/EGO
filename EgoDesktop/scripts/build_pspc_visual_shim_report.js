const fs = require("node:fs");
const path = require("node:path");
const { buildPspcVisualShim } = require("../src/pspcVisualShim");

function readJson(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function writeJson(filePath, payload) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(payload, null, 2), "utf8");
}

function writeText(filePath, content) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, content, "utf8");
}

function parseArgs(argv) {
  const parsed = {};
  const args = Array.from(argv || []);
  for (let index = 0; index < args.length; index += 1) {
    const item = args[index];
    if (!item.startsWith("--")) {
      continue;
    }
    const key = item.slice(2);
    const next = args[index + 1];
    if (typeof next === "string" && !next.startsWith("--")) {
      parsed[key] = next;
      index += 1;
    } else {
      parsed[key] = true;
    }
  }
  return parsed;
}

function renderMarkdown(shim, smokeReport) {
  const scenarioLines = shim.scenarios.map((scenario) => (
    `- ${scenario.packet_id}: \`${scenario.visual_profile.behavior_state}\`, ` +
    `motion=\`${scenario.visual_profile.motion_hint}\`, confidence=${scenario.confidence}, ` +
    `tag=\`${scenario.confidence_tag}\``
  ));
  const smokeSection = smokeReport ? `## Viewer Smoke

- status: \`${smokeReport.status || "unknown"}\`
- model_loaded: \`${Boolean(smokeReport.model_loaded)}\`
- pspc_visual_shim_ready: \`${Boolean(smokeReport.renderer_payload && smokeReport.renderer_payload.pspcVisualShimReady)}\`
- pspc_visual_scenario_count: \`${Number(smokeReport.renderer_payload && smokeReport.renderer_payload.pspcVisualScenarioCount || 0)}\`
- side_effects_executed: \`${Boolean(smokeReport.side_effects_executed)}\`
- memory_write: \`${Boolean(smokeReport.memory_write)}\`
- message_send: \`${Boolean(smokeReport.message_send)}\`
- tool_use: \`${Boolean(smokeReport.tool_use)}\`

` : "";
  return `# EgoDesktop PSPC Live2D Behavior v0 Report

- status: \`pass\`
- claim_ceiling: \`${shim.claim_ceiling}\`
- runtime_authority: \`${shim.runtime_authority}\`
- enabled: \`${shim.enabled}\`
- mainline_connected: \`${shim.mainline_connected}\`
- allowed_use: \`${shim.allowed_use}\`

## Scenario Mapping

${scenarioLines.join("\n")}

${smokeSection}\
## Side Effect Boundary

- user response mutated: \`${shim.side_effects_absent.user_response_mutated}\`
- memory written: \`${shim.side_effects_absent.memory_written}\`
- gate invoked: \`${shim.side_effects_absent.gate_invoked}\`
- approval invoked: \`${shim.side_effects_absent.approval_invoked}\`
- transport called: \`${shim.side_effects_absent.transport_called}\`
- proactive triggered: \`${shim.side_effects_absent.proactive_triggered}\`
- runtime registered: \`${shim.side_effects_absent.runtime_registered}\`

## What This Proves

${shim.what_this_proves}

## What This Does Not Prove

${shim.what_this_does_not_prove}

## Failure Meaning

Failure means PSPC proposal hints are unsafe or too ambiguous for product-only local visual review. PSPC should remain artifact-only and no UI demo should consume the packets.

## Rollback

Delete \`EgoDesktop/src/pspcVisualShim.js\`, \`EgoDesktop/tests/pspc_visual_shim.test.js\`, viewer PSPC demo edits, \`docs/codex/tasks/egodesktop-pspc-visual-shim-v0/\`, \`artifacts/egodesktop_pspc_live2d_behavior_v0/\`, and matching state/ledger/generated-view entries.
`;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const repoRoot = path.resolve(__dirname, "..", "..");
  const inputPath = path.resolve(String(args.input || path.join(
    repoRoot,
    "artifacts",
    "pspc_shadow_proposal_hint_contract_v0",
    "proposal_hint_contract.json"
  )));
  const outDir = path.resolve(String(args.out || path.join(
    repoRoot,
    "artifacts",
    "egodesktop_pspc_live2d_behavior_v0"
  )));
  const shim = buildPspcVisualShim(readJson(inputPath), { artifactPath: inputPath });
  const smokePath = path.join(outDir, "smoke", "live2d_desktop_smoke_report.json");
  const smokeReport = fs.existsSync(smokePath) ? readJson(smokePath) : null;
  writeJson(path.join(outDir, "pspc_visual_shim.json"), shim);
  writeText(path.join(outDir, "EGODESKTOP_PSPC_LIVE2D_BEHAVIOR_V0_REPORT.md"), renderMarkdown(shim, smokeReport));
  return 0;
}

if (require.main === module) {
  process.exitCode = main();
}

module.exports = { renderMarkdown };
