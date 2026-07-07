#!/usr/bin/env node
const fs = require("node:fs");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const adapter = require("../src/joiRealLoopGAblationKernelStateAdapter");

const repoRoot = path.resolve(__dirname, "..", "..");
const defaultArtifactDir = path.join(repoRoot, "artifacts", "ego_r3_adoption_slice_001a");
const frozenModules = [
  "EgoDesktop/src/joiRealLoopGAblationHarness.js",
  "EgoDesktop/src/joiRealLoopGAblationOfflineReplay.js",
  "EgoDesktop/src/joiRealLoopGAblationReplayEvaluator.js",
  "EgoDesktop/src/joiRealLoopGAblationCalibrationReference.js",
];
const forbiddenRuntimePaths = [
  "EgoDesktop/src/main.js",
  "EgoDesktop/src/preload.js",
  "EgoDesktop/src/chatTurn.js",
  "EgoDesktop/viewer",
  "scripts/ego_kernel",
  "EgoOperator",
];

function parseArgs(argv) {
  const parsed = {
    outDir: defaultArtifactDir,
    runId: `r3_adoption_${new Date().toISOString().replace(/[-:.TZ]/g, "").slice(0, 14)}`,
    printConfig: false,
    guardSeconds: 1800,
    baseCommit: "",
  };
  for (let index = 0; index < argv.length; index += 1) {
    const item = argv[index];
    if (item === "--print-config") {
      parsed.printConfig = true;
    } else if (item === "--out") {
      parsed.outDir = path.resolve(argv[index + 1]);
      index += 1;
    } else if (item === "--run-id") {
      parsed.runId = String(argv[index + 1] || "");
      index += 1;
    } else if (item === "--guard-seconds") {
      parsed.guardSeconds = Number(argv[index + 1] || 1800);
      index += 1;
    } else if (item === "--base-commit") {
      parsed.baseCommit = String(argv[index + 1] || "");
      index += 1;
    }
  }
  return parsed;
}

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function writeText(filePath, text) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, text, "utf8");
}

function writeJson(filePath, value) {
  writeText(filePath, `${adapter.stablePrettyJson(value)}\n`);
}

function runCommand(label, command, args, options = {}) {
  const started = Date.now();
  const result = spawnSync(command, args, {
    cwd: options.cwd || repoRoot,
    encoding: "utf8",
    timeout: options.timeoutMs || 120000,
    input: options.input,
    env: { ...process.env, ...(options.env || {}) },
  });
  return {
    label,
    command: [command, ...args],
    cwd: options.cwd || repoRoot,
    exit_code: result.status === null ? 124 : result.status,
    signal: result.signal || "",
    duration_ms: Date.now() - started,
    stdout: result.stdout || "",
    stderr: result.stderr || "",
  };
}

function git(args) {
  return runCommand("git", "git", args, { timeoutMs: 60000 });
}

function findLandingCommit() {
  const logged = git(["log", "--grep=ego-r3 adoption slice 001a: land stage card + mutation scope", "-n", "1", "--format=%H"]);
  return logged.exit_code === 0 ? logged.stdout.trim().split(/\s+/)[0] || "" : "";
}

function provenance(producerFunction, inputArtifacts, runId, extra = {}) {
  return {
    producer_function: producerFunction,
    input_artifacts: inputArtifacts,
    run_id: runId,
    seed_context: extra.seed_context || [],
    episode_ids: extra.episode_ids || [],
    aggregation_rule: extra.aggregation_rule || "",
    code_path_hash: adapter.canonicalSha256({
      adapter: fs.readFileSync(path.join(repoRoot, "EgoDesktop", "src", "joiRealLoopGAblationKernelStateAdapter.js"), "utf8"),
      producerFunction,
    }),
  };
}

function runParityGate(runId) {
  const vectors = adapter.PARITY_VECTORS.map((vector) => ({
    id: vector.id,
    value: vector.value,
    js_canonical: adapter.canonicalJsonStringify(vector.value),
    js_hash: adapter.canonicalSha256(vector.value),
  }));
  const pyCode = [
    "import json,sys",
    "from scripts.ego_kernel.state import canonical_json_dumps, canonical_sha256",
    "vectors=json.load(sys.stdin)",
    "out=[]",
    "for v in vectors:",
    "    out.append({'id':v['id'],'py_canonical':canonical_json_dumps(v['value']),'py_hash':canonical_sha256(v['value'])})",
    "print(json.dumps(out, ensure_ascii=False, sort_keys=True, separators=(',', ':')))",
  ].join("\n");
  const py = runCommand("python_parity", "python", ["-c", pyCode], {
    input: JSON.stringify(vectors),
    timeoutMs: 120000,
  });
  let pyVectors = [];
  if (py.exit_code === 0) {
    pyVectors = JSON.parse(py.stdout);
  }
  const details = vectors.map((vector) => {
    const pyVector = pyVectors.find((item) => item.id === vector.id) || {};
    return {
      id: vector.id,
      js_hash: vector.js_hash,
      py_hash: pyVector.py_hash || "",
      canonical_equal: vector.js_canonical === (pyVector.py_canonical || ""),
      hash_equal: vector.js_hash === (pyVector.py_hash || ""),
    };
  });
  const equalCount = details.filter((item) => item.canonical_equal && item.hash_equal).length;
  return {
    status: py.exit_code === 0 && equalCount === 16 ? "pass" : "fail",
    equal_count: equalCount,
    total_count: 16,
    parity_vector_sha256: adapter.PARITY_VECTOR_SHA256,
    details,
    command: py,
    provenance: provenance(
      "runParityGate",
      ["EgoDesktop/src/joiRealLoopGAblationKernelStateAdapter.js", "scripts/ego_kernel/state.py"],
      runId,
      { aggregation_rule: "all 16 vectors require canonical string and sha256 equality" },
    ),
  };
}

function runStateHashGate(runId) {
  const state = adapter.createKernelStateEnvelope({
    runId,
    episodeId: "state_hash_control",
    stepId: 1,
    substate: { semantic_label: "same", decimal: 1.25 },
    seedRegistry: { step_1: { seed: 123, draw_index: 1 } },
    ablations: { llm_mode: "replay_locked" },
  });
  const same = JSON.parse(JSON.stringify(state));
  const mutated = adapter.createKernelStateEnvelope({
    runId,
    episodeId: "state_hash_control",
    stepId: 1,
    substate: { semantic_label: "mutated", decimal: 1.25 },
    seedRegistry: { step_1: { seed: 123, draw_index: 1 } },
    ablations: { llm_mode: "replay_locked" },
  });
  const child = runCommand("node_state_hash_fresh_process", process.execPath, [
    "-e",
    [
      `const adapter=require(${JSON.stringify(path.join(repoRoot, "EgoDesktop", "src", "joiRealLoopGAblationKernelStateAdapter.js"))});`,
      "const state=JSON.parse(process.argv[1]);",
      "process.stdout.write(adapter.canonicalSha256(state));",
    ].join("\n"),
    JSON.stringify(state),
  ]);
  const hash = adapter.canonicalSha256(state);
  const sameHash = adapter.canonicalSha256(same);
  const mutatedHash = adapter.canonicalSha256(mutated);
  const pass = hash === sameHash && hash !== mutatedHash && child.exit_code === 0 && child.stdout.trim() === hash;
  return {
    status: pass ? "pass" : "fail",
    same_hash_equal: hash === sameHash,
    mutated_hash_differs: hash !== mutatedHash,
    fresh_process_equal: child.stdout.trim() === hash,
    decimal_control: state.substates.joi_loop_state_v0.decimal,
    hashes: { hash, sameHash, mutatedHash, freshProcessHash: child.stdout.trim() },
    command: child,
    provenance: provenance(
      "runStateHashGate",
      ["EgoDesktop/src/joiRealLoopGAblationKernelStateAdapter.js"],
      runId,
      { aggregation_rule: "same envelope same hash; mutated substate different; fresh process same" },
    ),
  };
}

function runNoForkAndRegressionGate(runId, baseCommit, artifactDir) {
  const base = baseCommit || findLandingCommit();
  const frozenDiffStat = base ? git(["diff", "--stat", `${base}..HEAD`, "--", ...frozenModules]) : { exit_code: 1, stdout: "", stderr: "landing commit not found" };
  const traceRunnerDiff = base ? git(["diff", `${base}..HEAD`, "--", "EgoDesktop/src/joiRealLoopGAblationTraceRunner.js"]) : { exit_code: 1, stdout: "", stderr: "landing commit not found" };
  const forbiddenDiff = base ? git(["diff", "--name-only", `${base}..HEAD`, "--", ...forbiddenRuntimePaths]) : { exit_code: 1, stdout: "", stderr: "landing commit not found" };
  const regressionCommands = [
    runCommand("kernel_adoption_node_test", "node", ["--test", "EgoDesktop/tests/joi_real_loop_g_ablation_kernel_adoption.test.js"], { timeoutMs: 120000 }),
    runCommand("egodesktop_npm_test", "npm", ["test"], { cwd: path.join(repoRoot, "EgoDesktop"), timeoutMs: 180000 }),
    runCommand("python_parity_test", "python", ["-m", "pytest", "-q", "tests/test_ego_r3_adoption_parity.py"], { timeoutMs: 120000 }),
    runCommand("joi_corpus_admission", "python", ["-m", "pytest", "-q", "tests/test_joi_corpus_admission.py"], { timeoutMs: 120000 }),
    runCommand("py_compile_parity_test", "python", ["-m", "py_compile", "tests/test_ego_r3_adoption_parity.py"], { timeoutMs: 120000 }),
    runCommand("lint_repo", "python", ["scripts/codex/lint_repo.py"], { timeoutMs: 180000 }),
    runCommand("verify_repo_fast", "python", ["scripts/codex/verify_repo.py", "--mode", "fast"], { timeoutMs: 180000 }),
  ];
  writeJson(path.join(artifactDir, "regression_commands.json"), regressionCommands);
  const regressionPass = regressionCommands.every((item) => item.exit_code === 0);
  const traceHookOnly = traceRunnerDiff.exit_code === 0
    && traceRunnerDiff.stdout.includes("kernelAdoptionHook")
    && !traceRunnerDiff.stdout.includes("JOI_REAL_LOOP_G_ABLATION = \"1\"");
  const frozenClean = frozenDiffStat.exit_code === 0 && frozenDiffStat.stdout.trim() === "";
  const forbiddenClean = forbiddenDiff.exit_code === 0 && forbiddenDiff.stdout.trim() === "";
  return {
    status: frozenClean && traceHookOnly && forbiddenClean && regressionPass ? "pass" : "fail",
    base_commit: base,
    frozen_modules_diffstat: frozenDiffStat.stdout,
    trace_runner_hook_only: traceHookOnly,
    forbidden_runtime_diff: forbiddenDiff.stdout,
    regression_pass: regressionPass,
    regression_commands: regressionCommands.map((item) => ({
      label: item.label,
      exit_code: item.exit_code,
      duration_ms: item.duration_ms,
      stdout_tail: item.stdout.slice(-2000),
      stderr_tail: item.stderr.slice(-2000),
    })),
    provenance: provenance(
      "runNoForkAndRegressionGate",
      ["git diff L1..HEAD", "EgoDesktop npm test", "pytest corpus/parity", "lint_repo", "verify_repo fast"],
      runId,
      { aggregation_rule: "frozen diffstat empty, trace hook present/default-off, forbidden paths clean, regression commands exit 0" },
    ),
  };
}

function runSchemaGate(runId, artifactDir, fixtureResult) {
  const notesPath = path.join(repoRoot, "docs", "codex", "tasks", "ego-r3-adoption-slice-001a", "SCHEMA_NOTES.md");
  const notes = fs.existsSync(notesPath) ? fs.readFileSync(notesPath, "utf8") : "";
  const configPath = path.join(artifactDir, "config_frozen.json");
  const expectedConfig = `${adapter.stablePrettyJson(adapter.CONFIG_FROZEN)}\n`;
  const configReadback = fs.existsSync(configPath) ? fs.readFileSync(configPath, "utf8") : "";
  const rows = fixtureResult.episodes.flatMap((episode) => episode.trace_rows);
  const allRowsHaveBlock = rows.every((row) => row.kernel_adoption_v0 && row.kernel_adoption_v0.state_before_hash && row.kernel_adoption_v0.state_after_hash);
  const pass = notes.includes("kernel_adoption_v0")
    && notes.includes("fixed_6")
    && configReadback === expectedConfig
    && allRowsHaveBlock;
  return {
    status: pass ? "pass" : "fail",
    schema_notes_path: notesPath,
    schema_notes_has_trace_block: notes.includes("kernel_adoption_v0"),
    schema_notes_has_decimal_rule: notes.includes("fixed_6"),
    config_frozen_byte_match: configReadback === expectedConfig,
    trace_rows_with_block: rows.filter((row) => row.kernel_adoption_v0).length,
    trace_row_count: rows.length,
    provenance: provenance(
      "runSchemaGate",
      ["docs/codex/tasks/ego-r3-adoption-slice-001a/SCHEMA_NOTES.md", "config_frozen.json", "trace jsonl"],
      runId,
      { aggregation_rule: "notes mention block and decimal rule, config bytes match, every trace row carries kernel block" },
    ),
  };
}

function verdictFromGates(gates) {
  const failing = Object.entries(gates)
    .filter(([, gate]) => gate.status !== "pass")
    .map(([name]) => name);
  if (failing.length === 0) {
    return { verdict: "r3_adoption_slice_pass", failing_gates: [] };
  }
  if (failing.includes("G-R3A-PARITY")) {
    return { verdict: "instrument_invalid_parity", failing_gates: failing };
  }
  if (gates["G-R3A-SWAP"] && gates["G-R3A-SWAP"].positive_control_c_detected === false) {
    return { verdict: "instrument_invalid_leak_detector_blind", failing_gates: failing };
  }
  return { verdict: `r3_adoption_fail_${failing[0].toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "")}`, failing_gates: failing };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.printConfig) {
    process.stdout.write(`${adapter.stablePrettyJson(adapter.CONFIG_FROZEN)}\n`);
    return 0;
  }

  const started = Date.now();
  ensureDir(args.outDir);
  writeJson(path.join(args.outDir, "config_frozen.json"), adapter.CONFIG_FROZEN);
  writeJson(path.join(args.outDir, "parity_vectors.json"), adapter.PARITY_VECTORS.map((vector) => ({ id: vector.id, value: vector.value })));

  const gates = {};
  const fixtureResult = adapter.runKernelAdoptionFixture({
    runId: args.runId,
    episodeCount: 2,
    rendererId: "A",
  });
  for (const episode of fixtureResult.episodes) {
    const jsonl = episode.trace_rows.map((row) => JSON.stringify(row)).join("\n");
    writeText(path.join(args.outDir, `trace_${episode.episode_id}.jsonl`), `${jsonl}\n`);
  }

  gates["G-R3A-PARITY"] = runParityGate(args.runId);
  gates["G-R3A-STATE-HASH"] = runStateHashGate(args.runId);
  gates["G-R3A-REPLAY"] = {
    status: fixtureResult.replay_report.mismatch_total === 0 ? "pass" : "fail",
    ...fixtureResult.replay_report,
    provenance: provenance(
      "adapter.runKernelAdoptionFixture.replay_report",
      ["serialized initial envelopes", "input logs", "trace rows"],
      args.runId,
      {
        episode_ids: fixtureResult.episodes.map((episode) => episode.episode_id),
        seed_context: fixtureResult.seed_context,
        aggregation_rule: fixtureResult.replay_report.aggregation_rule,
      },
    ),
  };
  gates["G-R3A-SWAP"] = {
    status: fixtureResult.swap_report.ab_kernel_field_leak_count === 0 && fixtureResult.swap_report.positive_control_c_detected ? "pass" : "fail",
    ...fixtureResult.swap_report,
    provenance: provenance(
      "adapter.runSwapInvarianceCheck",
      ["deterministic renderers A/B/C", "kernel_adoption_v0 projections"],
      args.runId,
      { aggregation_rule: fixtureResult.swap_report.aggregation_rule },
    ),
  };
  gates["G-R3A-NO-FORK"] = runNoForkAndRegressionGate(args.runId, args.baseCommit, args.outDir);
  gates["G-R3A-SCHEMA"] = runSchemaGate(args.runId, args.outDir, fixtureResult);

  writeJson(path.join(args.outDir, "parity_report.json"), gates["G-R3A-PARITY"]);
  writeJson(path.join(args.outDir, "replay_report.json"), gates["G-R3A-REPLAY"]);
  writeJson(path.join(args.outDir, "swap_report.json"), gates["G-R3A-SWAP"]);
  writeJson(path.join(args.outDir, "regression_report.json"), gates["G-R3A-NO-FORK"]);

  const verdict = verdictFromGates(gates);
  const durationMs = Date.now() - started;
  const guardBreached = durationMs > args.guardSeconds * 1000;
  if (guardBreached) {
    verdict.failing_gates.push("GUARD_BREACH");
  }
  const result = {
    schema_version: "ego.r3_adoption.result.v0",
    verdict: guardBreached ? "r3_adoption_fail_guard_breach" : verdict.verdict,
    failing_gates: verdict.failing_gates,
    run_id: args.runId,
    claim_ceiling: adapter.CLAIM_CEILING,
    gates,
    config_frozen_readback: {
      path: path.join(args.outDir, "config_frozen.json"),
      sha256: adapter.canonicalSha256(adapter.CONFIG_FROZEN),
      parity_vector_sha256: adapter.PARITY_VECTOR_SHA256,
      byte_match: fs.readFileSync(path.join(args.outDir, "config_frozen.json"), "utf8") === `${adapter.stablePrettyJson(adapter.CONFIG_FROZEN)}\n`,
    },
    guard: {
      guard_seconds: args.guardSeconds,
      duration_ms: durationMs,
      breached: guardBreached,
    },
    what_this_does_not_prove:
      "does not prove mechanism validity, learning, durable memory efficacy, runtime integration safety, stable user benefit, live autonomy, functional selfhood, agency, consciousness, subjective experience, or real emotion",
  };
  writeJson(path.join(args.outDir, "result.json"), result);
  writeJson(path.join(args.outDir, "failure_manifest.json"), {
    schema_version: "ego.r3_adoption.failure_manifest.v0",
    verdict: result.verdict,
    failing_gates: result.failing_gates,
    failures: result.failing_gates.map((gate) => ({
      gate,
      gate_result: gates[gate] || { status: "fail" },
    })),
  });
  writeJson(path.join(args.outDir, "run_log.json"), {
    schema_version: "ego.r3_adoption.run_log.v0",
    command: [process.execPath, __filename, ...process.argv.slice(2)],
    run_id: args.runId,
    started_at_unix_ms: started,
    duration_ms: durationMs,
    guard_seconds: args.guardSeconds,
    exit_code: result.failing_gates.length === 0 ? 0 : 1,
    artifact_dir: args.outDir,
  });
  process.stdout.write(`${result.verdict}\n`);
  return result.failing_gates.length === 0 ? 0 : 1;
}

if (require.main === module) {
  process.exitCode = main();
}
