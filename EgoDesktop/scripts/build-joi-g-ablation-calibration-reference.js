#!/usr/bin/env node
const path = require("node:path");

const {
  writeCalibrationReference,
} = require("../src/joiRealLoopGAblationCalibrationReference");

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
  const calibrationRowsPath = readArg("calibration-rows");
  const heldoutRowsPath = readArg("heldout-rows");
  const predeclaredPromptPackPath = readArg("predeclared-calibration-prompt-pack");
  const outDir = readArg("out");
  const runId = readArg("run-id", "egodesktop_gablation_009_captured_calibration_reference");
  if (!calibrationRowsPath || !heldoutRowsPath || !predeclaredPromptPackPath || !outDir) {
    throw new Error(
      "usage: node scripts/build-joi-g-ablation-calibration-reference.js --calibration-rows <trace_rows.jsonl> --heldout-rows <trace_rows.jsonl> --predeclared-calibration-prompt-pack <prompt_pack.json> --out <dir> [--run-id <id>]",
    );
  }
  const report = writeCalibrationReference({
    calibrationRowsPath: path.resolve(calibrationRowsPath),
    heldoutRowsPath: path.resolve(heldoutRowsPath),
    predeclaredPromptPackPath: path.resolve(predeclaredPromptPackPath),
    outDir: path.resolve(outDir),
    runId,
  });
  process.stdout.write(JSON.stringify({
    status: report.status,
    calibration_reference_path: report.calibration_reference_path,
    split_partition_manifest_path: report.split_partition_manifest_path,
    calibration_reference_hash: report.calibration_reference_hash,
    selection_policy_status: report.selection_policy_status,
    post_hoc_selection_status: report.post_hoc_selection_status,
    partition_disjointness_status: report.partition_disjointness_status,
  }, null, 2));
}

main();
