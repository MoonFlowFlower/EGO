const assert = require("node:assert/strict");
const test = require("node:test");

const {
  classifyExpressionForText,
  buildDesktopChatTurn,
  VISUALLY_UNSAFE_AUTOMATIC_EXPRESSIONS,
} = require("../src/chatTurn");

test("routes user and bot text to matching Live2D expression names", () => {
  assert.equal(classifyExpressionForText("我有点难过，刚才没做好"), "哭哭");
  assert.equal(classifyExpressionForText("这次成功了，好开心"), "星星眼");
  assert.equal(classifyExpressionForText("我需要先整理计划和记录"), "记笔记");
  assert.equal(classifyExpressionForText("这个表现不对"), "黑脸");
});

test("does not route neutral chat to visually unsafe front-lean expression", () => {
  assert.equal(VISUALLY_UNSAFE_AUTOMATIC_EXPRESSIONS.has("前倾"), true);
  assert.equal(classifyExpressionForText("你好呀"), "");
  assert.equal(classifyExpressionForText("你能做表情吗"), "");
  assert.equal(classifyExpressionForText("我的意思是 live2D 的表情"), "");
  assert.equal(buildDesktopChatTurn({ userText: "你好呀", botText: "我在" }).expression_name, "");
  assert.equal(buildDesktopChatTurn({ userText: "你好呀", botText: "我在", expressionName: "" }).expression_name, "");
});

test("desktop chat turn is side-effect free and carries expression intent", () => {
  const turn = buildDesktopChatTurn({
    userText: "这段体验还是不自然，需要修一下",
    botText: "先把不自然的点收成一个可验证修改。",
  });

  assert.equal(turn.status, "ok");
  assert.equal(turn.side_effects_executed, false);
  assert.equal(turn.memory_write, false);
  assert.equal(turn.tool_use, false);
  assert.equal(turn.message_send, false);
  assert.equal(turn.expression_name, "记笔记");
});
