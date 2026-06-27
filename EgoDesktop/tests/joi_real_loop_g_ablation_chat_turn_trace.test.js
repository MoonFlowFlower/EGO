const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const mainSourcePath = path.join(__dirname, "..", "src", "main.js");
const rendererSourcePath = path.join(__dirname, "..", "viewer", "renderer.js");

function readSource(filePath) {
  return fs.readFileSync(filePath, "utf8");
}

test("main config exposes only explicit chat-turn trace smoke prompt", () => {
  const mainSource = readSource(mainSourcePath);

  assert.match(mainSource, /joiRealLoopChatSmokeText:\s*String\(args\["joi-real-loop-chat-smoke-text"\]\s*\|\|\s*""\)/);
  assert.doesNotMatch(mainSource, /JOI_REAL_LOOP_G_ABLATION\s*=\s*["']1["']/);
});

test("renderer drives chat-turn trace smoke through preload IPC before renderer-ready", () => {
  const rendererSource = readSource(rendererSourcePath);

  assert.match(rendererSource, /config\.joiRealLoopChatSmokeText/);
  assert.match(rendererSource, /window\.egoDesktop\.sendChatTurn\(\{\s*userText:\s*config\.joiRealLoopChatSmokeText\s*\}\)/s);
  assert.match(rendererSource, /joiRealLoopChatSmoke/);

  const chatSmokeIndex = rendererSource.indexOf("sendChatTurn({ userText: config.joiRealLoopChatSmokeText })");
  const modelLoadIndex = rendererSource.indexOf("const loaded = await loadLive2DModel(config");
  const reportReadyIndex = rendererSource.indexOf("reportReady({");
  assert.ok(chatSmokeIndex > 0, "chat-turn smoke call should exist");
  assert.ok(modelLoadIndex > 0, "model load should exist");
  assert.ok(reportReadyIndex > 0, "renderer-ready payload should exist");
  assert.ok(chatSmokeIndex < modelLoadIndex, "chat-turn smoke should run before Live2D model loading can block");
  assert.ok(chatSmokeIndex < reportReadyIndex, "chat-turn smoke should run before renderer-ready is reported");
});
