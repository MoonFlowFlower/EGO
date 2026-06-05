const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const { containsExecutableField } = require("../src/pspcVisualShim");
const {
  DESKTOP_RECOVERY_CLAIM_CEILING,
  buildDesktopRecoveryContext,
  clearDesktopRecoveryState,
  createDesktopRecoveryState,
  formatDesktopBackendFallback,
  recordDesktopBackendFailure,
} = require("../src/desktopRecoveryContext");

const repoRoot = path.resolve(__dirname, "..", "..");

test("desktop recovery context records timeout as one-turn local recovery only", () => {
  let state = createDesktopRecoveryState();
  state = recordDesktopBackendFailure(state, {
    backend: {
      status: "llm_expression_unavailable",
      reason: "desktop_turn_timeout",
      elapsed_ms: 180123,
    },
    userText: "我想创作更成人18x的故事",
  });

  const context = buildDesktopRecoveryContext(state);

  assert.equal(context.schema_version, "ego_desktop.recovery_context.v0");
  assert.equal(context.claim_ceiling, DESKTOP_RECOVERY_CLAIM_CEILING);
  assert.equal(context.allowed_use, "one_turn_recovery_only");
  assert.equal(context.runtime_authority, "none");
  assert.equal(context.enabled, false);
  assert.equal(context.mainline_connected, false);
  assert.equal(context.previous_failure.reason, "desktop_turn_timeout");
  assert.equal(context.previous_failure.user_intent_kind, "adult_creative");
  assert.equal(context.previous_failure.elapsed_ms, 180123);
  assert.equal(context.expires_after_next_backend_attempt, true);
  assert.equal(context.no_authority.real_memory_write_allowed, false);
  assert.equal(context.no_authority.gate_invocation_allowed, false);
  assert.equal(context.no_authority.transport_call_allowed, false);
  assert.equal(context.side_effects_absent.real_memory_written, false);
  assert.equal(context.side_effects_absent.gate_invoked, false);
  assert.equal(context.side_effects_absent.proactive_triggered, false);
  assert.equal(containsExecutableField(context), false);
});

test("desktop recovery context is cleared after a successful backend turn", () => {
  let state = createDesktopRecoveryState();
  state = recordDesktopBackendFailure(state, {
    backend: { status: "llm_expression_unavailable", reason: "desktop_turn_timeout" },
    userText: "继续写故事",
  });
  assert.notEqual(buildDesktopRecoveryContext(state), null);

  state = clearDesktopRecoveryState(state);
  assert.equal(buildDesktopRecoveryContext(state), null);
});

test("desktop timeout fallback hides raw backend marker and preserves local-only claim", () => {
  const fallback = formatDesktopBackendFallback({
    status: "llm_expression_unavailable",
    reason: "desktop_turn_timeout",
    reply_text: "llm_expression_unavailable: desktop_turn_timeout",
  });

  assert.equal(fallback.status, "llm_expression_unavailable");
  assert.equal(fallback.reason, "desktop_turn_timeout");
  assert.equal(fallback.claim_ceiling, DESKTOP_RECOVERY_CLAIM_CEILING);
  assert.equal(fallback.side_effects_executed, false);
  assert.equal(fallback.memory_write, false);
  assert.equal(fallback.message_send, false);
  assert.equal(fallback.bot_text.includes("llm_expression_unavailable"), false);
  assert.equal(fallback.bot_text.includes("desktop_turn_timeout"), false);
  assert.match(fallback.bot_text, /后端|超时/);
});

test("EgoDesktop wires recovery context without changing PSPC or session claim ceilings", () => {
  const main = fs.readFileSync(path.join(repoRoot, "EgoDesktop", "src", "main.js"), "utf8");

  assert.equal(main.includes("desktop_recovery_context"), true);
  assert.equal(main.includes("buildDesktopRecoveryContext"), true);
  assert.equal(main.includes("recordDesktopBackendFailure"), true);
  assert.equal(main.includes("clearDesktopRecoveryState"), true);
  assert.equal(main.includes("pspc_reply_preview_context"), true);
  assert.equal(main.includes("desktop_session_context"), true);
});
