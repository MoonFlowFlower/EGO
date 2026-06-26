const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const { buildJoiRealLoopTraceRow, hashValue } = require("../src/joiRealLoopGAblationHarness");
const {
  CLAIM_CEILING,
  evaluateTraceRows,
  injectLeakagePositiveControl,
  parseTraceRowsJsonl,
  renderEvaluationReport,
  scanForLeakage,
  writeEvaluationReport,
} = require("../src/joiRealLoopGAblationReplayEvaluator");

const FORBIDDEN_ATTRIBUTION_PASS = new RegExp(`real_loop_causal_path_attribution_${"pass"}`);
const FORBIDDEN_ROUTE_PASS = new RegExp(`route-B ${"pass"}`, "i");

function sampleRow(overrides = {}) {
  const creatureState = {
    schema_version: "ego_desktop.joi_trace_runner.placeholder_state.v0",
    state_source: "not_connected_in_trace_runner_v0",
    condition: "CURRENT_SHIM",
  };
  const publicInputs = {
    user_text_hash: "user-text-hash",
    condition: "CURRENT_SHIM",
    prompt_pack: "prompt-pack",
    split: "heldout",
    llm_mode: "replay_locked",
  };
  return buildJoiRealLoopTraceRow({
    runId: "run-001",
    conditionId: "CURRENT_SHIM",
    turnId: "turn-001",
    tickId: "tick-001",
    seed: "seed-001",
    sourceHashes: { harness_hash: "harness", trace_runner_hash: "trace-runner" },
    promptId: "prompt-001",
    promptPackHash: "prompt-pack",
    splitId: "heldout",
    llmReplayId: "none",
    chatTurn: { status: "ok", expression_name: "记笔记", bot_text: "noted" },
    creatureState,
    adapterOutput: {
      source: "joi_real_loop_trace_runner_v0",
      adapter_status: "not_connected_trace_runner_v0",
      output_authority: "none",
    },
    publicInputs,
    replayInputs: {
      serialized_state_hash: hashValue(creatureState),
      observation_hash: hashValue(publicInputs),
      replay_policy: "trace_runner_v0_collect_only",
    },
    outputEvent: { order: 1, timestamp_ms: 1 },
    ...overrides,
  });
}

test("evaluator blocks placeholder rows while recomputing row hashes", () => {
  const report = evaluateTraceRows([sampleRow()], { runId: "eval-001" });

  assert.equal(report.claim_ceiling, CLAIM_CEILING);
  assert.equal(report.status, "blocked_unreplayable_runtime_trace");
  assert.equal(report.rows_evaluated, 1);
  assert.equal(report.row_results[0].hash_integrity_status, "pass");
  assert.equal(report.row_results[0].replay_integrity_status, "blocked_unreplayable_runtime_trace");
  assert.ok(report.blockers.includes("placeholder_creature_state"));
  assert.ok(report.blockers.includes("placeholder_adapter_output"));
  assert.equal(report.leakage_scan_status, "pass");
  assert.equal(report.leakage_positive_control_status, "pass");
  assert.doesNotMatch(JSON.stringify(report), FORBIDDEN_ATTRIBUTION_PASS);
});

test("leakage positive control is detected and required", () => {
  const clean = sampleRow();
  const injected = injectLeakagePositiveControl(clean);
  const cleanScan = scanForLeakage(clean);
  const injectedScan = scanForLeakage(injected);

  assert.equal(cleanScan.status, "pass");
  assert.equal(injectedScan.status, "fail");
  assert.ok(injectedScan.findings.some((finding) => finding.path.includes("future_target_label")));
  assert.ok(injectedScan.findings.some((finding) => finding.path.includes("memory_write")));
});

test("tampered row hashes block integrity preflight", () => {
  const tampered = { ...sampleRow(), public_inputs_hash: "not-a-valid-hash" };
  const report = evaluateTraceRows([tampered], { runId: "eval-002" });

  assert.equal(report.status, "blocked_trace_integrity_failure");
  assert.equal(report.row_results[0].hash_integrity_status, "fail");
  assert.ok(report.row_results[0].hash_failures.includes("public_inputs_hash"));
});

test("jsonl parser and writer produce underclaiming reports", () => {
  const outDir = fs.mkdtempSync(path.join(os.tmpdir(), "ego-joi-replay-eval-"));
  const rowsPath = path.join(outDir, "trace_rows.jsonl");
  fs.writeFileSync(rowsPath, `${JSON.stringify(sampleRow())}\n`, "utf8");

  const parsed = parseTraceRowsJsonl(fs.readFileSync(rowsPath, "utf8"));
  assert.equal(parsed.length, 1);

  const result = writeEvaluationReport({ rowsPath, outDir, runId: "eval-003" });
  assert.equal(result.status, "blocked_unreplayable_runtime_trace");
  assert.equal(fs.existsSync(path.join(outDir, "evaluation_report.json")), true);
  assert.equal(fs.existsSync(path.join(outDir, "EVALUATION_REPORT.md")), true);

  const markdown = renderEvaluationReport(result);
  assert.match(markdown, /replay\/leakage evaluator contract only/);
  assert.match(markdown, /blocked_unreplayable_runtime_trace/);
  assert.doesNotMatch(markdown, FORBIDDEN_ROUTE_PASS);
  assert.doesNotMatch(markdown, /consciousness pass/i);
});
