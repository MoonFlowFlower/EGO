const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawn } = require("node:child_process");
const { app, BrowserWindow, ipcMain, nativeImage } = require("electron");
const { parseArgs } = require("./args");
const { buildDesktopChatTurn } = require("./chatTurn");
const { resolveModelInput } = require("./modelResolver");
const { listExpressionFiles } = require("./modelSettings");
const { buildViewerSignalFrame } = require("./signalFrame");
const { buildTtsRequest } = require("./tts");
const { TtsWorkerClient } = require("./ttsWorkerClient");
const { createViewerServer, listen } = require("./server");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "..");
const launchArgs = parseArgs(process.argv.slice(1));

if (launchArgs.smoke) {
  const smokeOutDir = path.resolve(String(launchArgs.out || path.join(os.tmpdir(), "ego_live2d_desktop_smoke")));
  app.setPath("userData", path.join(smokeOutDir, "electron-user-data"));
}

function readJsonFile(filePath) {
  return JSON.parse(fs.readFileSync(filePath, "utf8"));
}

function loadSignalFrame(args) {
  let contract = {};
  if (args["signal-file"]) {
    contract = readJsonFile(path.resolve(String(args["signal-file"])));
  } else if (args["signal-json"]) {
    contract = JSON.parse(String(args["signal-json"]));
  }
  return buildViewerSignalFrame(contract);
}

function loadExpressionCatalog(modelDir) {
  const entries = listExpressionFiles(modelDir).map((entry) => {
    const filePath = path.join(modelDir, entry.File);
    let payload = {};
    try {
      payload = readJsonFile(filePath);
    } catch (_error) {
      payload = {};
    }
    return {
      name: entry.Name,
      file: entry.File,
      parameters: Array.isArray(payload.Parameters) ? payload.Parameters : [],
    };
  });
  return {
    entries,
    byName: Object.fromEntries(entries.map((entry) => [entry.name, entry])),
  };
}

function pythonExecutable() {
  return process.platform === "win32" ? "python.exe" : "python3";
}

function defaultRvcRoot() {
  return process.env.EGO_DESKTOP_RVC_ROOT || "D:\\Project\\AISinging\\ruanjian666";
}

function ttsPythonExecutable(rvcRoot, args) {
  if (args["tts-python"]) {
    return String(args["tts-python"]);
  }
  const executableName = process.platform === "win32" ? "python.exe" : "python";
  const bundledPython = path.join(rvcRoot, "runtime", executableName);
  return fs.existsSync(bundledPython) ? bundledPython : pythonExecutable();
}

function parseJsonLine(text) {
  const trimmed = String(text || "").trim();
  if (!trimmed) {
    throw new Error("empty backend output");
  }
  const lines = trimmed.split(/\r?\n/).filter(Boolean);
  return JSON.parse(lines[lines.length - 1]);
}

function backendEnv() {
  return {
    ...process.env,
    PYTHONIOENCODING: process.env.PYTHONIOENCODING || "utf-8",
    PYTHONUTF8: process.env.PYTHONUTF8 || "1",
  };
}

function runEgoOperatorDesktopTurn(userText, timeoutMs) {
  return new Promise((resolve) => {
    const child = spawn(
      pythonExecutable(),
      [path.join(repoRoot, "scripts", "ego_operator_desktop_turn.py")],
      {
        cwd: repoRoot,
        env: backendEnv(),
        stdio: ["pipe", "pipe", "pipe"],
        windowsHide: true,
      }
    );
    let stdout = "";
    let stderr = "";
    let settled = false;
    const timeout = setTimeout(() => {
      if (settled) {
        return;
      }
      settled = true;
      child.kill();
      resolve({
        status: "llm_expression_unavailable",
        reason: "desktop_turn_timeout",
        reply_text: "llm_expression_unavailable: desktop_turn_timeout",
      });
    }, Number(timeoutMs) || 180000);

    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString("utf8");
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString("utf8");
    });
    child.on("error", (error) => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timeout);
      resolve({
        status: "llm_expression_unavailable",
        reason: "desktop_turn_spawn_error",
        error: error.message,
        reply_text: `llm_expression_unavailable: ${error.message}`,
      });
    });
    child.on("close", () => {
      if (settled) {
        return;
      }
      settled = true;
      clearTimeout(timeout);
      try {
        const payload = parseJsonLine(stdout);
        resolve(payload);
      } catch (error) {
        resolve({
          status: "llm_expression_unavailable",
          reason: "desktop_turn_invalid_json",
          error: error.message,
          stderr: stderr.slice(0, 1200),
          reply_text: `llm_expression_unavailable: ${error.message}`,
        });
      }
    });
    child.stdin.end(JSON.stringify({ user_text: userText }));
  });
}

function writeJson(filePath, payload) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(payload, null, 2), "utf8");
}

function summarizeRendererPayload(payload) {
  if (!payload || typeof payload !== "object") {
    return payload || {};
  }
  const summarized = { ...payload };
  if (summarized.screenshotDataUrl) {
    summarized.screenshotDataUrl = "[omitted; screenshot_path contains PNG artifact]";
  }
  return summarized;
}

function countNonBlankPixels(bitmap, width, height) {
  if (!bitmap || !width || !height) {
    return 0;
  }
  let nonBlank = 0;
  const sampleStep = Math.max(1, Math.floor((width * height) / 80000));
  for (let pixel = 0; pixel < width * height; pixel += sampleStep) {
    const offset = pixel * 4;
    const blue = bitmap[offset];
    const green = bitmap[offset + 1];
    const red = bitmap[offset + 2];
    const alpha = bitmap[offset + 3];
    if (alpha > 0 && (red < 245 || green < 245 || blue < 245)) {
      nonBlank += 1;
    }
  }
  return nonBlank;
}

function visiblePixelBounds(image) {
  const size = image.getSize();
  const bitmap = image.toBitmap();
  let minX = size.width;
  let minY = size.height;
  let maxX = -1;
  let maxY = -1;
  for (let y = 0; y < size.height; y += 1) {
    for (let x = 0; x < size.width; x += 1) {
      const offset = (y * size.width + x) * 4;
      const blue = bitmap[offset];
      const green = bitmap[offset + 1];
      const red = bitmap[offset + 2];
      const alpha = bitmap[offset + 3];
      if (alpha > 0 && (red < 245 || green < 245 || blue < 245)) {
        minX = Math.min(minX, x);
        minY = Math.min(minY, y);
        maxX = Math.max(maxX, x);
        maxY = Math.max(maxY, y);
      }
    }
  }
  if (maxX < minX || maxY < minY) {
    return null;
  }
  return {
    x: minX,
    y: minY,
    width: maxX - minX + 1,
    height: maxY - minY + 1,
  };
}

function writeFaceCrop(image, outDir) {
  const bounds = visiblePixelBounds(image);
  if (!bounds) {
    return "";
  }
  const crop = {
    x: Math.max(0, Math.round(bounds.x + bounds.width * 0.24)),
    y: Math.max(0, Math.round(bounds.y + bounds.height * 0.02)),
    width: Math.max(1, Math.round(bounds.width * 0.52)),
    height: Math.max(1, Math.round(bounds.height * 0.28)),
  };
  const size = image.getSize();
  crop.width = Math.min(crop.width, size.width - crop.x);
  crop.height = Math.min(crop.height, size.height - crop.y);
  const faceCropPath = path.join(outDir, "live2d_desktop_face_crop.png");
  fs.writeFileSync(faceCropPath, image.crop(crop).toPNG());
  return faceCropPath;
}

async function captureSmoke(window, outDir, rendererPayload, signalFrame) {
  fs.mkdirSync(outDir, { recursive: true });
  const reportPath = path.join(outDir, "live2d_desktop_smoke_report.json");
  if (!rendererPayload || rendererPayload.modelLoaded !== true) {
    const report = {
      status: "live2d_desktop_smoke_fail",
      report_path: reportPath,
      model_loaded: false,
      renderer_payload: summarizeRendererPayload(rendererPayload),
      console_messages: window.__egoConsoleMessages || [],
      side_effects_executed: false,
      memory_write: false,
      tool_use: false,
      message_send: false,
      file_write: false,
      network_call: false,
      signal_frame: signalFrame,
      claim_ceiling: "local Live2D rendering smoke only; not stable embodiment, live autonomy, proactive messaging, durable memory efficacy, or consciousness proof",
    };
    writeJson(reportPath, report);
    return report;
  }
  await new Promise((resolve) => setTimeout(resolve, 500));
  let image;
  let canvasImage = null;
  let canvasScreenshotPath = "";
  let screenshot_source = "electron_capture_page";
  if (rendererPayload && rendererPayload.screenshotDataUrl) {
    canvasImage = nativeImage.createFromDataURL(rendererPayload.screenshotDataUrl);
    if (!canvasImage.isEmpty()) {
      canvasScreenshotPath = path.join(outDir, "live2d_desktop_canvas.png");
      fs.writeFileSync(canvasScreenshotPath, canvasImage.toPNG());
    }
  }
  image = await window.webContents.capturePage();
  if (image.isEmpty() && canvasImage && !canvasImage.isEmpty()) {
    image = canvasImage;
    screenshot_source = "renderer_canvas_data_url_fallback";
  }
  const screenshotPath = path.join(outDir, "live2d_desktop_smoke.png");
  fs.writeFileSync(screenshotPath, image.toPNG());
  const faceCropPath = writeFaceCrop(canvasImage && !canvasImage.isEmpty() ? canvasImage : image, outDir);
  let windowScreenshotPath = "";
  try {
    const windowImage = await window.webContents.capturePage();
    windowScreenshotPath = path.join(outDir, "live2d_desktop_window.png");
    fs.writeFileSync(windowScreenshotPath, windowImage.toPNG());
  } catch (_error) {
    windowScreenshotPath = "";
  }
  const size = image.getSize();
  const nonBlankPixelCount = countNonBlankPixels(image.toBitmap(), size.width, size.height);
  const modelVisible =
    rendererPayload &&
    rendererPayload.modelDebug &&
    rendererPayload.canvasPixelSample &&
    rendererPayload.canvasPixelSample.nonTransparentSamples > 0 &&
    rendererPayload.visualFitPass !== false &&
    rendererPayload.renderMode === "official_live2d_model_from" &&
    rendererPayload.manualRendererBinding === false &&
    rendererPayload.manualDrawableMutation === false &&
    rendererPayload.cssCanvasTransform === false &&
    rendererPayload.modelDebug.stageWidth > 20 &&
    rendererPayload.modelDebug.stageHeight > 20 &&
    rendererPayload.modelDebug.x >= -100 &&
    rendererPayload.modelDebug.x <= size.width + 100 &&
    rendererPayload.modelDebug.y >= -100 &&
    rendererPayload.modelDebug.y <= size.height + 100;
  const report = {
    status: rendererPayload && rendererPayload.modelLoaded && nonBlankPixelCount > 0 && modelVisible
      ? "live2d_desktop_smoke_pass"
      : "live2d_desktop_smoke_fail",
    report_path: reportPath,
    model_loaded: Boolean(rendererPayload && rendererPayload.modelLoaded),
    renderer_payload: summarizeRendererPayload(rendererPayload),
    console_messages: window.__egoConsoleMessages || [],
    screenshot_path: screenshotPath,
    canvas_screenshot_path: canvasScreenshotPath,
    face_crop_path: faceCropPath,
    window_screenshot_path: windowScreenshotPath,
    screenshot_source,
    screenshot_size: size,
    non_blank_pixel_count: nonBlankPixelCount,
    model_visible_geometry: Boolean(modelVisible),
    render_mode: rendererPayload.renderMode || "",
    manual_renderer_binding: Boolean(rendererPayload.manualRendererBinding),
    manual_drawable_mutation: Boolean(rendererPayload.manualDrawableMutation),
    css_canvas_transform: Boolean(rendererPayload.cssCanvasTransform),
    high_dpi_canvas: Boolean(rendererPayload.highDpiCanvas),
    high_dpi_disabled_reason: rendererPayload.highDpiDisabledReason || "",
    watermark_cover: Boolean(rendererPayload.watermarkCover),
    ticker_source: rendererPayload.tickerSource || "",
    tts_smoke: rendererPayload.ttsSmoke || null,
    tts_status: rendererPayload.ttsSmoke ? String(rendererPayload.ttsSmoke.status || "") : "",
    tts_text_source: rendererPayload.ttsSmoke ? String(rendererPayload.ttsSmoke.text_source || "") : "",
    tts_text_matches_displayed: Boolean(rendererPayload.ttsSmoke && rendererPayload.ttsSmoke.visible_text_matches_tts_text),
    ui_audio_delivery_executed: Boolean(rendererPayload.ttsSmoke && rendererPayload.ttsSmoke.ui_audio_delivery_executed),
    base_tts_network_call: Boolean(rendererPayload.ttsSmoke && rendererPayload.ttsSmoke.base_tts_network_call),
    tts_temp_audio_file_write: Boolean(rendererPayload.ttsSmoke && rendererPayload.ttsSmoke.tts_temp_audio_file_write),
    prohibited_side_effects_executed: false,
    side_effects_executed: false,
    memory_write: false,
    tool_use: false,
    message_send: false,
    file_write: false,
    network_call: false,
    signal_frame: signalFrame,
    claim_ceiling: "local Live2D rendering smoke only; not stable embodiment, live autonomy, proactive messaging, durable memory efficacy, or consciousness proof",
  };
  writeJson(reportPath, report);
  return report;
}

async function run() {
  const args = launchArgs;
  const modelInfo = resolveModelInput(args["model-path"]);
  const ttsAudioRoot = path.join(app.getPath("userData"), "tts-audio");
  fs.mkdirSync(ttsAudioRoot, { recursive: true });
  const rvcRoot = path.resolve(String(args["tts-rvc-root"] || defaultRvcRoot()));
  const ttsWorkerClient = new TtsWorkerClient({
    workerCommand: ttsPythonExecutable(rvcRoot, args),
    workerArgs: [
      path.join(repoRoot, "scripts", "ego_desktop_tts_worker.py"),
      "--rvc-root", rvcRoot,
      "--model-name", String(args["tts-model-name"] || "Skadi_CN.pth"),
      "--base-voice", String(args["tts-base-voice"] || "zh-CN-XiaoxiaoNeural"),
      "--f0method", String(args["tts-f0method"] || "rmvpe"),
      "--f0up-key", String(args["tts-f0up-key"] || "0"),
      "--device", String(args["tts-device"] || "cuda:0"),
      "--is-half", String(args["tts-is-half"] || "true"),
      "--audio-root", ttsAudioRoot,
      ...(args["tts-ffmpeg-path"] ? ["--ffmpeg-path", String(args["tts-ffmpeg-path"])] : []),
      ...(args["tts-fake"] ? ["--fake"] : []),
      ...(args["tts-skip-base-self-check"] ? ["--skip-base-tts-self-check"] : []),
    ],
    workerCwd: repoRoot,
    workerEnv: backendEnv(),
    audioRoot: ttsAudioRoot,
    startupTimeoutMs: Number(args["tts-startup-timeout-ms"] || 180000),
    requestTimeoutMs: Number(args["tts-timeout-ms"] || 240000),
  });
  const signalFrame = loadSignalFrame(args);
  const expressionCatalog = loadExpressionCatalog(modelInfo.modelDir);
  const server = createViewerServer({
    appRoot,
    modelInfo,
    viewerDir: path.join(appRoot, "viewer"),
    ttsAudioRoot,
  });
  const address = await listen(server, args.port);
  const baseUrl = `http://${address.address}:${address.port}`;
  const window = new BrowserWindow({
    width: 900,
    height: 700,
    title: "EgoDesktop Live2D",
    backgroundColor: "#f7f7f4",
    show: true,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
  });
  window.__egoConsoleMessages = [];
  window.webContents.on("console-message", (_event, level, message, line, sourceId) => {
    window.__egoConsoleMessages.push({ level, message, line, sourceId });
  });
  window.webContents.on("did-fail-load", (_event, errorCode, errorDescription, validatedURL) => {
    window.__egoConsoleMessages.push({
      level: "load-fail",
      message: `${errorCode}: ${errorDescription}`,
      sourceId: validatedURL,
    });
  });

  const config = {
    modelUrl: `${baseUrl}${modelInfo.modelUrl}`,
    signalFrame,
    expressionCatalog,
    watermarkParamValue: Number.isFinite(Number(args["watermark-param"]))
      ? Number(args["watermark-param"])
      : 1,
    hideDrawableIds: args["hide-drawables"] === "none"
      ? []
      : String(args["hide-drawables"] || "")
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
    initialExpressionName: String(args["initial-expression"] || ""),
    mouthFixMode: String(args["mouth-fix"] || "full"),
    voiceEnabled: !(args["voice-disabled"] || args["tts-disabled"]),
    ttsMaxChars: Number(args["tts-max-chars"] || 600),
    ttsBaseVoice: String(args["tts-base-voice"] || "zh-CN-XiaoxiaoNeural"),
    ttsRvcModel: String(args["tts-model-name"] || "Skadi_CN.pth"),
    ttsF0Method: String(args["tts-f0method"] || "rmvpe"),
    ttsSmokeText: String(args["tts-smoke-text"] || ""),
  };
  ipcMain.handle("ego-desktop:get-config", () => config);
  ipcMain.handle("ego-desktop:chat-turn", async (_event, payload) => {
    const userText = String((payload && payload.userText) || "").trim();
    if (!userText) {
      return buildDesktopChatTurn({
        userText,
        botText: "llm_expression_unavailable: empty_user_text",
        status: "input_error",
        expressionName: "晕晕眼",
      });
    }
    const backend = await runEgoOperatorDesktopTurn(userText, args["chat-timeout-ms"]);
    const status = backend.status === "ok" ? "ok" : "llm_expression_unavailable";
    const botText = status === "ok"
      ? String(backend.reply_text || "")
      : String(backend.reply_text || `llm_expression_unavailable: ${backend.reason || "backend_unavailable"}`);
    return {
      ...buildDesktopChatTurn({ userText, botText, status }),
      backend_status: backend.status || status,
      backend_reason: backend.reason || "",
      pending_approvals: Number(backend.pending_approvals || 0),
      side_effects_executed: Boolean(backend.side_effects_executed),
      memory_write: Boolean(backend.memory_write),
      tool_use: Boolean(backend.tool_use),
      message_send: Boolean(backend.message_send),
      file_write: Boolean(backend.file_write),
      network_call: Boolean(backend.network_call),
    };
  });
  ipcMain.handle("ego-desktop:synthesize-speech", async (_event, payload) => {
    const request = buildTtsRequest({
      turn: payload && payload.turn ? payload.turn : {},
      voiceEnabled: Boolean(config.voiceEnabled && payload && payload.voiceEnabled !== false),
      requestId: payload && payload.requestId,
      maxChars: config.ttsMaxChars,
      baseVoice: config.ttsBaseVoice,
      rvcModel: config.ttsRvcModel,
      f0method: config.ttsF0Method,
    });
    if (!request.should_synthesize) {
      return request;
    }
    try {
      return await ttsWorkerClient.synthesize(request);
    } catch (error) {
      return {
        type: "result",
        status: "tts_worker_unavailable",
        reason: error.message,
        request_id: request.request_id,
        side_effects_executed: false,
        memory_write: false,
        tool_use: false,
        message_send: false,
        file_write: false,
        network_call: false,
        ui_audio_delivery_executed: false,
      };
    }
  });
  ipcMain.handle("ego-desktop:cancel-speech", async () => ttsWorkerClient.cancel());
  app.once("before-quit", () => {
    ttsWorkerClient.shutdown();
  });

  let smokeSettled = false;
  ipcMain.on("ego-desktop:renderer-ready", async (_event, payload) => {
    if (!args.smoke || smokeSettled) {
      return;
    }
    smokeSettled = true;
    try {
      const outDir = path.resolve(String(args.out || path.join(app.getPath("temp"), "ego_live2d_desktop_smoke")));
      const report = await captureSmoke(window, outDir, payload, signalFrame);
      app.exit(report.status === "live2d_desktop_smoke_pass" ? 0 : 1);
    } catch (error) {
      const outDir = path.resolve(String(args.out || path.join(app.getPath("temp"), "ego_live2d_desktop_smoke")));
      writeJson(path.join(outDir, "live2d_desktop_smoke_report.json"), {
        status: "live2d_desktop_smoke_error",
        error: error.message,
        side_effects_executed: false,
        memory_write: false,
        tool_use: false,
        message_send: false,
      });
      app.exit(1);
    }
  });

  if (args.smoke) {
    const smokeTimeoutMs = args["tts-smoke-text"] ? 240000 : 90000;
    setTimeout(() => {
      if (smokeSettled) {
        return;
      }
      smokeSettled = true;
      const outDir = path.resolve(String(args.out || path.join(app.getPath("temp"), "ego_live2d_desktop_smoke")));
      writeJson(path.join(outDir, "live2d_desktop_smoke_report.json"), {
        status: "live2d_desktop_smoke_timeout",
        console_messages: window.__egoConsoleMessages || [],
        side_effects_executed: false,
        memory_write: false,
        tool_use: false,
        message_send: false,
      });
      app.exit(1);
    }, smokeTimeoutMs).unref();
  }

  await window.loadURL(`${baseUrl}/viewer/index.html`);
}

app.whenReady().then(run).catch((error) => {
  console.error(error);
  app.exit(1);
});

app.on("window-all-closed", () => {
  app.quit();
});

app.on("before-quit", () => {
  try {
    ipcMain.removeHandler("ego-desktop:synthesize-speech");
    ipcMain.removeHandler("ego-desktop:cancel-speech");
  } catch (_error) {
    // Handler cleanup is best effort during shutdown.
  }
});
