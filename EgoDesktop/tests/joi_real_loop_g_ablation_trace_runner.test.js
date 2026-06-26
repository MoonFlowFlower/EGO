const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const test = require("node:test");

const {
  createJoiRealLoopTraceRunner,
  renderTraceRunnerReport,
} = require("../src/joiRealLoopGAblationTraceRunner");

function tempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "ego-joi-trace-runner-"));
}

function validEnv(traceDir, overrides = {}) {
  return {
    JOI_REAL_LOOP_G_ABLATION: "1",
    JOI_REAL_LOOP_CONDITION: "CURRENT_SHIM",
    JOI_REAL_LOOP_TRACE_DIR: traceDir,
    JOI_REAL_LOOP_LLM_MODE: "replay_locked",
    JOI_REAL_LOOP_PROMPT_PACK: "prompt-pack-sha",
    JOI_REAL_LOOP_SPLIT: "heldout",
    ...overrides,
  };
}

function validTurn(overrides = {}) {
  return {
    schema_version: "ego_desktop.chat_turn.v1",
    status: "ok",
    user_text: "record a bounded trace",
    bot_text: "trace response",
    expression_name: "记笔记",
    side_effects_executed: false,
    memory_write: false,
    tool_use: false,
    message_send: false,
    file_write: false,
    network_call: false,
    ...overrides,
  };
}

test("absent experiment flag keeps runner inert and writes no artifacts", () => {
  const outDir = tempDir();
  const runner = createJoiRealLoopTraceRunner({}, { repoRoot: process.cwd() });

  const result = runner.recordChatTurn({
    userText: "hello",
    turn: validTurn(),
  });

  assert.equal(runner.enabled, false);
  assert.equal(result.status, "disabled_default_off");
  assert.deepEqual(fs.readdirSync(outDir), []);
});

test("unlocked LLM mode blocks trace writes with explicit contract status", () => {
  const outDir = tempDir();
  const runner = createJoiRealLoopTraceRunner(
    validEnv(outDir, { JOI_REAL_LOOP_LLM_MODE: "live" }),
    { repoRoot: process.cwd() },
  );

  const result = runner.recordChatTurn({
    userText: "hello",
    turn: validTurn(),
  });

  assert.equal(result.status, "blocked_missing_llm_replay_contract");
  assert.deepEqual(fs.readdirSync(outDir), []);
});

test("enabled runner writes trace row through existing harness contract", () => {
  const outDir = tempDir();
  const runner = createJoiRealLoopTraceRunner(validEnv(outDir), {
    repoRoot: process.cwd(),
    sourceHashes: {
      ego_head: "ego-head",
      harness_hash: "harness-hash",
      trace_runner_hash: "trace-runner-hash",
    },
  });

  const result = runner.recordChatTurn({
    userText: "record a bounded trace",
    turn: validTurn(),
    rendererReady: {
      parameterSamples: { ParamAngleX: 1.25, ParamMouthOpenY: 0.1 },
    },
    replayInputs: {
      serialized_state_hash: "state-sha",
      observation_hash: "observation-sha",
    },
  });

  assert.equal(result.status, "trace_row_written");
  assert.equal(result.verdict_label, "blocked_missing_real_loop_entrypoint");
  const rowPath = path.join(outDir, "trace_rows.jsonl");
  const row = JSON.parse(fs.readFileSync(rowPath, "utf8").trim());
  assert.equal(row.condition_id, "CURRENT_SHIM");
  assert.equal(row.chat_turn.expression_name, "记笔记");
  assert.equal(row.renderer_idle_excluded, true);
  assert.deepEqual(row.renderer_idle_params_excluded_from_d, ["ParamMouthOpenY", "ParamJawOpen"]);
  assert.equal(row.adapter_output.adapter_status, "not_connected_trace_runner_v0");
  assert.match(row.row_hash, /^[a-f0-9]{64}$/);
});

test("renderer-ready metadata is recorded only when contract is enabled", () => {
  const outDir = tempDir();
  const runner = createJoiRealLoopTraceRunner(validEnv(outDir), { repoRoot: process.cwd() });

  const result = runner.recordRendererReady({
    rendererPayload: {
      modelLoaded: true,
      parameterSamples: { ParamAngleX: 2 },
      visualFitPass: true,
    },
  });

  assert.equal(result.status, "renderer_ready_recorded");
  const payload = JSON.parse(fs.readFileSync(path.join(outDir, "renderer_ready.json"), "utf8"));
  assert.equal(payload.model_loaded, true);
  assert.equal(payload.parameter_samples.ParamAngleX, 2);
  assert.equal(payload.renderer_idle_excluded, true);
});

test("authority-bearing adapter payload is rejected before artifact write", () => {
  const outDir = tempDir();
  const runner = createJoiRealLoopTraceRunner(validEnv(outDir), { repoRoot: process.cwd() });

  assert.throws(
    () => runner.recordChatTurn({
      userText: "bad",
      turn: validTurn(),
      adapterOutput: { action: "drive_runtime" },
    }),
    /adapterOutput contains runtime authority field/,
  );
  assert.equal(fs.existsSync(path.join(outDir, "trace_rows.jsonl")), false);
});

test("report text stays below route and subjectivity claims", () => {
  const report = renderTraceRunnerReport({
    status: "blocked_missing_real_loop_entrypoint",
    traceRowCount: 1,
    traceDir: "artifact-dir",
  });

  assert.match(report, /trace-runner contract only/);
  assert.match(report, /does not prove real-loop effect/);
  assert.doesNotMatch(report, /route-B pass/i);
  assert.doesNotMatch(report, /consciousness pass/i);
  assert.doesNotMatch(report, /alive status pass/i);
});

test("main process wires trace runner only through chat-turn and renderer-ready seams", () => {
  const mainSource = fs.readFileSync(path.join(__dirname, "..", "src", "main.js"), "utf8");

  assert.match(mainSource, /createJoiRealLoopTraceRunner/);
  assert.match(mainSource, /joiTraceRunner\.recordChatTurn/);
  assert.match(mainSource, /joiTraceRunner\.recordRendererReady/);
  assert.doesNotMatch(mainSource, /JOI_REAL_LOOP_G_ABLATION\s*=\s*["']1["']/);
});
