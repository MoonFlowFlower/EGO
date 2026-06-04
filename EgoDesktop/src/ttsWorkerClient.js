const readline = require("node:readline");
const { spawn } = require("node:child_process");
const { buildTtsAudioUrl, resolveTtsAudioRequestPath } = require("./tts");

class TtsWorkerClient {
  constructor({
    workerCommand,
    workerArgs,
    workerEnv,
    workerCwd,
    audioRoot,
    startupTimeoutMs = 30000,
    requestTimeoutMs = 180000,
  } = {}) {
    this.workerCommand = workerCommand;
    this.workerArgs = Array.from(workerArgs || []);
    this.workerEnv = workerEnv || process.env;
    this.workerCwd = workerCwd || process.cwd();
    this.audioRoot = audioRoot;
    this.startupTimeoutMs = Number(startupTimeoutMs) || 30000;
    this.requestTimeoutMs = Number(requestTimeoutMs) || 180000;
    this.child = null;
    this.readyPromise = null;
    this.readyResolve = null;
    this.readyReject = null;
    this.pending = new Map();
    this.logs = [];
  }

  start() {
    if (this.child) {
      return this.readyPromise || Promise.resolve();
    }
    if (!this.workerCommand) {
      return Promise.reject(new Error("TTS worker command is not configured"));
    }
    this.child = spawn(this.workerCommand, this.workerArgs, {
      cwd: this.workerCwd,
      env: this.workerEnv,
      stdio: ["pipe", "pipe", "pipe"],
      windowsHide: true,
    });
    this.readyPromise = new Promise((resolve, reject) => {
      this.readyResolve = resolve;
      this.readyReject = reject;
    });
    const startupTimeout = setTimeout(() => {
      this._rejectReady(new Error("TTS worker startup timeout"));
      this.shutdown();
    }, this.startupTimeoutMs);
    this.readyPromise.finally(() => clearTimeout(startupTimeout)).catch(() => {});

    readline.createInterface({ input: this.child.stdout }).on("line", (line) => {
      this._handleLine(line);
    });
    this.child.stderr.on("data", (chunk) => {
      this._recordLog("stderr", chunk.toString("utf8"));
    });
    this.child.on("error", (error) => {
      this._rejectReady(error);
      this._rejectPending(error);
    });
    this.child.on("exit", (code, signal) => {
      const error = new Error(`TTS worker exited: code=${code} signal=${signal || ""}`);
      this.child = null;
      this._rejectReady(error);
      this._rejectPending(error);
    });
    return this.readyPromise;
  }

  async synthesize(request) {
    if (!request || request.should_synthesize !== true) {
      return request || { status: "tts_request_unavailable", should_synthesize: false };
    }
    await this.start();
    const requestId = String(request.request_id || `tts_${Date.now()}`);
    const payload = {
      ...request,
      request_id: requestId,
      audio_root: this.audioRoot,
    };
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        this.pending.delete(requestId);
        reject(new Error("TTS worker request timeout"));
      }, this.requestTimeoutMs);
      this.pending.set(requestId, {
        request: payload,
        resolve: (value) => {
          clearTimeout(timeout);
          resolve(value);
        },
        reject: (error) => {
          clearTimeout(timeout);
          reject(error);
        },
      });
      this.child.stdin.write(JSON.stringify(payload) + "\n", "utf8", (error) => {
        if (error) {
          this.pending.delete(requestId);
          clearTimeout(timeout);
          reject(error);
        }
      });
    });
  }

  cancel() {
    this.shutdown();
    return {
      status: "tts_cancelled",
      side_effects_executed: false,
      memory_write: false,
      tool_use: false,
      message_send: false,
      ui_audio_delivery_executed: false,
    };
  }

  shutdown() {
    if (!this.child) {
      return;
    }
    try {
      this.child.kill();
    } catch (_error) {
      // Best effort cleanup only.
    }
    this.child = null;
  }

  _handleLine(line) {
    const text = String(line || "").trim();
    if (!text) {
      return;
    }
    let payload;
    try {
      payload = JSON.parse(text);
    } catch (_error) {
      this._recordLog("stdout", text);
      return;
    }
    if (payload.type === "ready") {
      if (payload.status === "ok") {
        this._resolveReady(payload);
      } else {
        this._rejectReady(new Error(payload.reason || payload.status || "TTS worker unavailable"));
      }
      return;
    }
    if (payload.type !== "result") {
      this._recordLog("json", JSON.stringify(payload));
      return;
    }
    const requestId = String(payload.request_id || "");
    const pending = this.pending.get(requestId);
    if (!pending) {
      return;
    }
    this.pending.delete(requestId);
    const request = pending.request || {};
    if (payload.status === "ok" && payload.audio_file) {
      try {
        const audioPath = resolveTtsAudioRequestPath(
          this.audioRoot,
          "/tts-audio/" + encodeURIComponent(require("node:path").basename(payload.audio_file))
        );
        pending.resolve({
          ...payload,
          audio_file: audioPath,
          audio_url: buildTtsAudioUrl(audioPath),
          text: request.text || "",
          text_source: request.text_source || "",
          visible_text_matches_tts_text: Boolean(request.visible_text_matches_tts_text),
        });
      } catch (error) {
        pending.reject(error);
      }
      return;
    }
    pending.resolve({
      side_effects_executed: false,
      memory_write: false,
      tool_use: false,
      message_send: false,
      ui_audio_delivery_executed: false,
      text: request.text || "",
      text_source: request.text_source || "",
      visible_text_matches_tts_text: Boolean(request.visible_text_matches_tts_text),
      ...payload,
    });
  }

  _recordLog(stream, text) {
    this.logs.push({ stream, text: String(text || "").slice(0, 1200) });
    if (this.logs.length > 80) {
      this.logs.shift();
    }
  }

  _resolveReady(payload) {
    if (this.readyResolve) {
      this.readyResolve(payload);
      this.readyResolve = null;
      this.readyReject = null;
    }
  }

  _rejectReady(error) {
    if (this.readyReject) {
      this.readyReject(error);
      this.readyResolve = null;
      this.readyReject = null;
    }
  }

  _rejectPending(error) {
    for (const pending of this.pending.values()) {
      pending.reject(error);
    }
    this.pending.clear();
  }
}

module.exports = { TtsWorkerClient };
