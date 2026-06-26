#!/usr/bin/env node
const path = require("node:path");

const { writeEvaluationReport } = require("../src/joiRealLoopGAblationReplayEvaluator");

function readArg(name, fallback = "") {
  const prefix = `--${name}=`;
  const inline = process.argv.find((arg) => arg.startsWith(prefix));
  if (inline) {
    return inline.slice(prefix.length);
  }
  const index = process.argv.indexOf(`--${name}`);
  if (index >= 0 && process.argv[index + 1]) {
    return process.argv[index + 1];
  }
  return fallback;
}

function main() {
  const rowsPath = readArg("rows");
  const outDir = readArg("out");
  const runId = readArg("run-id", "joi_g_ablation_replay_leakage_eval_v0");
  if (!rowsPath || !outDir) {
    throw new Error("usage: node scripts/evaluate-joi-g-ablation-replay.js --rows <trace_rows.jsonl> --out <dir> [--run-id <id>]");
  }
  const report = writeEvaluationReport({
    rowsPath: path.resolve(rowsPath),
    outDir: path.resolve(outDir),
    runId,
  });
  process.stdout.write(JSON.stringify({
    status: report.status,
    rows_evaluated: report.rows_evaluated,
    leakage_positive_control_status: report.leakage_positive_control_status,
    blockers: report.blockers,
  }, null, 2));
}

main();
