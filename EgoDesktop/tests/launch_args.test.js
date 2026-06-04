const assert = require("node:assert/strict");
const test = require("node:test");

const { normalizeNpmArgs } = require("../scripts/launch");

test("normalizes positional smoke args including TTS smoke text", () => {
  assert.deepEqual(
    normalizeNpmArgs(["model.model3.json", "out-dir", "你好呀"]),
    ["--model-path", "model.model3.json", "--out", "out-dir", "--tts-smoke-text", "你好呀"]
  );
});
