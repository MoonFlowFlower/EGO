const fs = require("node:fs");
const path = require("node:path");

function isModelFile(filePath) {
  return path.basename(filePath).toLowerCase().endsWith(".model3.json");
}

function assertExists(filePath, label) {
  if (!fs.existsSync(filePath)) {
    throw new Error(`${label} does not exist: ${filePath}`);
  }
}

function findModelFileInDirectory(modelDir) {
  const candidates = fs
    .readdirSync(modelDir)
    .filter((name) => name.toLowerCase().endsWith(".model3.json"))
    .sort((left, right) => left.localeCompare(right));
  if (candidates.length === 0) {
    throw new Error(`no .model3.json file found in directory: ${modelDir}`);
  }
  return path.join(modelDir, candidates[0]);
}

function resolveModelInput(inputPath) {
  if (!inputPath || typeof inputPath !== "string") {
    throw new Error("--model-path is required");
  }
  const absoluteInput = path.resolve(inputPath);
  assertExists(absoluteInput, "model path");
  const stat = fs.statSync(absoluteInput);
  const modelFile = stat.isDirectory()
    ? findModelFileInDirectory(absoluteInput)
    : absoluteInput;
  if (!isModelFile(modelFile)) {
    throw new Error(`model path must be a .model3.json file or a directory containing one: ${inputPath}`);
  }
  assertExists(modelFile, "model file");
  const modelDir = path.dirname(modelFile);
  return {
    modelDir,
    modelFile,
    modelFileName: path.basename(modelFile),
    modelUrl: `/model/${encodeURIComponent(path.basename(modelFile))}`,
  };
}

function stripQueryAndHash(requestUrl) {
  return String(requestUrl || "").split("?")[0].split("#")[0];
}

function resolveModelRequestPath(modelInfo, requestUrl) {
  const rawPath = stripQueryAndHash(requestUrl);
  if (!rawPath.startsWith("/model/")) {
    throw new Error(`model request path must start with /model/: ${requestUrl}`);
  }
  let relativeRequest = rawPath.slice("/model/".length);
  try {
    relativeRequest = decodeURIComponent(relativeRequest);
  } catch (error) {
    throw new Error(`model request path is not valid URL encoding: ${requestUrl}`);
  }
  if (!relativeRequest || relativeRequest.includes("\0")) {
    throw new Error("model request path is empty or invalid");
  }
  relativeRequest = relativeRequest.replace(/\\/g, "/");
  if (relativeRequest.startsWith("/") || relativeRequest.split("/").includes("..")) {
    throw new Error("model request path outside selected model directory");
  }
  const targetPath = path.resolve(modelInfo.modelDir, ...relativeRequest.split("/").filter(Boolean));
  const relativeToRoot = path.relative(modelInfo.modelDir, targetPath);
  if (
    relativeToRoot === "" ||
    relativeToRoot.startsWith("..") ||
    path.isAbsolute(relativeToRoot)
  ) {
    throw new Error("model request path outside selected model directory");
  }
  return targetPath;
}

module.exports = {
  isModelFile,
  resolveModelInput,
  resolveModelRequestPath,
};
