(function defineSpeechTurnGuard(root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
    return;
  }
  root.EgoDesktopSpeechTurns = factory();
})(typeof globalThis !== "undefined" ? globalThis : this, function speechTurnGuardFactory() {
  function createSpeechTurnGuard() {
    let currentTurnId = 0;
    return {
      startTurn() {
        currentTurnId += 1;
        return currentTurnId;
      },
      currentTurnId() {
        return currentTurnId;
      },
      isCurrent(turnId) {
        return Number(turnId) === currentTurnId;
      },
      supersededResult(turnId) {
        return {
          status: "speech_superseded",
          speech_turn_id: Number(turnId) || 0,
          current_speech_turn_id: currentTurnId,
          side_effects_executed: false,
          ui_audio_delivery_executed: false,
          memory_write: false,
          tool_use: false,
          message_send: false,
          file_write: false,
          network_call: false,
        };
      },
    };
  }

  return { createSpeechTurnGuard };
});
