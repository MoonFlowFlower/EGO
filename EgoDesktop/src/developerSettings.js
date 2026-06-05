const fs = require("node:fs");
const path = require("node:path");

const DEVELOPER_SETTINGS_SCHEMA_VERSION = "ego_desktop.developer_settings.v0";
const DEVELOPER_SETTINGS_CLAIM_CEILING = "local_desktop_developer_settings_only";

const FORBIDDEN_FIELD_NAMES = new Set([
  "action",
  "tool_call",
  "command",
  "user_message",
  "memory_write",
  "gate_decision",
  "approval_id",
  "transport",
  "send",
  "schedule",
  "enable",
  "enabled",
  "mainline_connected",
  "mainline_authority",
  "runtime_authority",
  "api_key",
  "provider_key",
  "secret",
  "token",
  "password",
]);

const FIELD_SPECS = {
  developer_mode_enabled: {
    defaultValue: false,
    type: "boolean",
    live: true,
  },
  debug_overlay_default_visible: {
    defaultValue: false,
    type: "boolean",
    live: true,
  },
  model_path: {
    defaultValue: "",
    type: "string",
    argKey: "model-path",
    restartRequired: true,
  },
  pspc_proposal_hint_file: {
    defaultValue: "",
    type: "string",
    argKey: "pspc-proposal-hint-file",
    restartRequired: true,
  },
  pspc_reply_preview_mode: {
    defaultValue: false,
    type: "boolean",
    argKey: "pspc-reply-preview-mode",
    restartRequired: true,
  },
  pspc_recording_mode: {
    defaultValue: false,
    type: "boolean",
    argKey: "pspc-recording-mode",
    restartRequired: true,
  },
  tts_enabled: {
    defaultValue: true,
    type: "boolean",
    live: true,
    invertedArgKey: "tts-disabled",
  },
  tts_max_chars: {
    defaultValue: 600,
    type: "positive_integer",
    argKey: "tts-max-chars",
    restartRequired: true,
  },
  tts_base_voice: {
    defaultValue: "zh-CN-XiaoxiaoNeural",
    type: "string",
    argKey: "tts-base-voice",
    restartRequired: true,
  },
  tts_model_name: {
    defaultValue: "Skadi_CN.pth",
    type: "string",
    argKey: "tts-model-name",
    restartRequired: true,
  },
  tts_timeout_ms: {
    defaultValue: 240000,
    type: "positive_integer",
    argKey: "tts-timeout-ms",
    restartRequired: true,
  },
  chat_timeout_ms: {
    defaultValue: 180000,
    type: "positive_integer",
    argKey: "chat-timeout-ms",
    restartRequired: true,
  },
};

const METADATA_FIELDS = new Set(["schema_version", "claim_ceiling"]);
const FIELD_NAMES = Object.keys(FIELD_SPECS);
const LIVE_FIELD_NAMES = FIELD_NAMES.filter((field) => FIELD_SPECS[field].live);

function developerSettingsFilePath(userDataDir) {
  return path.join(userDataDir, "developer-settings.json");
}

function defaultDeveloperSettings() {
  const settings = {
    schema_version: DEVELOPER_SETTINGS_SCHEMA_VERSION,
    claim_ceiling: DEVELOPER_SETTINGS_CLAIM_CEILING,
  };
  for (const [field, spec] of Object.entries(FIELD_SPECS)) {
    settings[field] = spec.defaultValue;
  }
  return settings;
}

function isPlainObject(value) {
  return value && typeof value === "object" && !Array.isArray(value);
}

function assertNoForbiddenFields(value) {
  if (!value || typeof value !== "object") {
    return;
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      assertNoForbiddenFields(item);
    }
    return;
  }
  for (const [key, child] of Object.entries(value)) {
    if (FORBIDDEN_FIELD_NAMES.has(key)) {
      throw new Error(`forbidden developer settings field: ${key}`);
    }
    assertNoForbiddenFields(child);
  }
}

function parseBoolean(value, field) {
  if (typeof value === "boolean") {
    return value;
  }
  if (value === "true") {
    return true;
  }
  if (value === "false") {
    return false;
  }
  throw new Error(`${field} must be boolean`);
}

function parsePositiveInteger(value, field) {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed <= 0) {
    throw new Error(`${field} must be a positive integer`);
  }
  return parsed;
}

function normalizeValue(field, value) {
  const spec = FIELD_SPECS[field];
  if (value === undefined || value === null || value === "") {
    return spec.defaultValue;
  }
  if (spec.type === "boolean") {
    return parseBoolean(value, field);
  }
  if (spec.type === "positive_integer") {
    return parsePositiveInteger(value, field);
  }
  if (spec.type === "string") {
    return String(value).trim();
  }
  return value;
}

function validateDeveloperSettings(input) {
  const raw = isPlainObject(input) ? input : {};
  assertNoForbiddenFields(raw);
  for (const key of Object.keys(raw)) {
    if (!METADATA_FIELDS.has(key) && !Object.prototype.hasOwnProperty.call(FIELD_SPECS, key)) {
      throw new Error(`unknown developer settings field: ${key}`);
    }
  }
  if (
    raw.schema_version !== undefined &&
    raw.schema_version !== DEVELOPER_SETTINGS_SCHEMA_VERSION
  ) {
    throw new Error(`schema_version must be ${DEVELOPER_SETTINGS_SCHEMA_VERSION}`);
  }
  if (
    raw.claim_ceiling !== undefined &&
    raw.claim_ceiling !== DEVELOPER_SETTINGS_CLAIM_CEILING
  ) {
    throw new Error(`claim_ceiling must be ${DEVELOPER_SETTINGS_CLAIM_CEILING}`);
  }
  const normalized = defaultDeveloperSettings();
  for (const field of FIELD_NAMES) {
    if (Object.prototype.hasOwnProperty.call(raw, field)) {
      normalized[field] = normalizeValue(field, raw[field]);
    }
  }
  return normalized;
}

function loadDeveloperSettings(settingsPath) {
  if (!fs.existsSync(settingsPath)) {
    return defaultDeveloperSettings();
  }
  const payload = JSON.parse(fs.readFileSync(settingsPath, "utf8"));
  return validateDeveloperSettings(payload);
}

function saveDeveloperSettings(settingsPath, settings) {
  const normalized = validateDeveloperSettings(settings);
  fs.mkdirSync(path.dirname(settingsPath), { recursive: true });
  fs.writeFileSync(settingsPath, `${JSON.stringify(normalized, null, 2)}\n`, "utf8");
  return normalized;
}

function cliHasField(cliArgs, spec) {
  if (spec.argKey && Object.prototype.hasOwnProperty.call(cliArgs, spec.argKey)) {
    return true;
  }
  if (spec.invertedArgKey && Object.prototype.hasOwnProperty.call(cliArgs, spec.invertedArgKey)) {
    return true;
  }
  if (spec.invertedArgKey === "tts-disabled" && Object.prototype.hasOwnProperty.call(cliArgs, "voice-disabled")) {
    return true;
  }
  return false;
}

function valueDiffersFromDefault(field, value) {
  return value !== FIELD_SPECS[field].defaultValue;
}

function applySettingToArgs(effectiveArgs, field, value) {
  const spec = FIELD_SPECS[field];
  if (spec.invertedArgKey) {
    if (field === "tts_enabled" && value === false) {
      effectiveArgs[spec.invertedArgKey] = true;
    }
    return;
  }
  if (spec.argKey && spec.type === "boolean") {
    if (value === true) {
      effectiveArgs[spec.argKey] = true;
    }
    return;
  }
  if (spec.argKey && valueDiffersFromDefault(field, value)) {
    effectiveArgs[spec.argKey] = value;
  }
}

function buildEffectiveLaunchProfile(options) {
  const settingsPath = options && options.settingsPath ? String(options.settingsPath) : "";
  const cliArgs = { ...((options && options.cliArgs) || {}) };
  const smoke = Boolean(cliArgs.smoke || (options && options.smoke));
  const savedSettings = smoke
    ? defaultDeveloperSettings()
    : (options && options.settings ? validateDeveloperSettings(options.settings) : loadDeveloperSettings(settingsPath));
  const effectiveArgs = { ...cliArgs };
  const sourceByField = {};

  for (const field of FIELD_NAMES) {
    const spec = FIELD_SPECS[field];
    const value = savedSettings[field];
    if (smoke) {
      sourceByField[field] = cliHasField(cliArgs, spec) ? "cli_override" : "default";
      continue;
    }
    if (cliHasField(cliArgs, spec)) {
      sourceByField[field] = "cli_override";
      continue;
    }
    if (valueDiffersFromDefault(field, value)) {
      applySettingToArgs(effectiveArgs, field, value);
      sourceByField[field] = "saved";
      continue;
    }
    sourceByField[field] = "default";
  }

  return {
    settings: savedSettings,
    effectiveArgs,
    report: {
      schema_version: "ego_desktop.effective_launch_config.v0",
      claim_ceiling: DEVELOPER_SETTINGS_CLAIM_CEILING,
      settings_path: settingsPath,
      persistent_settings_ignored: smoke,
      developer_mode_enabled: Boolean(savedSettings.developer_mode_enabled),
      source_by_field: sourceByField,
      requires_restart: Object.fromEntries(
        FIELD_NAMES.map((field) => [field, Boolean(FIELD_SPECS[field].restartRequired)])
      ),
      live_fields: LIVE_FIELD_NAMES,
      side_effects_absent: {
        memory_write: false,
        gate_invoked: false,
        approval_invoked: false,
        transport_called: false,
        proactive_triggered: false,
        runtime_registered: false,
        pspc_mainline_connected: false,
      },
    },
  };
}

function buildLiveDeveloperSettingsUpdate({ currentSettings, requestedSettings }) {
  const current = validateDeveloperSettings(currentSettings || {});
  const requested = validateDeveloperSettings(requestedSettings || {});
  const applied = { ...current };
  const restartRequiredFields = [];
  for (const field of FIELD_NAMES) {
    if (LIVE_FIELD_NAMES.includes(field)) {
      applied[field] = requested[field];
    } else if (requested[field] !== current[field]) {
      restartRequiredFields.push(field);
    }
  }
  return {
    schema_version: "ego_desktop.live_developer_settings_update.v0",
    claim_ceiling: DEVELOPER_SETTINGS_CLAIM_CEILING,
    applied,
    restart_required_fields: restartRequiredFields,
    side_effects_absent: {
      memory_write: false,
      gate_invoked: false,
      approval_invoked: false,
      transport_called: false,
      proactive_triggered: false,
      runtime_registered: false,
      pspc_mainline_connected: false,
    },
  };
}

module.exports = {
  DEVELOPER_SETTINGS_CLAIM_CEILING,
  DEVELOPER_SETTINGS_SCHEMA_VERSION,
  FIELD_SPECS,
  buildEffectiveLaunchProfile,
  buildLiveDeveloperSettingsUpdate,
  defaultDeveloperSettings,
  developerSettingsFilePath,
  loadDeveloperSettings,
  saveDeveloperSettings,
  validateDeveloperSettings,
};
