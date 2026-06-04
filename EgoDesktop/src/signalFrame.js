function sideEffectsFromContract(contract) {
  const status = contract && typeof contract.side_effect_status === "object"
    ? contract.side_effect_status
    : {};
  return {
    side_effects_executed: Boolean(status.side_effects_executed),
    memory_write: Boolean(status.memory_write_executed),
    tool_use: Boolean(status.tool_use_executed),
    message_send: Boolean(status.message_send_executed),
    file_write: Boolean(status.file_write_executed),
    network_call: Boolean(status.network_call_executed),
  };
}

function buildViewerSignalFrame(contract) {
  const safeContract = contract && typeof contract === "object" ? contract : {};
  const presence = safeContract.presence_state && typeof safeContract.presence_state === "object"
    ? safeContract.presence_state
    : {};
  const visibleIntent =
    safeContract.visible_expression_intent && typeof safeContract.visible_expression_intent === "object"
      ? safeContract.visible_expression_intent
      : {};
  const sideEffects = sideEffectsFromContract(safeContract);
  return {
    schema_version: "ego_desktop.viewer_signal_frame.v1",
    primitive_class: safeContract.primitive_class || "live2d_presence_state",
    source: "ego_desktop.signal_frame_sanitizer",
    presence_state: {
      state: String(presence.state || "attentive_planning"),
      expression: String(presence.expression || "focused"),
      motion: String(presence.motion || "idle_listen"),
      intensity: String(presence.intensity || "low"),
    },
    visible_expression_intent: {
      intent_type: String(visibleIntent.intent_type || "embodied_initiative_expression"),
      side_effect_free: visibleIntent.side_effect_free !== false,
    },
    side_effects_executed: sideEffects.side_effects_executed,
    memory_write: sideEffects.memory_write,
    tool_use: sideEffects.tool_use,
    message_send: sideEffects.message_send,
    file_write: sideEffects.file_write,
    network_call: sideEffects.network_call,
    allowed_to_send_message: false,
    allowed_to_write_memory: false,
    allowed_to_use_tools: false,
    allowed_to_write_files: false,
    allowed_to_use_network: false,
  };
}

module.exports = { buildViewerSignalFrame };
