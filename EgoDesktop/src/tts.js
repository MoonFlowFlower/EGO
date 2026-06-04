const path = require("node:path");

const DEFAULT_TTS_MAX_CHARS = 600;
const DEFAULT_VOICE_PROFILE = "skadi_cn";
const DEFAULT_BASE_VOICE = "zh-CN-XiaoxiaoNeural";
const DEFAULT_RVC_MODEL = "Skadi_CN.pth";
const DEFAULT_F0_METHOD = "rmvpe";
const DEFAULT_F0_UP_KEY = 0;

function normalizeText(text) {
  return String(text || "").trim();
}

function denied(status, reason) {
  return {
    schema_version: "ego_desktop.tts_request.v1",
    status,
    reason,
    should_synthesize: false,
    side_effects_executed: false,
    memory_write: false,
    tool_use: false,
    message_send: false,
    file_write: false,
    network_call: false,
    ui_audio_delivery_executed: false,
  };
}

function buildTtsRequest({
  turn,
  voiceEnabled,
  requestId,
  maxChars = DEFAULT_TTS_MAX_CHARS,
  voiceProfile = DEFAULT_VOICE_PROFILE,
  baseVoice = DEFAULT_BASE_VOICE,
  rvcModel = DEFAULT_RVC_MODEL,
  f0method = DEFAULT_F0_METHOD,
  f0upKey = DEFAULT_F0_UP_KEY,
} = {}) {
  if (!voiceEnabled) {
    return denied("voice_disabled", "voice output is disabled");
  }
  if (!turn || turn.status !== "ok") {
    return denied("not_admitted", "only admitted ok bot turns may be synthesized");
  }
  const text = normalizeText(turn.bot_text);
  if (!text) {
    return denied("empty_text", "bot text is empty");
  }
  if (text.length > Number(maxChars || DEFAULT_TTS_MAX_CHARS)) {
    return denied("text_too_long", "bot text exceeds desktop TTS maximum length");
  }
  return {
    schema_version: "ego_desktop.tts_request.v1",
    status: "tts_request_admitted",
    should_synthesize: true,
    request_id: normalizeText(requestId) || `tts_${Date.now()}`,
    text,
    text_chars: text.length,
    voice_profile: normalizeText(voiceProfile) || DEFAULT_VOICE_PROFILE,
    base_voice: normalizeText(baseVoice) || DEFAULT_BASE_VOICE,
    rvc_model: normalizeText(rvcModel) || DEFAULT_RVC_MODEL,
    f0method: normalizeText(f0method) || DEFAULT_F0_METHOD,
    f0up_key: Number.isFinite(Number(f0upKey)) ? Number(f0upKey) : DEFAULT_F0_UP_KEY,
    delivery_gate: "desktop_voice_enabled_and_turn_status_ok",
    visible_expression_source: "llm",
    source_turn_status: turn.status,
    source_turn_schema_version: turn.schema_version || "",
    side_effects_executed: false,
    memory_write: false,
    tool_use: false,
    message_send: false,
    file_write: false,
    network_call: false,
    ui_audio_delivery_executed: false,
  };
}

function stripQueryAndHash(requestUrl) {
  return String(requestUrl || "").split("?")[0].split("#")[0];
}

function resolveTtsAudioRequestPath(audioRoot, requestUrl) {
  const root = path.resolve(String(audioRoot || ""));
  const rawPath = stripQueryAndHash(requestUrl);
  if (!rawPath.startsWith("/tts-audio/")) {
    throw new Error(`TTS audio request path must start with /tts-audio/: ${requestUrl}`);
  }
  let relativeRequest = rawPath.slice("/tts-audio/".length);
  try {
    relativeRequest = decodeURIComponent(relativeRequest);
  } catch (_error) {
    throw new Error(`TTS audio request path is not valid URL encoding: ${requestUrl}`);
  }
  if (!relativeRequest || relativeRequest.includes("\0")) {
    throw new Error("TTS audio request path is empty or invalid");
  }
  relativeRequest = relativeRequest.replace(/\\/g, "/");
  if (relativeRequest.startsWith("/") || relativeRequest.split("/").includes("..")) {
    throw new Error("TTS audio request path outside TTS audio directory");
  }
  const targetPath = path.resolve(root, ...relativeRequest.split("/").filter(Boolean));
  const relativeToRoot = path.relative(root, targetPath);
  if (relativeToRoot === "" || relativeToRoot.startsWith("..") || path.isAbsolute(relativeToRoot)) {
    throw new Error("TTS audio request path outside TTS audio directory");
  }
  return targetPath;
}

function buildTtsAudioUrl(audioFilePath) {
  return `/tts-audio/${encodeURIComponent(path.basename(audioFilePath))}`;
}

module.exports = {
  DEFAULT_BASE_VOICE,
  DEFAULT_F0_METHOD,
  DEFAULT_F0_UP_KEY,
  DEFAULT_RVC_MODEL,
  DEFAULT_TTS_MAX_CHARS,
  DEFAULT_VOICE_PROFILE,
  buildTtsAudioUrl,
  buildTtsRequest,
  resolveTtsAudioRequestPath,
};
