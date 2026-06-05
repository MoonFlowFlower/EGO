(async function bootLive2D() {
  const stage = document.getElementById("stage");
  const canvas = document.getElementById("live2d-canvas");
  const status = document.getElementById("status");
  const chatForm = document.getElementById("chat-form");
  const userInput = document.getElementById("user-input");
  const sendButton = document.getElementById("send-button");
  const chatOutput = document.getElementById("chat-output");
  const pspcDemoPanel = document.getElementById("pspc-demo-panel");
  const pspcScenarioSelect = document.getElementById("pspc-scenario-select");
  const pspcSameTrigger = document.getElementById("pspc-same-trigger");
  const pspcPlaybackButton = document.getElementById("pspc-playback-button");
  const pspcDebugToggle = document.getElementById("pspc-debug-toggle");
  const pspcDebugOverlay = document.getElementById("pspc-debug-overlay");
  const pspcBubble = document.getElementById("pspc-bubble");
  const pspcTrace = document.getElementById("pspc-trace");
  const voiceBar = document.getElementById("voice-bar");
  const voiceToggle = document.getElementById("voice-toggle");
  const stopVoiceButton = document.getElementById("stop-voice");
  const voiceStatus = document.getElementById("voice-status");
  let mouthAnimationUntil = 0;
  let speechActive = false;
  let voiceEnabled = true;
  let currentAudio = null;
  let ttsRequestPending = false;
  let pspcDebugOverlayToggleReady = false;
  const speechTurns = window.EgoDesktopSpeechTurns && typeof window.EgoDesktopSpeechTurns.createSpeechTurnGuard === "function"
    ? window.EgoDesktopSpeechTurns.createSpeechTurnGuard()
    : {
      startTurn: () => Date.now(),
      isCurrent: () => true,
      currentTurnId: () => 0,
      supersededResult: (turnId) => ({
        status: "speech_superseded",
        speech_turn_id: Number(turnId) || 0,
        current_speech_turn_id: 0,
        side_effects_executed: false,
        ui_audio_delivery_executed: false,
        memory_write: false,
        tool_use: false,
        message_send: false,
        file_write: false,
        network_call: false,
      }),
    };

  const RENDER_MODE = "official_live2d_model_from";
  const IDLE_MOUTH_PARAMETERS = {
    ParamMouthForm: -1,
    ParamMouthOpenY: 0,
    ParamJawOpen: 0,
    ParamMouthPressLipOpen: 0,
    ParamMouthPuckerWiden: 0,
    ParamMouthShrug: 0,
    ParamMouthX: 0,
  };

  function setStatus(text, className) {
    status.textContent = text;
    status.className = className || "";
  }

  function reportReady(payload) {
    if (window.egoDesktop && typeof window.egoDesktop.reportReady === "function") {
      window.egoDesktop.reportReady(payload);
    }
  }

  function cubismIdToString(cubismId) {
    try {
      const raw = cubismId && typeof cubismId.getString === "function" ? cubismId.getString() : cubismId;
      if (raw && typeof raw.s === "string") {
        return raw.s;
      }
      return String(raw || "");
    } catch (_error) {
      return "";
    }
  }

  function findParameterIndex(coreModel, id) {
    if (!coreModel || typeof coreModel.getParameterCount !== "function" || typeof coreModel.getParameterId !== "function") {
      return -1;
    }
    for (let index = 0; index < coreModel.getParameterCount(); index += 1) {
      if (cubismIdToString(coreModel.getParameterId(index)) === id) {
        return index;
      }
    }
    return -1;
  }

  function setParameter(model, id, value) {
    try {
      const coreModel = model && model.internalModel && model.internalModel.coreModel;
      const index = findParameterIndex(coreModel, id);
      if (coreModel && typeof coreModel.setParameterValueByIndex === "function" && index >= 0) {
        coreModel.setParameterValueByIndex(index, value);
      }
    } catch (_error) {
      // Some models do not expose every VTube/Cubism parameter.
    }
  }

  function getParameter(model, id) {
    try {
      const coreModel = model && model.internalModel && model.internalModel.coreModel;
      const index = findParameterIndex(coreModel, id);
      if (coreModel && typeof coreModel.getParameterValueByIndex === "function" && index >= 0) {
        return coreModel.getParameterValueByIndex(index);
      }
    } catch (_error) {
      return null;
    }
    return null;
  }

  function partIdToString(partId) {
    return cubismIdToString(partId);
  }

  function findPartIndex(coreModel, id) {
    if (!coreModel || typeof coreModel.getPartCount !== "function" || typeof coreModel.getPartId !== "function") {
      return -1;
    }
    for (let index = 0; index < coreModel.getPartCount(); index += 1) {
      if (partIdToString(coreModel.getPartId(index)) === id) {
        return index;
      }
    }
    return -1;
  }

  function getPartOpacity(model, id) {
    try {
      const coreModel = model && model.internalModel && model.internalModel.coreModel;
      const index = findPartIndex(coreModel, id);
      if (coreModel && typeof coreModel.getPartOpacityByIndex === "function" && index >= 0) {
        return coreModel.getPartOpacityByIndex(index);
      }
    } catch (_error) {
      return null;
    }
    return null;
  }

  function applyIdleMouth(model) {
    for (const [id, value] of Object.entries(IDLE_MOUTH_PARAMETERS)) {
      setParameter(model, id, value);
    }
  }

  function applyMouthState(model) {
    const now = performance.now();
    applyIdleMouth(model);
    if (speechActive) {
      const pulse = (Math.sin(now / 70) + 1) / 2;
      setParameter(model, "ParamMouthOpenY", 0.05 + pulse * 0.15);
      setParameter(model, "ParamJawOpen", pulse * 0.07);
      return;
    }
    if (mouthAnimationUntil <= now) {
      return;
    }
    const remaining = Math.max(0, mouthAnimationUntil - now);
    const progress = 1 - Math.min(1, remaining / 700);
    setParameter(model, "ParamMouthOpenY", Math.sin(progress * Math.PI) * 0.18);
    setParameter(model, "ParamJawOpen", Math.sin(progress * Math.PI) * 0.08);
  }

  function withTimeout(promise, timeoutMs, label) {
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => reject(new Error(label + "_timeout")), timeoutMs);
      Promise.resolve(promise).then((value) => {
        clearTimeout(timeout);
        resolve(value);
      }).catch((error) => {
        clearTimeout(timeout);
        reject(error);
      });
    });
  }

  async function applyNamedExpression(model, name) {
    const expressionName = String(name || "").trim();
    if (!expressionName) {
      return false;
    }
    try {
      if (typeof model.expression === "function") {
        await withTimeout(model.expression(expressionName), 1600, "live2d_expression");
        return true;
      }
    } catch (_error) {
      return false;
    }
    return false;
  }

  function applyWatermarkOff(model, config) {
    const value = Number.isFinite(Number(config && config.watermarkParamValue))
      ? Number(config.watermarkParamValue)
      : 1;
    setParameter(model, "Param85", value);
  }

  function appendMessage(role, text, className) {
    const message = document.createElement("div");
    message.className = ["message", role, className || ""].filter(Boolean).join(" ");
    const label = document.createElement("div");
    label.className = "message-label";
    label.textContent = role === "user" ? "You" : "Bot";
    const body = document.createElement("div");
    body.className = "message-text";
    body.textContent = text;
    message.append(label, body);
    chatOutput.appendChild(message);
    chatOutput.scrollTop = chatOutput.scrollHeight;
    return body;
  }

  function setVoiceStatus(text, className) {
    if (!voiceStatus) {
      return;
    }
    voiceStatus.textContent = text;
    voiceStatus.className = className || "";
  }

  function setVoiceEnabled(enabled) {
    voiceEnabled = Boolean(enabled);
    if (voiceToggle) {
      voiceToggle.setAttribute("aria-pressed", voiceEnabled ? "true" : "false");
      voiceToggle.textContent = voiceEnabled ? "语音开" : "语音关";
    }
    if (!voiceEnabled) {
      stopSpeech();
      setVoiceStatus("语音已关闭");
    } else {
      setVoiceStatus("语音待机");
    }
  }

  function stopSpeech(options) {
    const settings = options || {};
    speechActive = false;
    if (currentAudio) {
      try {
        currentAudio.pause();
        currentAudio.currentTime = 0;
      } catch (_error) {
        // Playback cleanup is best effort.
      }
      currentAudio = null;
    }
    if (
      settings.cancelWorker !== false &&
      ttsRequestPending &&
      window.egoDesktop &&
      typeof window.egoDesktop.cancelSpeech === "function"
    ) {
      window.egoDesktop.cancelSpeech().catch(() => {});
    }
  }

  async function playAudioUrl(audioUrl) {
    if (!audioUrl) {
      return "audio_url_missing";
    }
    stopSpeech({ cancelWorker: false });
    const audio = new Audio(audioUrl);
    currentAudio = audio;
    speechActive = true;
    audio.addEventListener("ended", () => {
      if (currentAudio === audio) {
        speechActive = false;
        currentAudio = null;
        setVoiceStatus("语音待机");
      }
    });
    audio.addEventListener("error", () => {
      if (currentAudio === audio) {
        speechActive = false;
        currentAudio = null;
        setVoiceStatus("播放失败", "error");
      }
    });
    try {
      await audio.play();
      return "playing";
    } catch (error) {
      speechActive = false;
      return "playback_unavailable: " + error.message;
    }
  }

  async function speakTurn(turn, config, options) {
    const settings = options || {};
    const speechTurnId = settings.speechTurnId === undefined ? speechTurns.startTurn() : settings.speechTurnId;
    if (!voiceEnabled || !window.egoDesktop || typeof window.egoDesktop.synthesizeSpeech !== "function") {
      return {
        status: "voice_disabled",
        speech_turn_id: speechTurnId,
        ui_audio_delivery_executed: false,
        memory_write: false,
        tool_use: false,
        message_send: false,
      };
    }
    const requestId = "turn_" + Date.now().toString(36);
    setVoiceStatus("语音合成中...");
    let result;
    ttsRequestPending = true;
    try {
      result = await window.egoDesktop.synthesizeSpeech({
        turn,
        voiceEnabled,
        requestId,
      });
    } finally {
      ttsRequestPending = false;
    }
    if (!speechTurns.isCurrent(speechTurnId)) {
      return speechTurns.supersededResult(speechTurnId);
    }
    if (!result || result.status !== "ok") {
      const statusText = result && result.status ? result.status : "tts_unavailable";
      setVoiceStatus(statusText, statusText.includes("unavailable") || statusText.includes("error") ? "error" : "");
      return result || { status: "tts_unavailable", ui_audio_delivery_executed: false };
    }
    setVoiceStatus("正在播放");
    const playbackStatus = settings.playAudio === false ? "not_played" : (
      speechTurns.isCurrent(speechTurnId) ? await playAudioUrl(result.audio_url) : "speech_superseded"
    );
    if (!speechTurns.isCurrent(speechTurnId)) {
      return speechTurns.supersededResult(speechTurnId);
    }
    return {
      ...result,
      speech_turn_id: speechTurnId,
      playback_status: playbackStatus,
    };
  }

  function setupChat(model, config) {
    if (config && config.pspcPerceptionDemo && !config.pspcReplyPreviewMode) {
      if (chatForm) {
        chatForm.hidden = true;
      }
      if (voiceBar) {
        voiceBar.hidden = true;
      }
      return;
    }
    if (!chatForm || !userInput || !sendButton || !window.egoDesktop || typeof window.egoDesktop.sendChatTurn !== "function") {
      return;
    }
    setVoiceEnabled(config && config.voiceEnabled !== false);
    if (voiceToggle) {
      voiceToggle.addEventListener("click", () => {
        setVoiceEnabled(!voiceEnabled);
      });
    }
    if (stopVoiceButton) {
      stopVoiceButton.addEventListener("click", () => {
        stopSpeech();
        setVoiceStatus("语音已停止");
      });
    }
    chatForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const userText = userInput.value.trim();
      if (!userText) {
        return;
      }
      const speechTurnId = speechTurns.startTurn();
      stopSpeech();
      userInput.value = "";
      appendMessage("user", userText);
      const pendingBody = appendMessage("bot", "...");
      sendButton.disabled = true;
      userInput.disabled = true;
      try {
        const turn = await window.egoDesktop.sendChatTurn({ userText });
        pendingBody.textContent = turn && turn.bot_text ? turn.bot_text : "llm_expression_unavailable: empty_reply";
        const visibleBotText = pendingBody.textContent.trim();
        if (turn && turn.status !== "ok") {
          pendingBody.parentElement.classList.add("error");
        }
        if (turn && turn.expression_name) {
          await applyNamedExpression(model, turn.expression_name);
        }
        if (turn && turn.pspc_reply_preview_scenario) {
          if (pspcDemoPanel) {
            pspcDemoPanel.hidden = false;
          }
          renderPspcDebugOverlay({
            claim_ceiling: "local_reply_preview_observability_only",
            debug_overlay: turn.pspc_reply_preview_scenario.debug_overlay || null,
          }, turn.pspc_reply_preview_scenario);
          await applyPspcScenario(model, turn.pspc_reply_preview_scenario);
        }
        if (turn && turn.status === "ok") {
          speakTurn({
            ...turn,
            visible_bot_text: visibleBotText,
            displayed_text: visibleBotText,
          }, config, { speechTurnId }).catch((error) => {
            setVoiceStatus("语音失败: " + error.message, "error");
          });
        } else {
          setVoiceStatus("错误回复不朗读");
        }
        mouthAnimationUntil = performance.now() + 700;
        applyWatermarkOff(model, config);
      } catch (error) {
        pendingBody.textContent = "llm_expression_unavailable: " + error.message;
        pendingBody.parentElement.classList.add("error");
        await applyNamedExpression(model, "晕晕眼");
        applyWatermarkOff(model, config);
      } finally {
        sendButton.disabled = false;
        userInput.disabled = false;
        userInput.focus();
      }
    });
    userInput.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" || event.shiftKey || event.isComposing || userInput.disabled) {
        return;
      }
      event.preventDefault();
      if (typeof chatForm.requestSubmit === "function") {
        chatForm.requestSubmit();
      } else {
        sendButton.click();
      }
    });
  }

  async function applyPspcScenario(model, scenario) {
    if (!scenario || !scenario.visual_profile) {
      return;
    }
    const profile = scenario.visual_profile;
    if (pspcBubble) {
      pspcBubble.textContent = String(profile.bubble_text || "");
    }
    if (pspcTrace) {
      pspcTrace.textContent = [
        String(scenario.title || ""),
        String(scenario.trigger_text || ""),
        String(scenario.packet_id || ""),
        String(profile.motion_hint || ""),
        String(scenario.confidence_tag || ""),
        String(profile.trace_explanation || ""),
      ].filter(Boolean).join(" | ");
    }
    const expressionNameByHint = {
      smile_soft: "星星眼",
      cautious: "黑脸",
      quiet_care: "记笔记",
      hesitate_observe: "晕晕眼",
    };
    const expressionName = expressionNameByHint[String(profile.expression_hint || "")] || "";
    if (expressionName) {
      await applyNamedExpression(model, expressionName);
    }
  }

  function setPspcDebugOverlayVisible(visible) {
    if (!pspcDebugOverlay || !pspcDebugToggle) {
      return;
    }
    pspcDebugOverlay.hidden = !visible;
    pspcDebugToggle.setAttribute("aria-pressed", visible ? "true" : "false");
  }

  function setupPspcDebugOverlayToggle() {
    if (!pspcDebugOverlay || !pspcDebugToggle || pspcDebugOverlayToggleReady) {
      return;
    }
    pspcDebugOverlay.hidden = true;
    pspcDebugToggle.setAttribute("aria-pressed", "false");
    pspcDebugToggle.addEventListener("click", () => {
      setPspcDebugOverlayVisible(pspcDebugOverlay.hidden);
    });
    pspcDebugOverlayToggleReady = true;
  }

  function renderPspcDebugOverlay(demo, scenario) {
    if (!pspcDebugOverlay || !scenario) {
      return;
    }
    const overlay = demo && demo.debug_overlay && typeof demo.debug_overlay === "object"
      ? demo.debug_overlay
      : {};
    const rows = Array.isArray(overlay.rows)
      ? overlay.rows
      : [];
    const row = rows.find((item) => String(item.packet_id || "") === String(scenario.packet_id || "")) || {};
    const historyCounts = row.history_counts && typeof row.history_counts === "object"
      ? row.history_counts
      : {};
    const recentCategories = Array.isArray(row.recent_categories)
      ? row.recent_categories
      : [];
    const proxyBars = Array.isArray(overlay.proxy_bars) ? overlay.proxy_bars : [];
    const barLines = proxyBars.map((bar) => {
      const value = Math.max(0, Math.min(1, Number(bar.value || 0)));
      const filled = Math.round(value * 10);
      const empty = Math.max(0, 10 - filled);
      return `${String(bar.label || bar.id || "").padEnd(24, " ")} [${"#".repeat(filled)}${".".repeat(empty)}] ${value.toFixed(2)}`;
    });
    pspcDebugOverlay.textContent = [
      String(overlay.label || "PSPC preview proxy"),
      `signal_status: ${String(overlay.signal_status || "PSPC signal inactive / neutral")}`,
      `packet_id: ${String(row.packet_id || scenario.packet_id || "")}`,
      `style: ${String(row.style || scenario.style || scenario.perception_behavior || "")}`,
      `confidence: ${String(row.confidence !== undefined ? row.confidence : scenario.confidence || "")}`,
      `basis: ${String(row.basis || scenario.basis || "")}`,
      `history_counts: gentle=${Number(historyCounts.gentle || 0)} interruption=${Number(historyCounts.interruption || 0)} late_night=${Number(historyCounts.late_night || 0)} neutral=${Number(historyCounts.neutral || 0)}`,
      `recent_categories: ${recentCategories.join(", ")}`,
      `reason_trace_refs: ${Array.isArray(row.reason_trace_refs)
        ? row.reason_trace_refs.join(", ")
        : (Array.isArray(scenario.reason_trace_refs) ? scenario.reason_trace_refs.join(", ") : "")}`,
      `claim_ceiling: ${String(row.claim_ceiling || overlay.claim_ceiling || demo.claim_ceiling || "")}`,
      ...barLines,
    ].join("\n");
  }

  function setupPspcPerceptionDemo(model, config) {
    const demo = config && config.pspcPerceptionDemo;
    const scenarios = demo && Array.isArray(demo.scenarios) ? demo.scenarios : [];
    if (!pspcDemoPanel || !pspcScenarioSelect || !pspcBubble || scenarios.length === 0) {
      return false;
    }
    pspcDemoPanel.hidden = false;
    if (pspcSameTrigger) {
      pspcSameTrigger.textContent = String(demo.trigger_text || "");
    }
    if (pspcDebugOverlay) {
      pspcDebugOverlay.hidden = true;
    }
    setupPspcDebugOverlayToggle();
    pspcScenarioSelect.textContent = "";
    scenarios.forEach((scenario, index) => {
      const option = document.createElement("option");
      option.value = String(index);
      option.textContent = `${scenario.title} / ${scenario.perception_behavior}`;
      pspcScenarioSelect.appendChild(option);
    });

    let playbackTimers = [];
    const clearPlaybackTimers = () => {
      for (const timer of playbackTimers) {
        clearTimeout(timer);
      }
      playbackTimers = [];
    };
    const selectIndex = (index) => {
      const safeIndex = Math.max(0, Math.min(scenarios.length - 1, Number(index) || 0));
      pspcScenarioSelect.value = String(safeIndex);
      const scenario = scenarios[safeIndex] || scenarios[0];
      renderPspcDebugOverlay(demo, scenario);
      applyPspcScenario(model, scenario).catch(() => {});
    };
    pspcScenarioSelect.addEventListener("change", () => {
      clearPlaybackTimers();
      selectIndex(Number(pspcScenarioSelect.value || 0));
    });
    if (pspcPlaybackButton) {
      pspcPlaybackButton.addEventListener("click", () => {
        clearPlaybackTimers();
        const steps = demo && Array.isArray(demo.playback) ? demo.playback : [];
        for (const step of steps) {
          const index = scenarios.findIndex((scenario) => scenario.demo_id === step.demo_id);
          if (index < 0) {
            continue;
          }
          playbackTimers.push(setTimeout(() => selectIndex(index), Number(step.start_ms) || 0));
        }
      });
    }
    selectIndex(0);
    return true;
  }

  function setupPspcVisualShim(model, config) {
    const shim = config && config.pspcVisualShim;
    const scenarios = shim && Array.isArray(shim.scenarios) ? shim.scenarios : [];
    if (!pspcDemoPanel || !pspcScenarioSelect || !pspcBubble || scenarios.length === 0) {
      return false;
    }
    pspcDemoPanel.hidden = false;
    if (pspcSameTrigger) {
      pspcSameTrigger.textContent = "";
    }
    if (pspcDebugOverlay) {
      pspcDebugOverlay.hidden = true;
    }
    setupPspcDebugOverlayToggle();
    pspcScenarioSelect.textContent = "";
    scenarios.forEach((scenario, index) => {
      const option = document.createElement("option");
      option.value = String(index);
      option.textContent = `${scenario.packet_id} / ${scenario.visual_profile.behavior_state}`;
      pspcScenarioSelect.appendChild(option);
    });
    const selectCurrent = () => {
      const index = Number(pspcScenarioSelect.value || 0);
      applyPspcScenario(model, scenarios[index] || scenarios[0]).catch(() => {});
    };
    pspcScenarioSelect.addEventListener("change", selectCurrent);
    selectCurrent();
    return true;
  }

  function rendererResolution() {
    return 1;
  }

  async function createPixiApplication(targetCanvas, resizeTarget) {
    const options = {
      view: targetCanvas,
      canvas: targetCanvas,
      resizeTo: resizeTarget || window,
      antialias: true,
      autoDensity: true,
      resolution: rendererResolution(),
      backgroundAlpha: 0,
      transparent: true,
      preserveDrawingBuffer: true,
      preference: "webgl",
      autoStart: true,
    };
    const app = new window.PIXI.Application(
      window.PIXI.Application.prototype && typeof window.PIXI.Application.prototype.init === "function"
        ? undefined
        : options
    );
    if (typeof app.init === "function") {
      await app.init(options);
    }
    targetCanvas.style.transformOrigin = "";
    targetCanvas.style.transform = "";
    return app;
  }

  function drawModelFrame(app) {
    if (typeof app.render === "function") {
      app.render();
    }
    const gl = app.renderer && app.renderer.gl;
    if (gl && typeof gl.flush === "function") {
      gl.flush();
    }
  }

  function pixelAt(pixels, width, x, y) {
    const offset = (y * width + x) * 4;
    return [
      pixels[offset],
      pixels[offset + 1],
      pixels[offset + 2],
      pixels[offset + 3],
    ];
  }

  function readCanvasPixelBounds(targetCanvas) {
    const gl = targetCanvas.getContext("webgl2") || targetCanvas.getContext("webgl");
    if (!gl) {
      return { available: false, nonTransparentPixels: 0 };
    }
    const width = gl.drawingBufferWidth;
    const height = gl.drawingBufferHeight;
    const pixels = new Uint8Array(width * height * 4);
    gl.readPixels(0, 0, width, height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
    const corners = [
      pixelAt(pixels, width, 0, 0),
      pixelAt(pixels, width, width - 1, 0),
      pixelAt(pixels, width, 0, height - 1),
      pixelAt(pixels, width, width - 1, height - 1),
    ];
    const background = corners.reduce((acc, item) => {
      acc[0] += item[0] / corners.length;
      acc[1] += item[1] / corners.length;
      acc[2] += item[2] / corners.length;
      acc[3] += item[3] / corners.length;
      return acc;
    }, [0, 0, 0, 0]);
    let minX = width;
    let minYBottom = height;
    let maxX = -1;
    let maxYBottom = -1;
    let nonTransparentPixels = 0;
    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        const offset = (y * width + x) * 4;
        const alpha = pixels[offset + 3];
        if (alpha <= 10) {
          continue;
        }
        const dr = pixels[offset] - background[0];
        const dg = pixels[offset + 1] - background[1];
        const db = pixels[offset + 2] - background[2];
        const da = alpha - background[3];
        if (Math.sqrt(dr * dr + dg * dg + db * db + da * da) <= 1) {
          continue;
        }
        nonTransparentPixels += 1;
        minX = Math.min(minX, x);
        maxX = Math.max(maxX, x);
        minYBottom = Math.min(minYBottom, y);
        maxYBottom = Math.max(maxYBottom, y);
      }
    }
    if (maxX < minX || maxYBottom < minYBottom) {
      return { available: true, width, height, nonTransparentPixels: 0 };
    }
    const top = height - maxYBottom - 1;
    const bottom = height - minYBottom;
    return {
      available: true,
      x: minX,
      y: top,
      width: maxX - minX + 1,
      height: bottom - top,
      centerX: minX + (maxX - minX + 1) / 2,
      bottom,
      canvasWidth: width,
      canvasHeight: height,
      nonTransparentPixels,
    };
  }

  function sampleCanvasPixels(targetCanvas) {
    const gl = targetCanvas.getContext("webgl2") || targetCanvas.getContext("webgl");
    if (!gl) {
      return { available: false, nonTransparentSamples: 0, samples: 0 };
    }
    const width = gl.drawingBufferWidth;
    const height = gl.drawingBufferHeight;
    const pixels = new Uint8Array(width * height * 4);
    gl.readPixels(0, 0, width, height, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
    const step = Math.max(1, Math.floor((width * height) / 120000));
    let samples = 0;
    let nonTransparentSamples = 0;
    for (let pixel = 0; pixel < width * height; pixel += step) {
      samples += 1;
      if (pixels[pixel * 4 + 3] > 10) {
        nonTransparentSamples += 1;
      }
    }
    return { available: true, width, height, samples, nonTransparentSamples };
  }

  function fitModelByPixiTransform(app, model) {
    const screen = app.screen || (app.renderer && app.renderer.screen) || {};
    const logicalWidth = screen.width || app.renderer.width || canvas.clientWidth || canvas.width;
    const logicalHeight = screen.height || app.renderer.height || canvas.clientHeight || canvas.height;
    if (model.anchor && typeof model.anchor.set === "function") {
      model.anchor.set(0.5, 0.5);
    }
    model.scale.set(1);
    model.position.set(logicalWidth / 2, logicalHeight / 2);
    drawModelFrame(app);
    const bounds = model.getBounds();
    const naturalWidth = Math.max(bounds.width, 1);
    const naturalHeight = Math.max(bounds.height, 1);
    const scale = Math.min(
      (logicalWidth * 0.78) / naturalWidth,
      (logicalHeight * 0.88) / naturalHeight
    );
    model.scale.set(scale);
    model.position.set(logicalWidth / 2, logicalHeight / 2);
    drawModelFrame(app);
    const scaledBounds = model.getBounds();
    model.position.x += logicalWidth / 2 - (scaledBounds.x + scaledBounds.width / 2);
    model.position.y += logicalHeight - 18 - (scaledBounds.y + scaledBounds.height);
  }

  async function loadLive2DModel(config, options) {
    const live2d = window.PIXI && window.PIXI.live2d;
    const Live2DModel = live2d && live2d.Live2DModel;
    const Live2DFactory = live2d && live2d.Live2DFactory;
    if (!Live2DModel || !Live2DFactory || typeof Live2DFactory.setupLive2DModel !== "function") {
      throw new Error("Live2D factory setup path is unavailable");
    }
    const model = new Live2DModel(options);
    const poseGuard = {
      modelSettingsDeclaredPose: false,
      disabledDefaultPose: false,
      finalPoseSetting: "",
    };
    let declaredPose = false;
    model.once("settingsJSONLoaded", (json) => {
      const fileReferences = json && json.FileReferences;
      declaredPose = Boolean(
        fileReferences &&
        typeof fileReferences.Pose === "string" &&
        fileReferences.Pose.trim()
      );
      poseGuard.modelSettingsDeclaredPose = declaredPose;
    });
    model.once("settingsLoaded", (settings) => {
      if (!declaredPose && settings && settings.pose === "Pose") {
        settings.pose = undefined;
        poseGuard.disabledDefaultPose = true;
      }
      poseGuard.finalPoseSetting = settings && settings.pose ? String(settings.pose) : "";
    });
    await Promise.race([
      Live2DFactory.setupLive2DModel(model, config.modelUrl, options),
      new Promise((_, reject) => setTimeout(() => reject(new Error("Live2DModel.from timed out after 70000ms")), 70000)),
    ]);
    return { model, poseGuard };
  }

  async function fitModelToPixels(app, targetCanvas, model) {
    targetCanvas.style.transformOrigin = "";
    targetCanvas.style.transform = "";
    fitModelByPixiTransform(app, model);
    const screen = app.screen || (app.renderer && app.renderer.screen) || {};
    const logicalWidth = screen.width || app.renderer.width || targetCanvas.clientWidth || targetCanvas.width;
    const pixelRatio = Math.max(1, targetCanvas.width / Math.max(1, logicalWidth));
    const attempts = [];
    let latest = null;
    for (let pass = 0; pass < 3; pass += 1) {
      drawModelFrame(app);
      latest = readCanvasPixelBounds(targetCanvas);
      attempts.push({
        phase: pass === 0 ? "initial" : `pixi_visual_fit_${pass}`,
        bounds: latest,
        modelScale: Number(model.scale.x.toFixed(4)),
        modelX: Number(model.position.x.toFixed(2)),
        modelY: Number(model.position.y.toFixed(2)),
      });
      if (!latest.available || !latest.nonTransparentPixels) {
        break;
      }
      const targetHeight = latest.canvasHeight * 0.85;
      const desiredCenterX = latest.canvasWidth * 0.5;
      const desiredBottom = latest.canvasHeight - 16 * pixelRatio;
      const heightRatio = latest.height / latest.canvasHeight;
      const scaleFactor = Math.max(0.82, Math.min(1.18, targetHeight / Math.max(1, latest.height)));
      if (heightRatio < 0.82 || heightRatio > 0.88) {
        model.scale.set(model.scale.x * scaleFactor);
      }
      model.position.x += (desiredCenterX - latest.centerX) / pixelRatio;
      model.position.y += (desiredBottom - latest.bottom) / pixelRatio;
    }
    drawModelFrame(app);
    latest = readCanvasPixelBounds(targetCanvas);
    const heightRatio = latest && latest.canvasHeight ? latest.height / latest.canvasHeight : 0;
    const bottomOverflow = latest && latest.bottom ? latest.bottom - latest.canvasHeight : 0;
    const visualFitPass = Boolean(
      latest &&
      latest.available &&
      latest.nonTransparentPixels > 0 &&
      heightRatio >= 0.78 &&
      heightRatio <= 0.9 &&
      latest.y >= 0 &&
      bottomOverflow <= 3
    );
    return {
      visualFitPass,
      visualPixelBounds: latest || { available: false },
      visualFitAttempts: attempts,
      visualFitScale: Number(model.scale.x.toFixed(4)),
      visualCssScale: 1,
      visualCssTranslate: { x: 0, y: 0 },
      visualHeightRatio: Number(heightRatio.toFixed(4)),
    };
  }

  async function waitForCanvasPixels(app, targetCanvas, timeoutMs) {
    const deadline = Date.now() + timeoutMs;
    drawModelFrame(app);
    let latest = sampleCanvasPixels(targetCanvas);
    while (Date.now() < deadline && latest.nonTransparentSamples === 0) {
      await Promise.race([
        new Promise((resolve) => requestAnimationFrame(resolve)),
        new Promise((resolve) => setTimeout(resolve, 500)),
      ]);
      drawModelFrame(app);
      latest = sampleCanvasPixels(targetCanvas);
    }
    return latest;
  }

  async function waitForRenderFrames(app, frameCount) {
    for (let index = 0; index < frameCount; index += 1) {
      await new Promise((resolve) => requestAnimationFrame(resolve));
      drawModelFrame(app);
    }
  }

  function modelDebug(model) {
    const bounds = model.getBounds();
    const internalModel = model.internalModel || {};
    return {
      x: Math.round(model.x),
      y: Math.round(model.y),
      scaleX: Number(model.scale.x.toFixed(4)),
      scaleY: Number(model.scale.y.toFixed(4)),
      width: Math.round(model.width),
      height: Math.round(model.height),
      renderable: Boolean(model.renderable),
      stageX: Math.round(bounds.x),
      stageY: Math.round(bounds.y),
      stageWidth: Math.round(bounds.width),
      stageHeight: Math.round(bounds.height),
      visible: Boolean(model.visible),
      alpha: Number(model.alpha),
      autoUpdate: Boolean(model.autoUpdate),
      canRender: typeof model.canRender === "function" ? Boolean(model.canRender()) : null,
      hasValidRenderer: typeof model.hasValidRenderer === "function" ? Boolean(model.hasValidRenderer()) : null,
      internalReady: typeof model.isReady === "function" ? Boolean(model.isReady()) : null,
      internalTextureCount: Array.isArray(internalModel.textures) ? internalModel.textures.length : null,
      internalTextureLoadedCount: Array.isArray(internalModel.textures)
        ? internalModel.textures.filter(Boolean).length
        : null,
      textureCount: Array.isArray(model.textures) ? model.textures.length : null,
      textureSizes: Array.isArray(model.textures)
        ? model.textures.map((texture) => {
          const source = texture && texture.source;
          return {
            width: source && Number(source.width) || null,
            height: source && Number(source.height) || null,
            valid: Boolean(texture && texture.valid),
          };
        })
        : [],
      appCanvasMatchesDomCanvas: Boolean(window.__egoAppCanvasMatchesDomCanvas),
    };
  }

  function rendererDebug(app) {
    const renderer = app && app.renderer;
    const gl = renderer && renderer.gl;
    const debug = {
      rendererType: renderer && renderer.constructor ? renderer.constructor.name : "",
      hasGl: Boolean(gl),
      isWebGL2: typeof WebGL2RenderingContext !== "undefined" && gl instanceof WebGL2RenderingContext,
      width: renderer && Number(renderer.width) || null,
      height: renderer && Number(renderer.height) || null,
      resolution: renderer && Number(renderer.resolution) || null,
      maxTextureSize: null,
      maxTextureImageUnits: null,
      vendor: "",
      renderer: "",
    };
    if (gl) {
      debug.maxTextureSize = gl.getParameter(gl.MAX_TEXTURE_SIZE);
      debug.maxTextureImageUnits = gl.getParameter(gl.MAX_TEXTURE_IMAGE_UNITS);
      const debugInfo = gl.getExtension("WEBGL_debug_renderer_info");
      if (debugInfo) {
        debug.vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) || "";
        debug.renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) || "";
      }
    }
    return debug;
  }

  function drawableDebug(model) {
    const internalModel = model.internalModel || {};
    const coreModel = internalModel.coreModel || {};
    const ids = typeof internalModel.getDrawableIDs === "function"
      ? internalModel.getDrawableIDs()
      : [];
    const drawables = [];
    for (let index = 0; index < ids.length; index += 1) {
      let bounds = null;
      try {
        if (typeof internalModel.getDrawableBounds === "function") {
          bounds = internalModel.getDrawableBounds(index);
        }
      } catch (_error) {
        bounds = null;
      }
      drawables.push({
        index,
        id: String(ids[index]),
        bounds: bounds ? {
          x: Number(bounds.x),
          y: Number(bounds.y),
          width: Number(bounds.width),
          height: Number(bounds.height),
        } : null,
        opacity: typeof coreModel.getDrawableOpacity === "function"
          ? Number(coreModel.getDrawableOpacity(index))
          : null,
        textureIndex: typeof coreModel.getDrawableTextureIndex === "function"
          ? Number(coreModel.getDrawableTextureIndex(index))
          : null,
        parentPartIndex: typeof coreModel.getDrawableParentPartIndex === "function"
          ? Number(coreModel.getDrawableParentPartIndex(index))
          : null,
      });
    }
    return drawables;
  }

  function partDebug(model) {
    const coreModel = model && model.internalModel && model.internalModel.coreModel;
    if (!coreModel || typeof coreModel.getPartCount !== "function" || typeof coreModel.getPartId !== "function") {
      return [];
    }
    const parts = [];
    for (let index = 0; index < coreModel.getPartCount(); index += 1) {
      parts.push({
        index,
        id: partIdToString(coreModel.getPartId(index)),
        opacity: typeof coreModel.getPartOpacityByIndex === "function"
          ? Number(coreModel.getPartOpacityByIndex(index))
          : null,
      });
    }
    return parts;
  }

  function applyDiagnosticDrawableHide(model, config) {
    const idsToHide = Array.isArray(config && config.hideDrawableIds) ? config.hideDrawableIds : [];
    if (idsToHide.length === 0) {
      return [];
    }
    const internalModel = model.internalModel || {};
    const coreModel = internalModel.coreModel || {};
    const ids = typeof internalModel.getDrawableIDs === "function" ? internalModel.getDrawableIDs() : [];
    const hidden = [];
    for (const id of idsToHide) {
      const index = ids.indexOf(id);
      const opacities = coreModel._model && coreModel._model.drawables && coreModel._model.drawables.opacities;
      if (index >= 0 && opacities && index < opacities.length) {
        opacities[index] = 0;
        hidden.push(id);
      }
    }
    return hidden;
  }

  try {
    if (!window.PIXI || !window.PIXI.live2d || !window.PIXI.live2d.Live2DModel) {
      throw new Error("PIXI Live2D runtime is unavailable: " + JSON.stringify({
        hasPIXI: Boolean(window.PIXI),
        pixiKeys: window.PIXI ? Object.keys(window.PIXI).slice(0, 18) : [],
        hasLive2d: Boolean(window.PIXI && window.PIXI.live2d),
        live2dKeys: window.PIXI && window.PIXI.live2d ? Object.keys(window.PIXI.live2d).slice(0, 18) : [],
      }));
    }
    const config = await window.egoDesktop.getConfig();
    const app = await createPixiApplication(canvas, stage || window);
    window.app = app;
    window.__egoAppCanvasMatchesDomCanvas = (app.canvas || app.view) === canvas;
    const loaded = await loadLive2DModel(config, {
      ticker: app.ticker,
      autoHitTest: false,
      autoFocus: false,
    });
    const model = loaded.model;
    const poseGuard = loaded.poseGuard;
    app.stage.addChild(model);
    applyWatermarkOff(model, config);
    applyIdleMouth(model);
    let initialExpressionApplied = false;
    if (config.initialExpressionName) {
      initialExpressionApplied = await applyNamedExpression(model, config.initialExpressionName);
      applyWatermarkOff(model, config);
      applyIdleMouth(model);
    }
    let diagnosticHiddenDrawableIds = applyDiagnosticDrawableHide(model, config);
    if (typeof app.start === "function") {
      app.start();
    }
    let visualFit = await fitModelToPixels(app, canvas, model);
    window.addEventListener("resize", () => {
      fitModelToPixels(app, canvas, model).then((result) => {
        visualFit = result;
      }).catch(() => {});
    });
    setupPspcDebugOverlayToggle();
    setupChat(model, config);
    if (!setupPspcPerceptionDemo(model, config)) {
      setupPspcVisualShim(model, config);
    }

    const expression = config.signalFrame &&
      config.signalFrame.presence_state &&
      config.signalFrame.presence_state.expression;
    const intensity = expression === "focused" ? 1 : 0.6;
    let deterministicFrame = 0;
    app.ticker.add(() => {
      const seconds = config && config.pspcRecordingMode ? deterministicFrame / 60 : performance.now() / 1000;
      deterministicFrame += 1;
      setParameter(model, "Param85", Number.isFinite(Number(config.watermarkParamValue)) ? Number(config.watermarkParamValue) : 1);
      setParameter(model, "ParamAngleX", Math.sin(seconds * 0.7) * 5 * intensity);
      setParameter(model, "ParamAngleY", Math.sin(seconds * 0.47) * 2 * intensity);
      setParameter(model, "ParamBodyAngleX", Math.sin(seconds * 0.42) * 3 * intensity);
      applyMouthState(model);
      if (Array.isArray(config.hideDrawableIds) && config.hideDrawableIds.length > 0) {
        diagnosticHiddenDrawableIds = applyDiagnosticDrawableHide(model, config);
      }
    });

    const canvasPixelSample = await waitForCanvasPixels(app, canvas, 30000);
    await waitForRenderFrames(app, 4);
    setStatus("Ready", "ready");
    await waitForRenderFrames(app, 2);
    let ttsSmoke = null;
    if (config.ttsSmokeText) {
      const ttsSmokeTurnId = speechTurns.startTurn();
      ttsSmoke = await speakTurn({
        schema_version: "ego_desktop.chat_turn.v1",
        status: "ok",
        bot_text: config.ttsSmokeText,
        visible_bot_text: config.ttsSmokeText,
        displayed_text: config.ttsSmokeText,
        side_effects_executed: false,
        memory_write: false,
        tool_use: false,
        message_send: false,
      }, config, { playAudio: false, speechTurnId: ttsSmokeTurnId });
    }
    let screenshotDataUrl = "";
    try {
      screenshotDataUrl = canvas.toDataURL("image/png");
    } catch (_error) {
      screenshotDataUrl = "";
    }
    reportReady({
      modelLoaded: true,
      modelUrl: config.modelUrl,
      primitiveClass: config.signalFrame && config.signalFrame.primitive_class,
      expressionNames: config.expressionCatalog && Array.isArray(config.expressionCatalog.entries)
        ? config.expressionCatalog.entries.map((entry) => entry.name)
        : [],
      renderMode: RENDER_MODE,
      modelCreationMode: "Live2DFactory.setupLive2DModel",
      settingsPoseGuard: poseGuard,
      manualRendererBinding: false,
      manualDrawableMutation: diagnosticHiddenDrawableIds.length > 0,
      cssCanvasTransform: Boolean(canvas.style.transform),
      highDpiCanvas: false,
      highDpiDisabledReason: "pixi8_live2d_viewport_mismatch",
      watermarkCover: Boolean(document.getElementById("watermark-cover")),
      tickerSource: "app.ticker",
      watermarkDefaultOff: true,
      chatUiReady: Boolean(chatForm && userInput && sendButton && chatOutput),
      pspcVisualShimReady: Boolean(config.pspcVisualShim && Array.isArray(config.pspcVisualShim.scenarios)),
      pspcVisualScenarioCount: config.pspcVisualShim && Array.isArray(config.pspcVisualShim.scenarios)
        ? config.pspcVisualShim.scenarios.length
        : 0,
      pspcPerceptionDemoReady: Boolean(config.pspcPerceptionDemo && Array.isArray(config.pspcPerceptionDemo.scenarios)),
      pspcPerceptionScenarioCount: config.pspcPerceptionDemo && Array.isArray(config.pspcPerceptionDemo.scenarios)
        ? config.pspcPerceptionDemo.scenarios.length
        : 0,
      pspcSameTriggerText: config.pspcPerceptionDemo ? String(config.pspcPerceptionDemo.trigger_text || "") : "",
      pspcRecordingMode: Boolean(config.pspcRecordingMode),
      pspcReplyPreviewMode: Boolean(config.pspcReplyPreviewMode),
      pspcReplyPreviewChatEnabled: Boolean(config.pspcReplyPreviewMode && chatForm && !chatForm.hidden),
      pspcPerceptionChatDisabled: Boolean(config.pspcPerceptionDemo && chatForm && chatForm.hidden),
      initialExpressionName: String(config.initialExpressionName || ""),
      initialExpressionApplied,
      hiddenDrawableIds: diagnosticHiddenDrawableIds,
      parameterSamples: {
        Param85: getParameter(model, "Param85"),
        Param107: getParameter(model, "Param107"),
        Param111: getParameter(model, "Param111"),
        Param113: getParameter(model, "Param113"),
        ParamMouthForm: getParameter(model, "ParamMouthForm"),
        ParamMouthOpenY: getParameter(model, "ParamMouthOpenY"),
        ParamJawOpen: getParameter(model, "ParamJawOpen"),
      },
      partOpacitySamples: {
        Part5: getPartOpacity(model, "Part5"),
        Part8: getPartOpacity(model, "Part8"),
      },
      modelDebug: modelDebug(model),
      rendererDebug: rendererDebug(app),
      visualFitPass: visualFit.visualFitPass,
      visualPixelBounds: visualFit.visualPixelBounds,
      visualFitAttempts: visualFit.visualFitAttempts,
      visualFitScale: visualFit.visualFitScale,
      visualCssScale: visualFit.visualCssScale,
      visualCssTranslate: visualFit.visualCssTranslate,
      visualHeightRatio: visualFit.visualHeightRatio,
      drawableDebug: drawableDebug(model),
      partDebug: partDebug(model),
      canvasPixelSample,
      ttsSmoke,
      screenshotDataUrl,
      sideEffectsExecuted: false,
    });
  } catch (error) {
    setStatus(error.message, "error");
    reportReady({
      modelLoaded: false,
      error: error.message,
      stack: error && error.stack ? String(error.stack).slice(0, 1200) : "",
      renderMode: RENDER_MODE,
      modelCreationMode: "Live2DFactory.setupLive2DModel",
      settingsPoseGuard: {},
      manualRendererBinding: false,
      manualDrawableMutation: false,
      cssCanvasTransform: Boolean(canvas.style.transform),
      highDpiCanvas: false,
      highDpiDisabledReason: "pixi8_live2d_viewport_mismatch",
      watermarkCover: false,
      tickerSource: "app.ticker",
      vendorStatus: {
        hasPIXI: Boolean(window.PIXI),
        hasLive2d: Boolean(window.PIXI && window.PIXI.live2d),
        live2dKeys: window.PIXI && window.PIXI.live2d ? Object.keys(window.PIXI.live2d).slice(0, 24) : [],
      },
      sideEffectsExecuted: false,
    });
  }
})();
