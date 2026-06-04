const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");
const { resolveModelRequestPath } = require("./modelResolver");
const { normalizeModelSettingsJson } = require("./modelSettings");
const { resolveTtsAudioRequestPath } = require("./tts");

const MIME_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".moc3": "application/octet-stream",
  ".png": "image/png",
  ".mp3": "audio/mpeg",
  ".wav": "audio/wav",
};

const VENDOR_FILES = {
  "/vendor/pixi/pixi.min.js": [
    "node_modules/pixi.js/dist/pixi.min.js",
  ],
  "/vendor/pixi/unsafe-eval.min.js": [
    "node_modules/pixi.js/dist/packages/unsafe-eval.min.js",
    "node_modules/pixi.js/dist/packages/unsafe-eval.js",
  ],
  "/vendor/pixi-live2d-display/cubism5.min.js": [
    "node_modules/@naari3/pixi-live2d-display/dist/cubism5.min.js",
    "node_modules/@naari3/pixi-live2d-display/dist/cubism5.js",
  ],
  "/vendor/live2dcubismcore/live2dcubismcore.min.js": [
    "node_modules/@hazart-pkg/live2d-core/live2dcubismcore.min.js",
  ],
};

function sendFile(response, filePath) {
  if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
    response.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
    response.end("not found");
    return;
  }
  const type = MIME_TYPES[path.extname(filePath).toLowerCase()] || "application/octet-stream";
  response.writeHead(200, { "content-type": type, "cache-control": "no-store" });
  fs.createReadStream(filePath).pipe(response);
}

function sendModelFile(response, filePath) {
  if (path.basename(filePath).toLowerCase().endsWith(".model3.json")) {
    const normalized = normalizeModelSettingsJson(fs.readFileSync(filePath, "utf8"), {
      modelDir: path.dirname(filePath),
    });
    response.writeHead(200, {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "no-store",
    });
    response.end(JSON.stringify(normalized));
    return;
  }
  sendFile(response, filePath);
}

function resolveViewerPath(viewerDir, requestPath) {
  const relativeRequest = requestPath.replace(/^\/viewer\/?/, "") || "index.html";
  const targetPath = path.resolve(viewerDir, ...relativeRequest.split("/").filter(Boolean));
  const relativeToRoot = path.relative(viewerDir, targetPath);
  if (relativeToRoot.startsWith("..") || path.isAbsolute(relativeToRoot)) {
    throw new Error("viewer request path outside viewer directory");
  }
  return targetPath;
}

function resolveVendorPath(appRoot, requestPath) {
  const candidates = VENDOR_FILES[requestPath] || [];
  for (const candidate of candidates) {
    const targetPath = path.join(appRoot, candidate);
    if (fs.existsSync(targetPath)) {
      return targetPath;
    }
  }
  throw new Error(`vendor asset unavailable: ${requestPath}`);
}

function createViewerServer({ appRoot, modelInfo, viewerDir, ttsAudioRoot }) {
  const server = http.createServer((request, response) => {
    const requestPath = String(request.url || "/").split("?")[0].split("#")[0];
    try {
      if (requestPath === "/" || requestPath.startsWith("/viewer/")) {
        sendFile(response, resolveViewerPath(viewerDir, requestPath === "/" ? "/viewer/index.html" : requestPath));
        return;
      }
      if (requestPath.startsWith("/model/")) {
        sendModelFile(response, resolveModelRequestPath(modelInfo, request.url || requestPath));
        return;
      }
      if (requestPath.startsWith("/vendor/")) {
        sendFile(response, resolveVendorPath(appRoot, requestPath));
        return;
      }
      if (requestPath.startsWith("/tts-audio/")) {
        sendFile(response, resolveTtsAudioRequestPath(ttsAudioRoot, request.url || requestPath));
        return;
      }
      response.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
      response.end("not found");
    } catch (error) {
      response.writeHead(403, { "content-type": "text/plain; charset=utf-8" });
      response.end(error.message);
    }
  });
  return server;
}

function listen(server, port = 0) {
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(Number(port) || 0, "127.0.0.1", () => {
      server.off("error", reject);
      resolve(server.address());
    });
  });
}

module.exports = {
  createViewerServer,
  listen,
  resolveVendorPath,
};
