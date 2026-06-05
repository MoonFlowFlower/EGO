const path = require("node:path");
const { spawn } = require("node:child_process");

const DEFAULT_EXTRACTOR_TIMEOUT_MS = 6000;

function buildPspcSignalExtractionPayload({ userText, desktopSessionContext } = {}) {
  const messages = desktopSessionContext && Array.isArray(desktopSessionContext.messages)
    ? desktopSessionContext.messages.slice(-8).map((message) => ({
      role: String(message.role || ""),
      content: String(message.content || "").slice(0, 600),
      turn_index: Number(message.turn_index || 0),
    })).filter((message) => ["user", "assistant"].includes(message.role) && message.content)
    : [];
  return {
    schema_version: "ego_desktop.pspc_signal_extraction_request.v0",
    source: "ego_desktop_main_process_session_local",
    claim_ceiling: "local_reply_preview_semantic_signal_extractor_only",
    allowed_use: "local_reply_preview_signal_extraction_only",
    runtime_authority: "none",
    enabled: false,
    mainline_connected: false,
    user_text: String(userText || ""),
    recent_messages: messages,
    forbidden: {
      direct_action: true,
      direct_user_message: true,
      direct_memory_write: true,
      runtime_gate_bypass: true,
      runtime_registration: true,
      proactive_trigger: true,
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

function unavailablePacket(userText, reason) {
  return {
    schema_version: "ego_desktop.pspc_semantic_interaction_events.v0",
    source: "ego_desktop_pspc_semantic_signal_extractor",
    claim_ceiling: "local_reply_preview_semantic_signal_extractor_only",
    runtime_authority: "none",
    enabled: false,
    mainline_connected: false,
    extractor_status: "extractor_unavailable",
    input_text_hash_basis: String(userText || "").slice(0, 24),
    reason: String(reason || "unavailable").slice(0, 240),
    events: [],
  };
}

function runPspcSignalExtractor({
  repoRoot,
  pythonCommand,
  userText,
  desktopSessionContext,
  timeoutMs,
} = {}) {
  const root = path.resolve(repoRoot || path.resolve(__dirname, "..", ".."));
  const command = pythonCommand || "python";
  const scriptPath = path.join(root, "scripts", "ego_desktop_pspc_signal_extract.py");
  const payload = buildPspcSignalExtractionPayload({ userText, desktopSessionContext });
  const safeTimeout = Number(timeoutMs || DEFAULT_EXTRACTOR_TIMEOUT_MS);

  return new Promise((resolve) => {
    const child = spawn(command, [scriptPath, "--timeout-ms", String(safeTimeout)], {
      cwd: root,
      windowsHide: true,
      stdio: ["pipe", "pipe", "pipe"],
    });
    let stdout = "";
    let stderr = "";
    let settled = false;
    const timer = setTimeout(() => {
      if (settled) {
        return;
      }
      settled = true;
      child.kill();
      resolve(unavailablePacket(userText, "extractor_timeout"));
    }, safeTimeout + 1000);

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString("utf8");
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString("utf8");
    });
    child.on("error", (error) => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timer);
      resolve(unavailablePacket(userText, error.message));
    });
    child.on("close", () => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timer);
      try {
        resolve(JSON.parse(stdout));
      } catch (_error) {
        resolve(unavailablePacket(userText, stderr || "invalid extractor output"));
      }
    });
    child.stdin.end(`${JSON.stringify(payload)}\n`, "utf8");
  });
}

module.exports = {
  DEFAULT_EXTRACTOR_TIMEOUT_MS,
  buildPspcSignalExtractionPayload,
  runPspcSignalExtractor,
};
