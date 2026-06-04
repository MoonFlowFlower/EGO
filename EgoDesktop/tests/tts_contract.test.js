const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const {
  buildTtsRequest,
  resolveTtsAudioRequestPath,
  sanitizeSpeechTextForTts,
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

test("builds TTS request from displayed bot text before raw bot text", () => {
  const request = buildTtsRequest({
    turn: {
      schema_version: "ego_desktop.chat_turn.v1",
      status: "ok",
      bot_text: "这不是屏幕最终显示的文字。",
      visible_bot_text: "这才是屏幕最终显示的文字。",
    },
    voiceEnabled: true,
    requestId: "turn-visible-1",
  });

  assert.equal(request.status, "tts_request_admitted");
  assert.equal(request.text, "这才是屏幕最终显示的文字。");
  assert.equal(request.source_visible_text, "这才是屏幕最终显示的文字。");
  assert.equal(request.text_source, "displayed_bot_text_sanitized");
  assert.equal(request.visible_text_matches_tts_text, true);
  assert.equal(request.removed_non_speech_tokens, false);
});

test("sanitizes emoji and pictographic symbols out of TTS text", () => {
  assert.equal(sanitizeSpeechTextForTts("哈哈，您好呀～ 😊"), "哈哈，您好呀～");
  assert.equal(sanitizeSpeechTextForTts("可以👍🏽👩‍💻🇯🇵1️⃣，再说。"), "可以，再说。");
});

test("builds TTS request from displayed text but removes emoji for speech", () => {
  const request = buildTtsRequest({
    turn: {
      schema_version: "ego_desktop.chat_turn.v1",
      status: "ok",
      bot_text: "raw fallback",
      visible_bot_text: "哈哈，您好呀～ 😊",
    },
    voiceEnabled: true,
    requestId: "turn-emoji-1",
  });

  assert.equal(request.status, "tts_request_admitted");
  assert.equal(request.source_visible_text, "哈哈，您好呀～ 😊");
  assert.equal(request.text, "哈哈，您好呀～");
  assert.equal(request.text_source, "displayed_bot_text_sanitized");
  assert.equal(request.visible_text_matches_tts_text, false);
  assert.equal(request.removed_non_speech_tokens, true);
  assert.deepEqual(request.prosody_hint_candidates, ["warm", "playful"]);
});

test("does not synthesize disabled, empty, error, emoji-only, or too-long text", () => {
  assert.equal(buildTtsRequest({
    turn: { status: "ok", bot_text: "你好" },
    voiceEnabled: false,
  }).status, "voice_disabled");

  assert.equal(buildTtsRequest({
    turn: { status: "ok", bot_text: "" },
    voiceEnabled: true,
  }).status, "empty_text");

  assert.equal(buildTtsRequest({
    turn: { status: "ok", bot_text: "fallback", visible_bot_text: "😊👩‍💻🇯🇵1️⃣" },
    voiceEnabled: true,
  }).status, "empty_speech_text");

  assert.equal(buildTtsRequest({
    turn: {
      status: "llm_expression_unavailable",
      bot_text: "llm_expression_unavailable",
      visible_bot_text: "屏幕错误文本也不能朗读",
    },
    voiceEnabled: true,
  }).status, "not_admitted");

  assert.equal(buildTtsRequest({
    turn: { status: "ok", bot_text: "短文本", visible_bot_text: "啊".repeat(601) },
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
