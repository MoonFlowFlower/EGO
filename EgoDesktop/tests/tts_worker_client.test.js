const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const { TtsWorkerClient } = require("../src/ttsWorkerClient");

function writeFakeWorker() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "ego-tts-worker-test-"));
  const workerPath = path.join(root, "fake-worker.js");
  fs.writeFileSync(workerPath, `
const fs = require("node:fs");
const path = require("node:path");
const readline = require("node:readline");
console.log("worker boot noise");
console.log(JSON.stringify({ type: "ready", status: "ok", worker_mode: "fake" }));
readline.createInterface({ input: process.stdin }).on("line", (line) => {
  const request = JSON.parse(line);
  const audioRoot = request.audio_root;
  fs.mkdirSync(audioRoot, { recursive: true });
  const filePath = path.join(audioRoot, request.request_id + ".wav");
  fs.writeFileSync(filePath, "wav");
  console.log(JSON.stringify({
    type: "result",
    status: "ok",
    request_id: request.request_id,
    audio_file: filePath,
    audio_duration_sec: 0.1,
    side_effects_executed: false,
    memory_write: false,
    tool_use: false,
    message_send: false,
    ui_audio_delivery_executed: true
  }));
});
`, "utf8");
  return workerPath;
}

test("TtsWorkerClient sends JSON requests and returns contained audio URLs", async () => {
  const workerPath = writeFakeWorker();
  const audioRoot = fs.mkdtempSync(path.join(os.tmpdir(), "ego-tts-audio-client-"));
  const client = new TtsWorkerClient({
    workerCommand: process.execPath,
    workerArgs: [workerPath],
    audioRoot,
    startupTimeoutMs: 3000,
    requestTimeoutMs: 3000,
  });

  try {
    const result = await client.synthesize({
      status: "tts_request_admitted",
      should_synthesize: true,
      request_id: "turn_1",
      text: "你好",
      text_source: "displayed_bot_text",
      visible_text_matches_tts_text: true,
    });

    assert.equal(result.status, "ok");
    assert.equal(result.audio_url, "/tts-audio/turn_1.wav");
    assert.equal(result.text, "你好");
    assert.equal(result.text_source, "displayed_bot_text");
    assert.equal(result.visible_text_matches_tts_text, true);
    assert.equal(result.memory_write, false);
    assert.equal(result.tool_use, false);
    assert.equal(result.message_send, false);
    assert.equal(result.ui_audio_delivery_executed, true);
  } finally {
    client.shutdown();
  }
});
