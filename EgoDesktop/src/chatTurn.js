const EXPRESSION_RULES = [
  { name: "哭哭", patterns: [/难过/, /伤心/, /哭/, /失败/, /沮丧/, /崩/, /糟/] },
  { name: "流泪", patterns: [/委屈/, /流泪/, /疼/, /痛苦/] },
  { name: "星星眼", patterns: [/开心/, /成功/, /太棒/, /喜欢/, /可以了/, /好耶/, /漂亮/] },
  { name: "脸红", patterns: [/害羞/, /脸红/, /可爱/, /喜欢你/] },
  { name: "记笔记", patterns: [/计划/, /记录/, /整理/, /修/, /实现/, /验证/, /问题/, /方案/] },
  { name: "晕晕眼", patterns: [/混乱/, /不懂/, /晕/, /复杂/, /卡住/] },
  { name: "黑脸", patterns: [/生气/, /烦/, /离谱/, /不对/, /糟糕/, /模板/] },
  { name: "看手机", patterns: [/看看/, /查/, /搜索/, /找一下/] },
];
const NEUTRAL_EXPRESSION_NAME = "";
const VISUALLY_UNSAFE_AUTOMATIC_EXPRESSIONS = new Set(["前倾"]);

function normalizeText(text) {
  return String(text || "").trim();
}

function classifyExpressionForText(...parts) {
  const text = parts.map(normalizeText).filter(Boolean).join("\n");
  for (const rule of EXPRESSION_RULES) {
    if (rule.patterns.some((pattern) => pattern.test(text))) {
      return rule.name;
    }
  }
  return NEUTRAL_EXPRESSION_NAME;
}

function buildDesktopChatTurn({ userText, botText, status = "ok", expressionName } = {}) {
  const safeUserText = normalizeText(userText);
  const safeBotText = normalizeText(botText);
  const resolvedExpressionName = expressionName === undefined
    ? classifyExpressionForText(safeUserText, safeBotText)
    : normalizeText(expressionName);
  return {
    schema_version: "ego_desktop.chat_turn.v1",
    status,
    user_text: safeUserText,
    bot_text: safeBotText,
    expression_name: resolvedExpressionName,
    side_effects_executed: false,
    memory_write: false,
    tool_use: false,
    message_send: false,
    file_write: false,
    network_call: false,
  };
}

module.exports = {
  buildDesktopChatTurn,
  classifyExpressionForText,
  VISUALLY_UNSAFE_AUTOMATIC_EXPRESSIONS,
};
