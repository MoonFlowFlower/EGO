const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");
const test = require("node:test");

const {
  createJoiRealLoopTraceRunner,
} = require("../src/joiRealLoopGAblationTraceRunner");
const { hashValue } = require("../src/joiRealLoopGAblationHarness");

const repoRoot = path.resolve(__dirname, "..", "..");
const frozenModules = [
  "EgoDesktop/src/joiRealLoopGAblationHarness.js",
  "EgoDesktop/src/joiRealLoopGAblationOfflineReplay.js",
  "EgoDesktop/src/joiRealLoopGAblationReplayEvaluator.js",
  "EgoDesktop/src/joiRealLoopGAblationCalibrationReference.js",
];

function loadAdapter() {
  return require("../src/joiRealLoopGAblationKernelStateAdapter");
}

function tempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "ego-r3-kernel-adoption-"));
}

function validEnv(traceDir) {
  return {
    JOI_REAL_LOOP_G_ABLATION: "1",
    JOI_REAL_LOOP_CONDITION: "CURRENT_SHIM",
    JOI_REAL_LOOP_TRACE_DIR: traceDir,
    JOI_REAL_LOOP_LLM_MODE: "replay_locked",
    JOI_REAL_LOOP_PROMPT_PACK: "r3-adoption-fixture-pack",
    JOI_REAL_LOOP_SPLIT: "heldout",
    JOI_REAL_LOOP_RUN_ID: "r3-adoption-test-run",
    JOI_REAL_LOOP_SEED: "r3-seed",
  };
}

function validTurn(step = 1) {
  return {
    schema_version: "ego_desktop.chat_turn.v1",
    status: "ok",
    user_text: `bounded adoption turn ${step}`,
    bot_text: `surface reply ${step}`,
    expression_name: "观测",
    pspc_scenario_id: "r3_kernel_adoption_fixture",
    side_effects_executed: false,
    memory_write: false,
    tool_use: false,
    message_send: false,
    file_write: false,
    network_call: false,
  };
}

function legacyRowHashPayload(row) {
  const legacy = { ...row };
  delete legacy.row_hash;
  delete legacy.kernel_adoption_v0;
  return legacy;
}

test("parity vectors cover the declared parity-safe value domain", () => {
  const adapter = loadAdapter();

  assert.equal(adapter.PARITY_VECTORS.length, 16);
  const ids = adapter.PARITY_VECTORS.map((item) => item.id).join("\n");
  for (const required of [
    "unicode",
    "cjk_keys",
    "nested",
    "negative_int",
    "max_safe_integer",
    "bool_null",
    "empty_containers",
    "decimal_string_float",
    "key_order_trap",
  ]) {
    assert.match(ids, new RegExp(required));
  }
  for (const vector of adapter.PARITY_VECTORS) {
    assert.match(adapter.canonicalSha256(vector.value), /^[a-f0-9]{64}$/);
    assert.equal(adapter.canonicalJsonStringify(JSON.parse(adapter.canonicalJsonStringify(vector.value))), adapter.canonicalJsonStringify(vector.value));
  }
});

test("kernel state hash controls are process-stable and mutation-sensitive", () => {
  const adapter = loadAdapter();
  const envelope = adapter.createKernelStateEnvelope({
    taskId: "ego-r3-adoption-slice-001a",
    runId: "run-state-hash",
    episodeId: "episode-state-hash",
    stepId: 1,
    substate: {
      semantic_label: "stable",
      non_integer_numeric_control: 1.25,
      nested: { count: -7 },
    },
    seedRegistry: { step_1: { seed: 12345, draw_index: 1 } },
    ablations: { llm_mode: "replay_locked" },
  });
  const sameEnvelope = JSON.parse(JSON.stringify(envelope));
  const mutatedEnvelope = adapter.createKernelStateEnvelope({
    taskId: "ego-r3-adoption-slice-001a",
    runId: "run-state-hash",
    episodeId: "episode-state-hash",
    stepId: 1,
    substate: {
      semantic_label: "mutated",
      non_integer_numeric_control: 1.25,
      nested: { count: -7 },
    },
    seedRegistry: { step_1: { seed: 12345, draw_index: 1 } },
    ablations: { llm_mode: "replay_locked" },
  });

  assert.equal(envelope.substates.joi_loop_state_v0.non_integer_numeric_control, "1.250000");
  assert.equal(adapter.canonicalSha256(envelope), adapter.canonicalSha256(sameEnvelope));
  assert.notEqual(adapter.canonicalSha256(envelope), adapter.canonicalSha256(mutatedEnvelope));

  const child = spawnSync(process.execPath, [
    "-e",
    `const a=require(${JSON.stringify(path.join(repoRoot, "EgoDesktop", "src", "joiRealLoopGAblationKernelStateAdapter.js"))}); const value=${JSON.stringify(envelope)}; process.stdout.write(a.canonicalSha256(value));`,
  ], { cwd: repoRoot, encoding: "utf8" });
  assert.equal(child.status, 0, child.stderr);
  assert.equal(child.stdout.trim(), adapter.canonicalSha256(envelope));
});

test("fresh-process replay x2 plus mid-episode resume has zero mismatches", () => {
  const adapter = loadAdapter();

  const result = adapter.runKernelAdoptionFixture({
    runId: "run-replay",
    episodeCount: 2,
    rendererId: "A",
  });

  assert.equal(result.replay_report.fresh_process_runs, 2);
  assert.equal(result.replay_report.fresh_process_mismatch_count, 0);
  assert.equal(result.replay_report.resume_mismatch_count, 0);
  assert.equal(result.replay_report.mismatch_total, 0);
  assert.equal(result.episodes.length, 2);
  for (const episode of result.episodes) {
    assert.equal(episode.trace_rows.every((row) => row.kernel_adoption_v0), true);
    assert.equal(episode.trace_rows.every((row) => row.kernel_adoption_v0.state_before_hash !== row.kernel_adoption_v0.state_after_hash), true);
  }
});

test("LLM-swap invariance keeps A/B kernel fields identical and flags leaky renderer C", () => {
  const adapter = loadAdapter();

  const report = adapter.runSwapInvarianceCheck({ runId: "run-swap" });

  assert.equal(report.ab_kernel_field_leak_count, 0);
  assert.equal(report.ab_kernel_fields_identical, true);
  assert.equal(report.renderer_surface_texts_differ, true);
  assert.equal(report.positive_control_c_detected, true);
  assert.equal(report.leaky_renderer_c_leak_count > 0, true);
});

test("trace runner hook is additive/default-off and frozen modules remain untouched", () => {
  const adapter = loadAdapter();
  const outDir = tempDir();
  const defaultRunner = createJoiRealLoopTraceRunner(validEnv(outDir), { repoRoot });
  defaultRunner.recordChatTurn({
    userText: "default off kernel hook",
    turn: validTurn(1),
  });
  const defaultRow = JSON.parse(fs.readFileSync(path.join(outDir, "trace_rows.jsonl"), "utf8").trim());
  assert.equal(defaultRow.kernel_adoption_v0, undefined);

  const hookedDir = tempDir();
  const before = adapter.createKernelStateEnvelope({
    runId: "trace-hook-run",
    episodeId: "trace-hook-episode",
    stepId: 0,
    substate: { semantic_label: "before" },
    seedRegistry: { step_0: { seed: 1, draw_index: 0 } },
  });
  const after = adapter.createKernelStateEnvelope({
    runId: "trace-hook-run",
    episodeId: "trace-hook-episode",
    stepId: 1,
    substate: { semantic_label: "after" },
    seedRegistry: { step_1: { seed: 2, draw_index: 1 } },
  });
  const hookedRunner = createJoiRealLoopTraceRunner(validEnv(hookedDir), {
    repoRoot,
    kernelAdoptionHook: () => adapter.buildKernelAdoptionBlock({
      stateBefore: before,
      stateAfter: after,
      stepId: 1,
      seedContext: { seed: 2, draw_index: 1 },
    }),
  });
  hookedRunner.recordChatTurn({
    userText: "hooked kernel adoption",
    turn: validTurn(2),
  });
  const hookedRow = JSON.parse(fs.readFileSync(path.join(hookedDir, "trace_rows.jsonl"), "utf8").trim());
  assert.match(hookedRow.kernel_adoption_v0.state_before_hash, /^[a-f0-9]{64}$/);
  assert.match(hookedRow.kernel_adoption_v0.state_after_hash, /^[a-f0-9]{64}$/);
  assert.equal(hookedRow.row_hash, hashValue(legacyRowHashPayload(hookedRow)));

  const diff = spawnSync("git", ["diff", "--name-only", "--", ...frozenModules], { cwd: repoRoot, encoding: "utf8" });
  assert.equal(diff.status, 0, diff.stderr);
  assert.equal(diff.stdout.trim(), "");
});

test("config_frozen is byte-stable and runner prints matching config", () => {
  const adapter = loadAdapter();
  const scriptPath = path.join(repoRoot, "EgoDesktop", "scripts", "run-joi-g-ablation-kernel-adoption.js");

  assert.equal(adapter.CONFIG_FROZEN.parity_vectors.count, 16);
  assert.equal(adapter.CONFIG_FROZEN.parity_vectors.sha256, adapter.PARITY_VECTOR_SHA256);
  assert.equal(adapter.CONFIG_FROZEN.trace_block.name, "kernel_adoption_v0");

  const expected = `${adapter.stablePrettyJson(adapter.CONFIG_FROZEN)}\n`;
  const printed = spawnSync(process.execPath, [scriptPath, "--print-config"], {
    cwd: repoRoot,
    encoding: "utf8",
  });
  assert.equal(printed.status, 0, printed.stderr);
  assert.equal(printed.stdout, expected);
});

test("battery regression executor uses configured timeout and preserves spawn_error detail", () => {
  const runner = require("../scripts/run-joi-g-ablation-kernel-adoption.js");

  assert.equal(runner.REGRESSION_COMMAND_TIMEOUT_MS, 900000);
  for (const spec of runner.buildRegressionCommandSpecs()) {
    assert.equal(spec.timeoutMs, runner.REGRESSION_COMMAND_TIMEOUT_MS, spec.label);
  }

  const spawnFailure = runner.runCommand(
    "spawn_failure_probe",
    "definitely-not-a-command-for-ego-r3-runner",
    [],
    { timeoutMs: 1000 },
  );
  assert.equal(spawnFailure.result_kind, "spawn_error");
  assert.notEqual(spawnFailure.exit_code, 124);
  assert.match(spawnFailure.error.message, /definitely-not-a-command-for-ego-r3-runner|ENOENT|not found|not recognized/i);
  assert.match(spawnFailure.command_line, /definitely-not-a-command-for-ego-r3-runner/);

  const timeout = runner.runCommand(
    "timeout_probe",
    process.execPath,
    ["-e", "setTimeout(() => {}, 2000)"],
    { timeoutMs: 100 },
  );
  assert.equal(timeout.result_kind, "timeout");
  assert.equal(timeout.exit_code, 124);
  assert.match(timeout.error.message, /timed out|ETIMEDOUT|timeout/i);
  assert.match(timeout.command_line, /setTimeout/);
});

test("TraceRunner no-fork detector rejects any removed body line", () => {
  const runner = require("../scripts/run-joi-g-ablation-kernel-adoption.js");

  const pureAdditive = [
    "diff --git a/EgoDesktop/src/joiRealLoopGAblationTraceRunner.js b/EgoDesktop/src/joiRealLoopGAblationTraceRunner.js",
    "index 86a7c4e0..ec64d973 100644",
    "--- a/EgoDesktop/src/joiRealLoopGAblationTraceRunner.js",
    "+++ b/EgoDesktop/src/joiRealLoopGAblationTraceRunner.js",
    "@@ -1,3 +1,4 @@",
    " const existing = true;",
    "+const kernelAdoptionHook = options.kernelAdoptionHook || null;",
    " module.exports = {};",
  ].join("\n");
  const withDeletion = [
    "diff --git a/EgoDesktop/src/joiRealLoopGAblationTraceRunner.js b/EgoDesktop/src/joiRealLoopGAblationTraceRunner.js",
    "index 86a7c4e0..ec64d973 100644",
    "--- a/EgoDesktop/src/joiRealLoopGAblationTraceRunner.js",
    "+++ b/EgoDesktop/src/joiRealLoopGAblationTraceRunner.js",
    "@@ -1,3 +1,4 @@",
    "-const existing = true;",
    "+const kernelAdoptionHook = options.kernelAdoptionHook || null;",
    " module.exports = {};",
  ].join("\n");

  assert.equal(runner.analyzeTraceRunnerDiff(pureAdditive).pure_additive, true);
  const deletionAnalysis = runner.analyzeTraceRunnerDiff(withDeletion);
  assert.equal(deletionAnalysis.pure_additive, false);
  assert.equal(deletionAnalysis.removed_body_line_count, 1);
  assert.deepEqual(deletionAnalysis.removed_body_lines, ["-const existing = true;"]);
});
