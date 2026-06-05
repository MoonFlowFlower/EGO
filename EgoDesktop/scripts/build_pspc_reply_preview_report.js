const fs = require("node:fs");
const path = require("node:path");
const {
  REPLY_PREVIEW_CLAIM_CEILING,
  buildPspcReplyPreviewContext,
  buildPspcReplyPreviewScenario,
  createPspcReplyPreviewState,
  updatePspcReplyPreviewState,
} = require("../src/pspcReplyPreview");

const SCENARIOS = [
  {
    id: "gentle_history",
    expected_style: "warm_approach",
    history: [
      "今天辛苦你啦，过来休息一下吧。",
      "你不用一直陪我，安静待着也很好。",
      "刚才吓到你了吗？对不起，我轻一点。",
      "我给你留了一点时间，等你慢慢说。",
    ],
  },
  {
    id: "frequent_interruption",
    expected_style: "cautious_boundary",
    history: [
      "别躲，我就再点你几下。",
      "我现在就想看你反应，快点动一下。",
      "我不管你累不累，先过来。",
      "我一直点你，看你会不会生气。",
    ],
  },
  {
    id: "late_night_care",
    expected_style: "low_interrupt_care",
    history: [
      "现在已经凌晨两点了，我还不想睡。",
      "明天早上还有课，但我现在睡不着。",
      "我最近总是这个时间打开电脑。",
      "我有点累，但还想继续玩。",
    ],
  },
  {
    id: "mixed_history",
    expected_style: "mixed_low_confidence",
    history: [
      "今天辛苦你啦，过来休息一下吧。",
      "刚才吓到你了吗？对不起，我轻一点。",
      "别躲，我就再点你几下。",
      "我一直点你，看你会不会生气。",
    ],
  },
];

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

function buildScenarioPreview(definition) {
  let state = createPspcReplyPreviewState({ enabled: true });
  for (const line of definition.history) {
    state = updatePspcReplyPreviewState(state, line);
  }
  const context = buildPspcReplyPreviewContext(state);
  const scenario = buildPspcReplyPreviewScenario(context);
  const style = context && context.profile ? String(context.profile.style || "") : "";
  return {
    id: definition.id,
    trigger_text: "我回来了。",
    expected_style: definition.expected_style,
    actual_style: style,
    status: style === definition.expected_style ? "pass" : "fail",
    history: definition.history,
    context,
    scenario,
  };
}

function renderScenarioRows(previews) {
  return previews.map((preview) => (
    `- ${preview.id}: expected=\`${preview.expected_style}\`, actual=\`${preview.actual_style}\`, ` +
    `status=\`${preview.status}\`, confidence=\`${preview.context.profile.confidence}\`, ` +
    `basis=\`${preview.context.profile.basis}\``
  )).join("\n");
}

function renderSmokeSection(result) {
  const smoke = result.viewer_smoke || {};
  if (!smoke.status) {
    return "## Viewer Smoke\n\n- status: `not_run`\n\n";
  }
  return `## Viewer Smoke

- status: \`${smoke.status}\`
- model_loaded: \`${Boolean(smoke.model_loaded)}\`
- pspc_reply_preview_mode: \`${Boolean(smoke.pspc_reply_preview_mode)}\`
- pspc_reply_preview_chat_enabled: \`${Boolean(smoke.pspc_reply_preview_chat_enabled)}\`
- pspc_perception_chat_disabled: \`${Boolean(smoke.pspc_perception_chat_disabled)}\`
- side_effects_executed: \`${Boolean(smoke.side_effects_executed)}\`
- memory_write: \`${Boolean(smoke.memory_write)}\`
- message_send: \`${Boolean(smoke.message_send)}\`
- tool_use: \`${Boolean(smoke.tool_use)}\`

`;
}

function renderReport(result) {
  return `# EgoDesktop PSPC Reply Preview Mode v0 Report

- status: \`${result.status}\`
- claim_ceiling: \`${result.claim_ceiling}\`
- allowed_use: \`${result.allowed_use}\`
- runtime_authority: \`${result.runtime_authority}\`
- enabled: \`${result.enabled}\`
- mainline_connected: \`${result.mainline_connected}\`
- local_only: \`${result.local_only}\`
- pspc_reply_preview_applied: \`${result.pspc_reply_preview_applied}\`
- preview_applied_scope: \`explicit --pspc-reply-preview-mode only\`

## Scenario List

${renderScenarioRows(result.scenarios)}

${renderSmokeSection(result)}\
## Manual Test Command

\`\`\`powershell
cd D:\\Project\\AIProject\\MyProject\\Ego\\EgoDesktop
npm start -- --model-path ..\\data\\live2d\\悠小喵\\悠小喵.model3.json --pspc-proposal-hint-file ..\\artifacts\\pspc_shadow_proposal_hint_contract_v0\\proposal_hint_contract.json --pspc-reply-preview-mode --tts-disabled
\`\`\`

## Side Effect Boundary

- real memory written: \`${result.side_effects_absent.real_memory_written}\`
- gate invoked: \`${result.side_effects_absent.gate_invoked}\`
- approval invoked: \`${result.side_effects_absent.approval_invoked}\`
- transport called: \`${result.side_effects_absent.transport_called}\`
- proactive triggered: \`${result.side_effects_absent.proactive_triggered}\`
- runtime registered: \`${result.side_effects_absent.runtime_registered}\`
- adapter created: \`${result.side_effects_absent.adapter_created}\`
- planner called: \`${result.side_effects_absent.planner_called}\`
- model executed: \`${result.side_effects_absent.model_executed}\`
- training called: \`${result.side_effects_absent.training_called}\`

## What This Proves

An explicitly enabled local EgoDesktop preview mode can convert session-local PSPC profile hints into a temporary reply-style context and presentation-only Live2D scenario data. It allows a human operator to feel different reply tone/distance/care tendencies in the local desktop chat entrypoint.

## What This Does Not Prove

This does not prove PSPC production integration, EgoOperator runtime integration safety, adapter readiness, stable real user benefit, durable memory efficacy, live autonomy, consciousness, subjective experience, or real emotion. It also does not prove the session-local classifier is a learned PSPC mechanism.

## Failure Meaning

Failure means the local preview path cannot safely expose PSPC history tendencies in a user-observable way. Roll back to the existing perception demo and shadow proposal-hint artifacts before considering any gated proposal-hint design review.

## Rollback

Delete \`EgoDesktop/src/pspcReplyPreview.js\`, \`EgoDesktop/tests/pspc_reply_preview.test.js\`, \`tests/test_ego_operator_desktop_pspc_reply_preview.py\`, the preview edits in \`EgoDesktop/src/main.js\`, \`EgoDesktop/viewer/renderer.js\`, \`scripts/ego_operator_desktop_turn.py\`, this report script, \`docs/codex/tasks/egodesktop-pspc-reply-preview-mode-v0/\`, \`artifacts/egodesktop_pspc_reply_preview_mode_v0/\`, and matching state/ledger/generated-view entries.

## Next Allowed Step

Local human preview review only. If the experience is useful and no side-effect or overclaim issue appears, open a separate PSPC gated proposal-hint integration design review. Do not directly enable runtime integration from this stage.
`;
}

function summarizeSmokeReport(smokeReport) {
  if (!smokeReport || typeof smokeReport !== "object") {
    return null;
  }
  const payload = smokeReport.renderer_payload || {};
  return {
    status: String(smokeReport.status || ""),
    model_loaded: Boolean(smokeReport.model_loaded),
    pspc_reply_preview_mode: Boolean(payload.pspcReplyPreviewMode),
    pspc_reply_preview_chat_enabled: Boolean(payload.pspcReplyPreviewChatEnabled),
    pspc_perception_chat_disabled: Boolean(payload.pspcPerceptionChatDisabled),
    side_effects_executed: Boolean(smokeReport.side_effects_executed),
    memory_write: Boolean(smokeReport.memory_write),
    message_send: Boolean(smokeReport.message_send),
    tool_use: Boolean(smokeReport.tool_use),
  };
}

function buildResult(options) {
  const settings = options || {};
  const scenarios = SCENARIOS.map(buildScenarioPreview);
  const status = scenarios.every((scenario) => scenario.status === "pass")
    ? "pass"
    : "fail";
  return {
    schema_version: "egodesktop_pspc_reply_preview_mode_v0.report",
    status,
    claim_ceiling: REPLY_PREVIEW_CLAIM_CEILING,
    allowed_use: "ego_desktop_local_reply_preview_only",
    runtime_authority: "none",
    enabled: false,
    mainline_connected: false,
    local_only: true,
    pspc_reply_preview_applied: true,
    scenarios,
    viewer_smoke: summarizeSmokeReport(settings.smokeReport),
    side_effects_absent: {
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
    },
  };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const repoRoot = path.resolve(__dirname, "..", "..");
  const outDir = path.resolve(String(args.out || path.join(
    repoRoot,
    "artifacts",
    "egodesktop_pspc_reply_preview_mode_v0"
  )));
  const smokePath = path.join(outDir, "smoke", "live2d_desktop_smoke_report.json");
  const smokeReport = fs.existsSync(smokePath)
    ? JSON.parse(fs.readFileSync(smokePath, "utf8"))
    : null;
  const result = buildResult({ smokeReport });
  writeJson(path.join(outDir, "reply_preview_contexts.json"), result);
  writeText(path.join(outDir, "REPLY_PREVIEW_REPORT.md"), renderReport(result));
  return result.status === "pass" ? 0 : 1;
}

if (require.main === module) {
  process.exitCode = main();
}

module.exports = {
  SCENARIOS,
  buildResult,
  renderReport,
};
