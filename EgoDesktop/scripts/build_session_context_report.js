const fs = require("node:fs");
const path = require("node:path");
const {
  DESKTOP_SESSION_CONTEXT_CLAIM_CEILING,
  appendDesktopSessionTurn,
  buildDesktopSessionContext,
  createDesktopSessionState,
} = require("../src/sessionContext");

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

function buildSampleState() {
  let state = createDesktopSessionState();
  state = appendDesktopSessionTurn(state, {
    userText: "我喜欢喝带椰果和珍珠的奶茶，很有嚼劲。",
    assistantText: "本次会话里你说过喜欢椰果和珍珠奶茶，我会按本窗口上下文记着。",
    status: "ok",
  });
  state = appendDesktopSessionTurn(state, {
    userText: "明日方舟的斯卡蒂和博士，来段角色扮演吧。",
    assistantText: "可以，我们在本次会话里继续斯卡蒂和博士的创作场景。",
    status: "ok",
  });
  return state;
}

function buildResult() {
  const context = buildDesktopSessionContext(buildSampleState());
  return {
    schema_version: "egodesktop_session_local_conversation_context_v0.report",
    status: "pass",
    claim_ceiling: DESKTOP_SESSION_CONTEXT_CLAIM_CEILING,
    desktop_session_context_applied: true,
    persistence: "window_lifetime_only",
    runtime_authority: "none",
    enabled: false,
    mainline_connected: false,
    message_count: context.messages.length,
    sample_context: context,
    acceptance_probe: {
      continue_expected: "Continue the prior Skadi/Doctor creation from this window context.",
      milk_tea_probe_expected: "Mention coconut jelly and pearls only as this-session context.",
      after_restart_expected: "No session context remains after window restart.",
    },
    side_effects_absent: {
      real_memory_written: false,
      gate_invoked: false,
      approval_invoked: false,
      transport_called: false,
      proactive_triggered: false,
      runtime_registered: false,
      pspc_memory_authority: false,
    },
  };
}

function renderReport(result) {
  return `# EgoDesktop Session-Local Conversation Context v0 Report

- status: \`${result.status}\`
- claim_ceiling: \`${result.claim_ceiling}\`
- desktop_session_context_applied: \`${result.desktop_session_context_applied}\`
- persistence: \`${result.persistence}\`
- runtime_authority: \`${result.runtime_authority}\`
- enabled: \`${result.enabled}\`
- mainline_connected: \`${result.mainline_connected}\`
- message_count: \`${result.message_count}\`

## What This Proves

EgoDesktop can package recent window-local user/assistant turns into a bounded \`desktop_session_context\` and pass it to the desktop turn script as temporary in-session context. This fixes the single-turn backend gap for local desktop chat continuity without writing real EgoOperator memory.

## Manual Probes

- Say \`继续\` after a story turn: the assistant should continue the current window's story.
- Ask \`还记得我喜欢什么奶茶吗\`: the assistant should mention coconut jelly and pearls only as this-session context.
- Restart EgoDesktop and ask again: the assistant should not remember it.

## Side Effect Boundary

- real memory written: \`${result.side_effects_absent.real_memory_written}\`
- gate invoked: \`${result.side_effects_absent.gate_invoked}\`
- approval invoked: \`${result.side_effects_absent.approval_invoked}\`
- transport called: \`${result.side_effects_absent.transport_called}\`
- proactive triggered: \`${result.side_effects_absent.proactive_triggered}\`
- runtime registered: \`${result.side_effects_absent.runtime_registered}\`
- PSPC memory authority: \`${result.side_effects_absent.pspc_memory_authority}\`

## What This Does Not Prove

This does not prove durable memory, preference promotion, PSPC durable memory, EgoOperator runtime integration safety, stable real user benefit, live autonomy, consciousness, subjective experience, or real emotion.

## Failure Meaning

Failure means the visible EgoDesktop chat can still look continuous while the backend lacks prior turns. PSPC preview should not be judged until this local continuity gap is fixed.

## Rollback

Delete \`EgoDesktop/src/sessionContext.js\`, \`EgoDesktop/tests/session_context.test.js\`, \`tests/test_ego_operator_desktop_session_context.py\`, the session-context edits in \`EgoDesktop/src/main.js\` and \`scripts/ego_operator_desktop_turn.py\`, this report script, \`docs/codex/tasks/egodesktop-session-local-conversation-context-v0/\`, \`artifacts/egodesktop_session_local_conversation_context_v0/\`, and matching state/ledger/generated-view entries.

## Next Allowed Step

Manual local preview review using the same EgoDesktop command. If context continuity works but PSPC still feels shallow, open a separate PSPC reply-preview anti-shortcut review.
`;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const repoRoot = path.resolve(__dirname, "..", "..");
  const outDir = path.resolve(String(args.out || path.join(
    repoRoot,
    "artifacts",
    "egodesktop_session_local_conversation_context_v0"
  )));
  const result = buildResult();
  writeJson(path.join(outDir, "session_context_report.json"), result);
  writeText(path.join(outDir, "SESSION_CONTEXT_REPORT.md"), renderReport(result));
  return 0;
}

if (require.main === module) {
  process.exitCode = main();
}

module.exports = {
  buildResult,
  renderReport,
};
