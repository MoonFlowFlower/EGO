const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const { containsExecutableField } = require("../src/pspcVisualShim");
const {
  DESKTOP_SESSION_CONTEXT_CLAIM_CEILING,
  appendDesktopSessionTurn,
  buildDesktopSessionContext,
  createDesktopSessionState,
} = require("../src/sessionContext");

const repoRoot = path.resolve(__dirname, "..", "..");

test("session context starts empty and appends successful turns", () => {
  let state = createDesktopSessionState();
  let context = buildDesktopSessionContext(state);

  assert.equal(context.schema_version, "ego_desktop.session_context.v0");
  assert.equal(context.claim_ceiling, DESKTOP_SESSION_CONTEXT_CLAIM_CEILING);
  assert.equal(context.persistence, "window_lifetime_only");
  assert.deepEqual(context.messages, []);
  assert.equal(containsExecutableField(context), false);

  state = appendDesktopSessionTurn(state, {
    userText: "我喜欢椰果和珍珠奶茶",
    assistantText: "本次会话里我记下了这个偏好。",
    status: "ok",
  });
  context = buildDesktopSessionContext(state);

  assert.deepEqual(context.messages.map((message) => message.role), ["user", "assistant"]);
  assert.equal(context.messages[0].content, "我喜欢椰果和珍珠奶茶");
  assert.equal(context.messages[1].content, "本次会话里我记下了这个偏好。");
  assert.equal(context.messages[0].turn_index, 1);
  assert.equal(context.messages[1].turn_index, 1);
});

test("session context does not append failed backend turns", () => {
  const state = appendDesktopSessionTurn(createDesktopSessionState(), {
    userText: "继续",
    assistantText: "llm_expression_unavailable",
    status: "llm_expression_unavailable",
  });

  assert.deepEqual(buildDesktopSessionContext(state).messages, []);
});

test("session context trims old turns and long message content", () => {
  let state = createDesktopSessionState({ maxTurns: 2, maxCharsPerMessage: 12 });
  for (let index = 0; index < 4; index += 1) {
    state = appendDesktopSessionTurn(state, {
      userText: `用户第${index}轮：` + "很长".repeat(20),
      assistantText: `助手第${index}轮：` + "回应".repeat(20),
      status: "ok",
    });
  }

  const context = buildDesktopSessionContext(state);
  assert.equal(context.messages.length, 4);
  assert.deepEqual(context.messages.map((message) => message.turn_index), [3, 3, 4, 4]);
  for (const message of context.messages) {
    assert.ok(message.content.length <= 27, "content should be truncated with marker");
  }
});

test("session context enforces total character budget", () => {
  let state = createDesktopSessionState({ maxTurns: 12, maxCharsPerMessage: 1200, maxTotalChars: 90 });
  for (let index = 0; index < 6; index += 1) {
    state = appendDesktopSessionTurn(state, {
      userText: `user-${index}-` + "u".repeat(30),
      assistantText: `assistant-${index}-` + "a".repeat(30),
      status: "ok",
    });
  }

  const context = buildDesktopSessionContext(state);
  const total = context.messages.reduce((sum, message) => sum + message.content.length, 0);
  assert.ok(total <= 90);
  assert.ok(context.messages.length < 12);
});

test("session context wiring remains separated from PSPC reply preview context", () => {
  const main = fs.readFileSync(path.join(repoRoot, "EgoDesktop", "src", "main.js"), "utf8");

  assert.equal(main.includes("buildDesktopSessionContext"), true);
  assert.equal(main.includes("appendDesktopSessionTurn"), true);
  assert.equal(main.includes("desktop_session_context"), true);
  assert.equal(main.includes("pspc_reply_preview_context"), true);

  const contextIndex = main.indexOf("desktop_session_context");
  const pspcIndex = main.indexOf("pspc_reply_preview_context");
  assert.ok(contextIndex >= 0);
  assert.ok(pspcIndex >= 0);
  assert.notEqual(contextIndex, pspcIndex);
});
