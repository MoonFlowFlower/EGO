(async function bootSettings() {
  const form = document.getElementById("settings-form");
  const status = document.getElementById("settings-status");
  const developerModeToggle = document.getElementById("developer-mode-toggle");
  const developerOptions = document.getElementById("developer-options");

  const fieldIds = {
    developer_mode_enabled: "developer-mode-toggle",
    debug_overlay_default_visible: "debug-overlay-default-visible",
    model_path: "model-path",
    pspc_proposal_hint_file: "pspc-proposal-hint-file",
    pspc_reply_preview_mode: "pspc-reply-preview-mode",
    pspc_recording_mode: "pspc-recording-mode",
    tts_enabled: "tts-enabled",
    tts_max_chars: "tts-max-chars",
    tts_base_voice: "tts-base-voice",
    tts_model_name: "tts-model-name",
    tts_timeout_ms: "tts-timeout-ms",
    chat_timeout_ms: "chat-timeout-ms",
  };

  function setStatus(text, className) {
    if (!status) {
      return;
    }
    status.textContent = text;
    status.className = className || "";
  }

  function setDeveloperOptionsVisible(visible) {
    if (developerOptions) {
      developerOptions.hidden = !visible;
    }
  }

  function fieldElement(field) {
    return document.getElementById(fieldIds[field]);
  }

  function writeField(field, value) {
    const element = fieldElement(field);
    if (!element) {
      return;
    }
    if (element.type === "checkbox") {
      element.checked = Boolean(value);
      return;
    }
    element.value = value === undefined || value === null ? "" : String(value);
  }

  function readField(field) {
    const element = fieldElement(field);
    if (!element) {
      return "";
    }
    if (element.type === "checkbox") {
      return Boolean(element.checked);
    }
    if (element.type === "number") {
      return Number(element.value);
    }
    return String(element.value || "").trim();
  }

  function readSettings() {
    return Object.fromEntries(Object.keys(fieldIds).map((field) => [field, readField(field)]));
  }

  function populate(settings) {
    for (const field of Object.keys(fieldIds)) {
      writeField(field, settings[field]);
    }
    setDeveloperOptionsVisible(Boolean(settings.developer_mode_enabled));
  }

  if (!form || !window.egoDesktop || typeof window.egoDesktop.getDeveloperSettings !== "function") {
    setStatus("settings unavailable", "error");
    return;
  }

  try {
    const response = await window.egoDesktop.getDeveloperSettings();
    populate(response.settings || {});
    setStatus("已载入");
  } catch (error) {
    setStatus("载入失败: " + error.message, "error");
  }

  if (developerModeToggle) {
    developerModeToggle.addEventListener("change", () => {
      setDeveloperOptionsVisible(Boolean(developerModeToggle.checked));
    });
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const settings = readSettings();
      const saved = await window.egoDesktop.saveDeveloperSettings({ settings });
      const live = await window.egoDesktop.applyLiveDeveloperSettings({ settings: saved.settings });
      populate(saved.settings || {});
      const restartFields = live && Array.isArray(live.restart_required_fields)
        ? live.restart_required_fields.length
        : 0;
      setStatus(restartFields > 0 ? "已保存，部分设置重启后生效" : "已保存");
    } catch (error) {
      setStatus("保存失败: " + error.message, "error");
    }
  });
})();
