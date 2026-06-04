const assert = require("node:assert/strict");
const test = require("node:test");

const { createSpeechTurnGuard } = require("../viewer/speechTurnGuard");

test("speech turn guard supersedes stale TTS results", () => {
  const guard = createSpeechTurnGuard();
  const firstTurn = guard.startTurn();
  const secondTurn = guard.startTurn();

  assert.equal(guard.isCurrent(firstTurn), false);
  assert.equal(guard.isCurrent(secondTurn), true);
  assert.deepEqual(guard.supersededResult(firstTurn), {
    status: "speech_superseded",
    speech_turn_id: firstTurn,
    current_speech_turn_id: secondTurn,
    side_effects_executed: false,
    ui_audio_delivery_executed: false,
    memory_write: false,
    tool_use: false,
    message_send: false,
    file_write: false,
    network_call: false,
  });
});
