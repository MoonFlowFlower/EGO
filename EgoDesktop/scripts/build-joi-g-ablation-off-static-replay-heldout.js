#!/usr/bin/env node
const path = require("node:path");

const {
  writeOffStaticReplayHeldoutRows,
} = require("../src/joiRealLoopGAblationOfflineReplay");

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
  const sourceRowsPath = readArg("source-rows");
  const calibrationReferencePath = readArg("calibration-reference");
  const outDir = readArg("out");
  const runId = readArg("run-id", "egodesktop_gablation_008_off_static_replay_heldout");
  if (!sourceRowsPath || !outDir) {
    throw new Error("usage: node scripts/build-joi-g-ablation-off-static-replay-heldout.js --source-rows <trace_rows.jsonl> --out <dir> [--run-id <id>]");
  }
  const report = writeOffStaticReplayHeldoutRows({
    sourceRowsPath: path.resolve(sourceRowsPath),
    calibrationReferencePath: calibrationReferencePath ? path.resolve(calibrationReferencePath) : "",
    outDir: path.resolve(outDir),
    runId,
  });
  process.stdout.write(JSON.stringify({
    status: report.status,
    trace_row_count: report.trace_row_count,
    trace_rows_path: report.trace_rows_path,
    row_hash: report.row_hash,
    calibration_reference_kind: report.calibration_reference_kind,
  }, null, 2));
}

main();
