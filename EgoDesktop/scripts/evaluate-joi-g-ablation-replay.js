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

function hasFlag(name) {
  return process.argv.includes(`--${name}`);
}

function main() {
  const rowsPath = readArg("rows");
  const outDir = readArg("out");
  const runId = readArg("run-id", "joi_g_ablation_replay_leakage_eval_v0");
  const requireScoringPrecondition = hasFlag("require-007-scoring-precondition");
  const requiredCondition = readArg("required-condition", "");
  if (!rowsPath || !outDir) {
    throw new Error("usage: node scripts/evaluate-joi-g-ablation-replay.js --rows <trace_rows.jsonl> --out <dir> [--run-id <id>] [--require-007-scoring-precondition] [--required-condition <condition>]");
  }
  const report = writeEvaluationReport({
    rowsPath: path.resolve(rowsPath),
    outDir: path.resolve(outDir),
    runId,
    requireScoringPrecondition,
    requiredCondition,
  });
  process.stdout.write(JSON.stringify({
    status: report.status,
    rows_evaluated: report.rows_evaluated,
    leakage_positive_control_status: report.leakage_positive_control_status,
    d_field_replay_precondition_satisfied: report.d_field_replay_precondition_satisfied,
    scoring_run_authorized: report.scoring_run_authorized,
    blockers: report.blockers,
  }, null, 2));
  if (requireScoringPrecondition && report.d_field_replay_precondition_satisfied !== true) {
    process.exitCode = 3;
  }
}

main();
