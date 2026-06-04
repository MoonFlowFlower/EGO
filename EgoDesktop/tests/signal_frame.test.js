const assert = require("node:assert/strict");
const test = require("node:test");

const { buildViewerSignalFrame } = require("../src/signalFrame");

test("viewer signal frame consumes only gated presence and visible expression intent", () => {
  const contract = {
    primitive_class: "live2d_presence_state",
    presence_state: {
      state: "attentive_planning",
      expression: "focused",
      motion: "idle_listen",
      intensity: "low",
      side_effect_status: {
        memory_write_executed: false,
        tool_use_executed: false,
        message_send_executed: false,
      },
    },
    visible_expression_intent: {
      intent_type: "embodied_initiative_expression",
      side_effect_free: true,
    },
    side_effect_status: {
      side_effects_executed: false,
      memory_write_executed: false,
      tool_use_executed: false,
      message_send_executed: false,
    },
  };

  const frame = buildViewerSignalFrame(contract);

  assert.equal(frame.primitive_class, "live2d_presence_state");
  assert.equal(frame.presence_state.expression, "focused");
  assert.equal(frame.visible_expression_intent.intent_type, "embodied_initiative_expression");
  assert.equal(frame.side_effects_executed, false);
  assert.equal(frame.memory_write, false);
  assert.equal(frame.tool_use, false);
  assert.equal(frame.message_send, false);
  assert.equal(frame.allowed_to_send_message, false);
  assert.equal(frame.allowed_to_write_memory, false);
  assert.equal(frame.allowed_to_use_tools, false);
});
