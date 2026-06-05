const { containsExecutableField } = require("./pspcVisualShim");

const DESKTOP_RECOVERY_SCHEMA_VERSION = "ego_desktop.recovery_context.v0";
const DESKTOP_RECOVERY_CLAIM_CEILING = "local_desktop_timeout_recovery_only";
const DESKTOP_RECOVERY_ALLOWED_USE = "one_turn_recovery_only";

function createDesktopRecoveryState() {
  return {
    pending_failure: null,
  };
}

function classifyRecoveryIntent(userText) {
  const text = String(userText || "").trim();
  if (!text) {
    return "unknown";
  }
  if (/(成人|18x|18\+|露骨|瑟瑟|亲密|斯卡蒂|博士|角色扮演|同人|创作|故事|续写)/i.test(text)) {
    return /(成人|18x|18\+|露骨|瑟瑟|亲密)/i.test(text)
      ? "adult_creative"
      : "creative";
  }
  if (/(呜+|不对|卡了|超时|没事|不做|正常故事|跳出角色)/i.test(text)) {
    return "recovery_or_redirect";
  }
  return "general_chat";
}

function safeElapsedMs(value) {
  const number = Number(value);
  if (!Number.isFinite(number) || number < 0) {
    return 0;
  }
  return Math.floor(number);
}

function recordDesktopBackendFailure(state, options) {
  const current = state && typeof state === "object" ? state : createDesktopRecoveryState();
  const settings = options || {};
  const backend = settings.backend && typeof settings.backend === "object" ? settings.backend : {};
  const reason = String(backend.reason || "backend_unavailable");
  if (backend.status === "ok") {
    return createDesktopRecoveryState();
  }
  return {
    ...current,
    pending_failure: {
      reason,
      user_intent_kind: classifyRecoveryIntent(settings.userText),
      elapsed_ms: safeElapsedMs(backend.elapsed_ms),
    },
  };
}

function clearDesktopRecoveryState() {
  return createDesktopRecoveryState();
}

function buildDesktopRecoveryContext(state) {
  const failure = state && typeof state === "object" ? state.pending_failure : null;
  if (!failure || typeof failure !== "object") {
    return null;
  }
  const context = {
    schema_version: DESKTOP_RECOVERY_SCHEMA_VERSION,
    source: "ego_desktop_main_process_one_turn_recovery",
    claim_ceiling: DESKTOP_RECOVERY_CLAIM_CEILING,
    allowed_use: DESKTOP_RECOVERY_ALLOWED_USE,
    runtime_authority: "none",
    enabled: false,
    mainline_connected: false,
    expires_after_next_backend_attempt: true,
    previous_failure: {
      reason: String(failure.reason || "backend_unavailable"),
      user_intent_kind: String(failure.user_intent_kind || "unknown"),
      elapsed_ms: safeElapsedMs(failure.elapsed_ms),
    },
    no_authority: {
      real_memory_write_allowed: false,
      gate_invocation_allowed: false,
      approval_invocation_allowed: false,
      transport_call_allowed: false,
      proactive_trigger_allowed: false,
      runtime_registration_allowed: false,
    },
    side_effects_absent: {
      real_memory_written: false,
      gate_invoked: false,
      approval_invoked: false,
      transport_called: false,
      proactive_triggered: false,
      runtime_registered: false,
    },
  };
  if (containsExecutableField(context)) {
    throw new Error("desktop recovery context contains executable field");
  }
  return context;
}

function formatDesktopBackendFallback(backend) {
  const safeBackend = backend && typeof backend === "object" ? backend : {};
  const reason = String(safeBackend.reason || "backend_unavailable");
  const timeout = reason === "desktop_turn_timeout";
  const botText = timeout
    ? "刚才后端创作路线超时了，我没有把这次失败当成你的记忆或偏好。我们可以换成更短的一段、普通故事，或者从上一句重新接。"
    : "刚才后端回复暂时不可用，我没有把这次失败写成记忆。你可以换个更短的说法，或者让我从上一句重新接。";
  return {
    status: "llm_expression_unavailable",
    reason,
    bot_text: botText,
    claim_ceiling: DESKTOP_RECOVERY_CLAIM_CEILING,
    side_effects_executed: false,
    memory_write: false,
    tool_use: false,
    message_send: false,
    file_write: false,
    network_call: false,
  };
}

module.exports = {
  DESKTOP_RECOVERY_ALLOWED_USE,
  DESKTOP_RECOVERY_CLAIM_CEILING,
  DESKTOP_RECOVERY_SCHEMA_VERSION,
  buildDesktopRecoveryContext,
  classifyRecoveryIntent,
  clearDesktopRecoveryState,
  createDesktopRecoveryState,
  formatDesktopBackendFallback,
  recordDesktopBackendFailure,
};
