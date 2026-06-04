const path = require("node:path");
const { spawn } = require("node:child_process");
const electronPath = require("electron");

const appRoot = path.resolve(__dirname, "..");

function normalizeNpmArgs(rawArgs) {
  const args = Array.from(rawArgs || []);
  if (args.includes("--model-path")) {
    return args;
  }
  const normalized = [];
  if (args[0]) {
    normalized.push("--model-path", args[0]);
  }
  if (args[1]) {
    normalized.push("--out", args[1]);
  }
  if (args.length > 2) {
    if (args[2] && !args[2].startsWith("--")) {
      normalized.push("--tts-smoke-text", args[2]);
      normalized.push(...args.slice(3));
    } else {
      normalized.push(...args.slice(2));
    }
  }
  return normalized;
}

function launchElectron(extraArgs, rawArgs) {
  const child = spawn(electronPath, [appRoot, ...extraArgs, ...normalizeNpmArgs(rawArgs)], {
    cwd: appRoot,
    stdio: "inherit",
    windowsHide: false,
  });

  child.on("exit", (code, signal) => {
    if (signal) {
      process.kill(process.pid, signal);
      return;
    }
    process.exit(code || 0);
  });
}

module.exports = { launchElectron, normalizeNpmArgs };
