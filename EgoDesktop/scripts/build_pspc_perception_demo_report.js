const fs = require("node:fs");
const path = require("node:path");
const { buildPspcPerceptionDemo } = require("../src/pspcPerceptionDemo");
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

function renderScenarioList(demo) {
  return demo.scenarios.map((scenario) => (
    `- ${scenario.demo_id}: packet=\`${scenario.packet_id}\`, trigger=\`${scenario.trigger_text}\`, ` +
    `behavior=\`${scenario.perception_behavior}\`, motion=\`${scenario.visual_profile.motion_hint}\`, ` +
    `confidence=${scenario.confidence}, basis=\`${scenario.basis}\``
  )).join("\n");
}

function renderSmokeSection(smokeReport) {
  if (!smokeReport) {
    return "## Viewer Smoke\n\n- status: `not_run`\n\n";
  }
  const payload = smokeReport.renderer_payload || {};
  return `## Viewer Smoke

- status: \`${smokeReport.status || "unknown"}\`
- model_loaded: \`${Boolean(smokeReport.model_loaded)}\`
- pspc_perception_demo_ready: \`${Boolean(payload.pspcPerceptionDemoReady)}\`
- pspc_perception_scenario_count: \`${Number(payload.pspcPerceptionScenarioCount || 0)}\`
- same_trigger: \`${String(payload.pspcSameTriggerText || "")}\`
- recording_mode: \`${Boolean(payload.pspcRecordingMode)}\`
- perception_chat_disabled: \`${Boolean(payload.pspcPerceptionChatDisabled)}\`
- side_effects_executed: \`${Boolean(smokeReport.side_effects_executed)}\`
- memory_write: \`${Boolean(smokeReport.memory_write)}\`
- message_send: \`${Boolean(smokeReport.message_send)}\`
- tool_use: \`${Boolean(smokeReport.tool_use)}\`

`;
}

function renderReport(demo, smokeReport) {
  return `# EgoDesktop PSPC Perception Demo v0 Report

- status: \`pass\`
- claim_ceiling: \`${demo.claim_ceiling}\`
- runtime_authority: \`${demo.runtime_authority}\`
- enabled: \`${demo.enabled}\`
- mainline_connected: \`${demo.mainline_connected}\`
- adapter_created: \`${demo.adapter_created}\`
- allowed_use: \`${demo.allowed_use}\`
- trigger: \`${demo.trigger_text}\`
- recording_window: \`${demo.recording_mode.width}x${demo.recording_mode.height}\`
- deterministic_step_ms: \`${demo.recording_mode.step_ms}\`

## Scenario List

${renderScenarioList(demo)}

${renderSmokeSection(smokeReport)}\
## Side Effect Boundary

- user response mutated: \`${demo.side_effects_absent.user_response_mutated}\`
- real memory written: \`${demo.side_effects_absent.real_memory_written}\`
- gate invoked: \`${demo.side_effects_absent.gate_invoked}\`
- approval invoked: \`${demo.side_effects_absent.approval_invoked}\`
- transport called: \`${demo.side_effects_absent.transport_called}\`
- proactive triggered: \`${demo.side_effects_absent.proactive_triggered}\`
- runtime registered: \`${demo.side_effects_absent.runtime_registered}\`
- message sent: \`${demo.side_effects_absent.message_sent}\`

## What This Proves

${demo.what_this_proves}

It proves only a local presentation layer can replay four PSPC proposal-hint histories as different visible Live2D companion behaviors for the same trigger.

## What This Does Not Prove

${demo.what_this_does_not_prove}

It also does not prove humans will perceive the differences as useful; that needs a separate human perception review.

## Failure Meaning

Failure means the product-only visual layer is not yet suitable for human perception review. PSPC should remain artifact-only or visual-shim-only until the viewer can present deterministic, auditable, non-executable scenario differences.

## Rollback

Delete \`EgoDesktop/src/pspcPerceptionDemo.js\`, \`EgoDesktop/tests/pspc_perception_demo.test.js\`, the perception viewer edits, \`EgoDesktop/scripts/build_pspc_perception_demo_report.js\`, \`docs/codex/tasks/egodesktop-pspc-perception-demo-v0/\`, \`artifacts/egodesktop_pspc_perception_demo_v0/\`, and matching state/ledger/generated-view entries.

## Next Allowed Step

${demo.next_allowed_step}
`;
}

function renderBilibiliScripts(demo) {
  return `# Bilibili 3 Video Scripts

claim_ceiling: \`${demo.claim_ceiling}\`

These scripts are for local visual market validation only. They must not claim PSPC runtime integration, consciousness, subjective experience, real emotion, live autonomy, durable memory, or real user benefit.

## Video 1: Same Trigger, Different History

- Opening shot: show the fixed trigger \`${demo.trigger_text}\`.
- Cut 1: gentle history -> warm approach, soft greeting, closer posture.
- Cut 2: frequent interruption -> cautious boundary, slight step back, boundary bubble.
- Cut 3: late-night care -> quiet low-interrupt posture, gentle rest cue.
- Cut 4: mixed history -> hesitation, observation, preference check.
- Caption: \`同一句话，不同相处历史，展示层反应不同。\`
- Required disclaimer: \`本视频展示的是本地 presentation-only demo，不是主线接入。\`

## Video 2: Boundaries Are Product Value

- Show frequent interruption history label.
- Trigger: \`${demo.trigger_text}\`.
- Reaction: cautious boundary.
- Caption: \`不是永远讨好，而是能展示边界感。\`
- Required disclaimer: \`PSPC 不发消息、不写记忆、不影响真实回复。\`

## Video 3: Low-Interrupt Care

- Show late-night care history label.
- Trigger: \`${demo.trigger_text}\`.
- Reaction: quiet care, low motion, short bubble.
- Caption: \`深夜场景更安静，不靠弹窗打扰。\`
- Required disclaimer: \`这是本地视觉验证，不证明长期用户收益。\`
`;
}

function renderSteamGifChecklist(demo) {
  return `# Steam GIF Checklist

- [ ] Capture in \`${demo.recording_mode.width}x${demo.recording_mode.height}\`.
- [ ] Use deterministic scenario order: ${demo.scenario_order.map((item) => `\`${item}\``).join(" -> ")}.
- [ ] Show \`${demo.trigger_text}\` in every clip.
- [ ] Hide debug overlay for public GIFs.
- [ ] Record each scenario for at least ${Math.ceil(demo.recording_mode.step_ms / 1000)} seconds.
- [ ] Include one composite GIF showing all four scenarios in order.
- [ ] Do not show or imply runtime authority, direct messaging, memory writing, proactive behavior, consciousness, subjective experience, or real emotion.
- [ ] Verify no chat reply is generated during capture.
- [ ] Verify no EgoOperator gate, memory, transport, approval, or proactive path is invoked.
`;
}

function renderPerceptionTestPlan(demo) {
  return `# Perception Test Plan

- status: \`ready_for_human_perception_review\`
- claim_ceiling: \`${demo.claim_ceiling}\`
- trigger: \`${demo.trigger_text}\`

## Test Question

Can reviewers perceive that the same trigger produces different companion behaviors because the history context differs?

## Procedure

1. Show the four scenarios without the debug overlay.
2. Ask reviewers to label each reaction as one of: warm approach, cautious boundary, low-interrupt care, hesitation/low-confidence.
3. Repeat once with scenario labels hidden.
4. Record confusion pairs and whether any reaction feels manipulative, overly dependent, or too scripted.

## Minimum Useful Signal

- At least 3 of 4 scenario types are correctly distinguished by most reviewers.
- No public-facing clip implies PSPC has runtime authority or real subjective emotion.
- Reviewers can describe the visible difference without seeing the debug overlay.

## Stop-Loss

Stop and return to visual mapping if reviewers cannot distinguish the four behaviors, if the demo looks like static scripted text only, or if any script implies consciousness, live autonomy, durable memory, or real user benefit.

## What This Does Not Prove

This does not prove PSPC runtime integration, adapter readiness, EgoOperator efficacy, real user benefit, durable memory efficacy, live autonomy, consciousness, subjective experience, real emotion, or that the product should ship.
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
    "egodesktop_pspc_perception_demo_v0"
  )));
  const shim = buildPspcVisualShim(readJson(inputPath), { artifactPath: inputPath });
  const demo = buildPspcPerceptionDemo(shim);
  const smokePath = path.join(outDir, "smoke", "live2d_desktop_smoke_report.json");
  const smokeReport = fs.existsSync(smokePath) ? readJson(smokePath) : null;

  writeJson(path.join(outDir, "pspc_perception_demo.json"), demo);
  writeText(path.join(outDir, "PERCEPTION_DEMO_REPORT.md"), renderReport(demo, smokeReport));
  writeText(path.join(outDir, "BILIBILI_3_VIDEO_SCRIPTS.md"), renderBilibiliScripts(demo));
  writeText(path.join(outDir, "STEAM_GIF_CHECKLIST.md"), renderSteamGifChecklist(demo));
  writeText(path.join(outDir, "PERCEPTION_TEST_PLAN.md"), renderPerceptionTestPlan(demo));
  return 0;
}

if (require.main === module) {
  process.exitCode = main();
}

module.exports = {
  renderBilibiliScripts,
  renderPerceptionTestPlan,
  renderReport,
  renderSteamGifChecklist,
};
