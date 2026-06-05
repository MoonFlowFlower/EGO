const { containsExecutableField } = require("./pspcVisualShim");

const DESKTOP_SESSION_CONTEXT_SCHEMA_VERSION = "ego_desktop.session_context.v0";
const DESKTOP_SESSION_CONTEXT_CLAIM_CEILING = "local_session_context_only";
const DEFAULT_MAX_TURNS = 12;
const DEFAULT_MAX_CHARS_PER_MESSAGE = 1200;
const DEFAULT_MAX_TOTAL_CHARS = 12000;

function clampPositiveInteger(value, fallback) {
  const number = Number(value);
  if (!Number.isFinite(number) || number <= 0) {
    return fallback;
  }
  return Math.floor(number);
}

function createDesktopSessionState(options) {
  const settings = options || {};
  return {
    next_turn_index: 1,
    max_turns: clampPositiveInteger(settings.maxTurns, DEFAULT_MAX_TURNS),
    max_chars_per_message: clampPositiveInteger(settings.maxCharsPerMessage, DEFAULT_MAX_CHARS_PER_MESSAGE),
    max_total_chars: clampPositiveInteger(settings.maxTotalChars, DEFAULT_MAX_TOTAL_CHARS),
    turns: [],
  };
}

function truncateText(text, maxChars) {
  const raw = String(text || "").trim();
  if (raw.length <= maxChars) {
    return raw;
  }
  return raw.slice(0, maxChars) + "\n...[truncated]";
}

function trimToTotalBudget(messages, maxTotalChars) {
  const trimmed = messages.slice();
  let total = trimmed.reduce((sum, message) => sum + String(message.content || "").length, 0);
  while (trimmed.length > 0 && total > maxTotalChars) {
    const removed = trimmed.shift();
    total -= String(removed.content || "").length;
  }
  return trimmed;
}

function appendDesktopSessionTurn(state, turn) {
  const current = state && typeof state === "object"
    ? state
    : createDesktopSessionState();
  if (!turn || turn.status !== "ok") {
    return current;
  }
  const userText = truncateText(turn.userText, current.max_chars_per_message);
  const assistantText = truncateText(turn.assistantText, current.max_chars_per_message);
  if (!userText || !assistantText) {
    return current;
  }
  const nextTurnIndex = Number(current.next_turn_index || 1);
  const turns = Array.isArray(current.turns) ? current.turns.slice() : [];
  turns.push({
    turn_index: nextTurnIndex,
    user: userText,
    assistant: assistantText,
  });
  const maxTurns = clampPositiveInteger(current.max_turns, DEFAULT_MAX_TURNS);
  return {
    ...current,
    next_turn_index: nextTurnIndex + 1,
    turns: turns.slice(-maxTurns),
  };
}

function messagesFromTurns(state) {
  const turns = Array.isArray(state && state.turns) ? state.turns : [];
  const maxChars = clampPositiveInteger(
    state && state.max_chars_per_message,
    DEFAULT_MAX_CHARS_PER_MESSAGE
  );
  const messages = [];
  for (const turn of turns) {
    const turnIndex = Number(turn.turn_index || 0);
    const user = truncateText(turn.user, maxChars);
    const assistant = truncateText(turn.assistant, maxChars);
    if (user) {
      messages.push({ role: "user", content: user, turn_index: turnIndex });
    }
    if (assistant) {
      messages.push({ role: "assistant", content: assistant, turn_index: turnIndex });
    }
  }
  return trimToTotalBudget(
    messages,
    clampPositiveInteger(state && state.max_total_chars, DEFAULT_MAX_TOTAL_CHARS)
  );
}

function buildDesktopSessionContext(state) {
  const safeState = state && typeof state === "object" ? state : createDesktopSessionState();
  const context = {
    schema_version: DESKTOP_SESSION_CONTEXT_SCHEMA_VERSION,
    source: "ego_desktop_main_process_session_local",
    claim_ceiling: DESKTOP_SESSION_CONTEXT_CLAIM_CEILING,
    persistence: "window_lifetime_only",
    runtime_authority: "none",
    enabled: false,
    mainline_connected: false,
    messages: messagesFromTurns(safeState),
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
    throw new Error("desktop session context contains executable field");
  }
  return context;
}

module.exports = {
  DEFAULT_MAX_CHARS_PER_MESSAGE,
  DEFAULT_MAX_TOTAL_CHARS,
  DEFAULT_MAX_TURNS,
  DESKTOP_SESSION_CONTEXT_CLAIM_CEILING,
  DESKTOP_SESSION_CONTEXT_SCHEMA_VERSION,
  appendDesktopSessionTurn,
  buildDesktopSessionContext,
  createDesktopSessionState,
};
