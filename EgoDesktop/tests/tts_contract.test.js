const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const {
  buildTtsRequest,
  resolveTtsAudioRequestPath,
} = require("../src/tts");

test("builds TTS request only for admitted bot text", () => {
  const request = buildTtsRequest({
    turn: {
      schema_version: "ego_desktop.chat_turn.v1",
      status: "ok",
      bot_text: "你好呀，我在这里。",
      side_effects_executed: false,
      memory_write: false,
      tool_use: false,
      message_send: false,
    },
    voiceEnabled: true,
    requestId: "turn-1",
  });

  assert.equal(request.status, "tts_request_admitted");
  assert.equal(request.should_synthesize, true);
  assert.equal(request.text, "你好呀，我在这里。");
  assert.equal(request.voice_profile, "skadi_cn");
  assert.equal(request.rvc_model, "Skadi_CN.pth");
  assert.equal(request.f0method, "rmvpe");
  assert.equal(request.memory_write, false);
  assert.equal(request.tool_use, false);
  assert.equal(request.message_send, false);
});

test("does not synthesize disabled, empty, error, or too-long text", () => {
  assert.equal(buildTtsRequest({
    turn: { status: "ok", bot_text: "你好" },
    voiceEnabled: false,
  }).status, "voice_disabled");

  assert.equal(buildTtsRequest({
    turn: { status: "ok", bot_text: "" },
    voiceEnabled: true,
  }).status, "empty_text");

  assert.equal(buildTtsRequest({
    turn: { status: "llm_expression_unavailable", bot_text: "llm_expression_unavailable" },
    voiceEnabled: true,
  }).status, "not_admitted");

  assert.equal(buildTtsRequest({
    turn: { status: "ok", bot_text: "啊".repeat(601) },
    voiceEnabled: true,
    maxChars: 600,
  }).status, "text_too_long");
});

test("resolves only contained TTS audio files", () => {
  const audioRoot = fs.mkdtempSync(path.join(os.tmpdir(), "ego-tts-audio-"));
  const audioFile = path.join(audioRoot, "语音.wav");
  fs.writeFileSync(audioFile, "wav");

  assert.equal(
    resolveTtsAudioRequestPath(audioRoot, "/tts-audio/" + encodeURIComponent("语音.wav")),
    audioFile
  );

  assert.throws(
    () => resolveTtsAudioRequestPath(audioRoot, "/tts-audio/../secret.wav"),
    /outside TTS audio directory/
  );
});
