const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const {
  DEVELOPER_SETTINGS_CLAIM_CEILING,
  DEVELOPER_SETTINGS_SCHEMA_VERSION,
  buildEffectiveLaunchProfile,
  buildLiveDeveloperSettingsUpdate,
  defaultDeveloperSettings,
  developerSettingsFilePath,
  loadDeveloperSettings,
  saveDeveloperSettings,
  validateDeveloperSettings,
} = require("../src/developerSettings");

const repoRoot = path.resolve(__dirname, "..", "..");

function tempSettingsPath() {
  return path.join(fs.mkdtempSync(path.join(os.tmpdir(), "ego-desktop-dev-settings-")), "developer-settings.json");
}

test("developer settings load defaults when no settings file exists", () => {
  const settingsPath = tempSettingsPath();
  const loaded = loadDeveloperSettings(settingsPath);

  assert.equal(loaded.schema_version, DEVELOPER_SETTINGS_SCHEMA_VERSION);
  assert.equal(loaded.claim_ceiling, DEVELOPER_SETTINGS_CLAIM_CEILING);
  assert.equal(loaded.developer_mode_enabled, false);
  assert.equal(loaded.tts_enabled, true);
  assert.equal(loaded.pspc_reply_preview_mode, false);
});

test("developer settings save and reload selected launch profile fields", () => {
  const settingsPath = tempSettingsPath();
  saveDeveloperSettings(settingsPath, {
    developer_mode_enabled: true,
    model_path: "D:/models/yuno.model3.json",
    pspc_proposal_hint_file: "../artifacts/pspc_shadow_proposal_hint_contract_v0/proposal_hint_contract.json",
    pspc_reply_preview_mode: true,
    pspc_recording_mode: true,
    tts_enabled: false,
    tts_max_chars: 320,
    tts_base_voice: "zh-CN-XiaoxiaoNeural",
    tts_model_name: "Skadi_CN.pth",
    tts_timeout_ms: 180000,
    chat_timeout_ms: 120000,
    debug_overlay_default_visible: true,
  });

  const loaded = loadDeveloperSettings(settingsPath);
  assert.equal(loaded.developer_mode_enabled, true);
  assert.equal(loaded.model_path, "D:/models/yuno.model3.json");
  assert.equal(loaded.pspc_reply_preview_mode, true);
  assert.equal(loaded.tts_enabled, false);
  assert.equal(loaded.debug_overlay_default_visible, true);
});

test("developer settings reject unknown executable or authority fields", () => {
  assert.throws(
    () => validateDeveloperSettings({ action: "send" }),
    /forbidden developer settings field/
  );
  assert.throws(
    () => validateDeveloperSettings({ memory_write: true }),
    /forbidden developer settings field/
  );
  assert.throws(
    () => validateDeveloperSettings({ enabled: true }),
    /forbidden developer settings field/
  );
  assert.throws(
    () => validateDeveloperSettings({ unexpected_field: true }),
    /unknown developer settings field/
  );
});

test("saved settings affect startup args while explicit CLI args override saved values", () => {
  const settingsPath = tempSettingsPath();
  saveDeveloperSettings(settingsPath, {
    ...defaultDeveloperSettings(),
    model_path: "saved.model3.json",
    pspc_reply_preview_mode: true,
    pspc_proposal_hint_file: "saved-proposal.json",
    tts_enabled: false,
    tts_max_chars: 300,
    chat_timeout_ms: 150000,
  });

  const profile = buildEffectiveLaunchProfile({
    settingsPath,
    cliArgs: {
      "model-path": "cli.model3.json",
      "tts-max-chars": "500",
    },
  });

  assert.equal(profile.effectiveArgs["model-path"], "cli.model3.json");
  assert.equal(profile.effectiveArgs["pspc-reply-preview-mode"], true);
  assert.equal(profile.effectiveArgs["pspc-proposal-hint-file"], "saved-proposal.json");
  assert.equal(profile.effectiveArgs["tts-disabled"], true);
  assert.equal(profile.effectiveArgs["tts-max-chars"], "500");
  assert.equal(profile.effectiveArgs["chat-timeout-ms"], 150000);
  assert.equal(profile.report.source_by_field.model_path, "cli_override");
  assert.equal(profile.report.source_by_field.pspc_reply_preview_mode, "saved");
  assert.equal(profile.report.source_by_field.tts_max_chars, "cli_override");
});

test("smoke mode ignores persisted developer settings", () => {
  const settingsPath = tempSettingsPath();
  saveDeveloperSettings(settingsPath, {
    ...defaultDeveloperSettings(),
    model_path: "saved.model3.json",
    pspc_reply_preview_mode: true,
    tts_enabled: false,
  });

  const profile = buildEffectiveLaunchProfile({
    settingsPath,
    cliArgs: {
      smoke: true,
      "model-path": "smoke.model3.json",
    },
  });

  assert.equal(profile.effectiveArgs["model-path"], "smoke.model3.json");
  assert.equal(profile.effectiveArgs["pspc-reply-preview-mode"], undefined);
  assert.equal(profile.effectiveArgs["tts-disabled"], undefined);
  assert.equal(profile.report.persistent_settings_ignored, true);
});

test("live developer settings update only admits safe live fields", () => {
  const current = defaultDeveloperSettings();
  const live = buildLiveDeveloperSettingsUpdate({
    currentSettings: current,
    requestedSettings: {
      ...current,
      developer_mode_enabled: true,
      debug_overlay_default_visible: true,
      tts_enabled: false,
      model_path: "changed.model3.json",
      pspc_reply_preview_mode: true,
      chat_timeout_ms: 100000,
    },
  });

  assert.equal(live.applied.developer_mode_enabled, true);
  assert.equal(live.applied.debug_overlay_default_visible, true);
  assert.equal(live.applied.tts_enabled, false);
  assert.deepEqual(live.restart_required_fields.sort(), [
    "chat_timeout_ms",
    "model_path",
    "pspc_reply_preview_mode",
  ]);
  assert.equal(live.side_effects_absent.memory_write, false);
  assert.equal(live.side_effects_absent.gate_invoked, false);
});

test("developer settings file path stays under Electron userData", () => {
  const userData = path.join(os.tmpdir(), "ego-desktop-user-data");
  assert.equal(
    developerSettingsFilePath(userData),
    path.join(userData, "developer-settings.json")
  );
});

test("EgoDesktop exposes developer settings UI and IPC without runtime authority", () => {
  const html = fs.readFileSync(path.join(repoRoot, "EgoDesktop", "viewer", "index.html"), "utf8");
  const settingsHtml = fs.readFileSync(path.join(repoRoot, "EgoDesktop", "viewer", "settings.html"), "utf8");
  const settingsJs = fs.readFileSync(path.join(repoRoot, "EgoDesktop", "viewer", "settings.js"), "utf8");
  const preload = fs.readFileSync(path.join(repoRoot, "EgoDesktop", "src", "preload.js"), "utf8");
  const main = fs.readFileSync(path.join(repoRoot, "EgoDesktop", "src", "main.js"), "utf8");

  assert.equal(html.includes("settings-button"), true);
  assert.equal(settingsHtml.includes("developer-mode-toggle"), true);
  assert.equal(settingsHtml.includes("developer-options"), true);
  assert.equal(settingsHtml.includes("重启后生效"), true);
  assert.equal(settingsJs.includes("getDeveloperSettings"), true);
  assert.equal(settingsJs.includes("saveDeveloperSettings"), true);
  assert.equal(settingsJs.includes("applyLiveDeveloperSettings"), true);
  assert.equal(preload.includes("openDeveloperSettings"), true);
  assert.equal(preload.includes("getEffectiveLaunchConfig"), true);
  assert.equal(main.includes("ego-desktop:save-developer-settings"), true);
  assert.equal(main.includes("ego-desktop:apply-live-developer-settings"), true);
  assert.equal(main.includes("developer-settings.json"), false);
});
