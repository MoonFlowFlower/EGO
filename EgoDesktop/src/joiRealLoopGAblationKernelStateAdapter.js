const crypto = require("node:crypto");
const { spawnSync } = require("node:child_process");

const TASK_ID = "ego-r3-adoption-slice-001a";
const CLAIM_CEILING = "r3_adoption_engineering_only";
const KERNEL_STATE_SCHEMA_VERSION = "kernel_state_v0";
const SUBSTATE_NAME = "joi_loop_state_v0";
const TRACE_BLOCK_NAME = "kernel_adoption_v0";
const DECIMAL_STRING_FORMAT = "fixed_6";
const MAX_SAFE_INTEGER = 9007199254740991;

function deepFreeze(value) {
  if (value && typeof value === "object" && !Object.isFrozen(value)) {
    Object.freeze(value);
    for (const child of Object.values(value)) {
      deepFreeze(child);
    }
  }
  return value;
}

function isPlainObject(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return false;
  }
  const proto = Object.getPrototypeOf(value);
  return proto === Object.prototype || proto === null;
}

function canonicalizeForJson(value, label = "value") {
  if (value === null || typeof value === "string" || typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    if (!Number.isSafeInteger(value)) {
      throw new Error(`${label} contains non-integer or unsafe numeric value`);
    }
    return value;
  }
  if (Array.isArray(value)) {
    return value.map((item, index) => canonicalizeForJson(item, `${label}[${index}]`));
  }
  if (isPlainObject(value)) {
    return Object.keys(value).sort().reduce((acc, key) => {
      const child = value[key];
      if (child === undefined) {
        throw new Error(`${label}.${key} contains undefined`);
      }
      acc[key] = canonicalizeForJson(child, `${label}.${key}`);
      return acc;
    }, {});
  }
  throw new Error(`${label} is outside the parity-safe JSON domain`);
}

function canonicalJsonStringify(value) {
  return JSON.stringify(canonicalizeForJson(value));
}

function canonicalSha256(value) {
  return crypto.createHash("sha256").update(canonicalJsonStringify(value), "utf8").digest("hex");
}

function stablePrettyJson(value) {
  return JSON.stringify(canonicalizeForJson(value), null, 2);
}

function sha256Text(text) {
  return crypto.createHash("sha256").update(String(text), "utf8").digest("hex");
}

function decimalString(value) {
  if (!Number.isFinite(value)) {
    throw new Error("non-finite numeric value cannot enter kernel state");
  }
  return value.toFixed(6);
}

function sanitizeForKernelState(value, label = "substate") {
  if (value === null || typeof value === "string" || typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    if (Number.isSafeInteger(value)) {
      return value;
    }
    return decimalString(value);
  }
  if (Array.isArray(value)) {
    return value.map((item, index) => sanitizeForKernelState(item, `${label}[${index}]`));
  }
  if (isPlainObject(value)) {
    return Object.keys(value).sort().reduce((acc, key) => {
      const child = value[key];
      if (child === undefined) {
        throw new Error(`${label}.${key} contains undefined`);
      }
      acc[key] = sanitizeForKernelState(child, `${label}.${key}`);
      return acc;
    }, {});
  }
  throw new Error(`${label} contains unsupported value type`);
}

function normalizeSeedRegistry(seedRegistry) {
  const safe = seedRegistry && typeof seedRegistry === "object" ? seedRegistry : {};
  return sanitizeForKernelState(safe, "seed_registry");
}

function createKernelStateEnvelope({
  taskId = TASK_ID,
  runId = "r3_adoption_run",
  episodeId = "episode_001",
  stepId = 0,
  substate = {},
  seedRegistry = {},
  ablations = {},
} = {}) {
  const stepNumber = Number(stepId);
  if (!Number.isSafeInteger(stepNumber) || stepNumber < 0) {
    throw new Error("stepId must be a non-negative safe integer");
  }
  return {
    schema_version: KERNEL_STATE_SCHEMA_VERSION,
    task_id: String(taskId),
    run_id: String(runId),
    episode_id: String(episodeId),
    step_id: stepNumber,
    substates: {
      [SUBSTATE_NAME]: sanitizeForKernelState(substate, SUBSTATE_NAME),
    },
    seed_registry: normalizeSeedRegistry(seedRegistry),
    ablations: sanitizeForKernelState(ablations, "ablations"),
  };
}

function cloneJson(value) {
  return JSON.parse(JSON.stringify(value));
}

function buildKernelAdoptionBlock({ stateBefore, stateAfter, stepId, seedContext }) {
  return {
    state_before_hash: canonicalSha256(stateBefore),
    state_after_hash: canonicalSha256(stateAfter),
    step_id: Number(stepId),
    seed_context: sanitizeForKernelState(seedContext || {}, "seed_context"),
  };
}

const PARITY_VECTORS = deepFreeze([
  { id: "unicode_string_beta_cjk", value: { text: "βeta 椰果" } },
  { id: "cjk_keys_sorted", value: { 乙: "two", 甲: "one", 丁: "four" } },
  { id: "nested_object_array", value: { z: [{ b: 2, a: 1 }], a: { y: false, x: true } } },
  { id: "negative_int", value: { n: -123456789 } },
  { id: "max_safe_integer_2pow53_minus_1", value: { max: MAX_SAFE_INTEGER } },
  { id: "bool_null_mix", value: { truth: true, falsehood: false, none: null } },
  { id: "empty_containers", value: { arr: [], obj: {} } },
  { id: "decimal_string_float_positive", value: { fixed: "1.250000" } },
  { id: "decimal_string_float_negative", value: { fixed: "-0.125000" } },
  { id: "key_order_trap_ascii", value: { b: 1, aa: 2, a: 3 } },
  { id: "key_order_trap_nested_cjk", value: { outer: { 龙: "dragon", 龟: "turtle", a: "latin" } } },
  { id: "array_preserves_order", value: ["z", "a", { b: "kept", a: "sorted" }] },
  { id: "zero_and_negative_one", value: { zero: 0, minus_one: -1 } },
  { id: "escaped_string_controls", value: { quote: "\"", backslash: "\\", newline: "\n" } },
  { id: "deep_null_bool_cjk", value: { 层: [{ inner: null }, { ok: true }] } },
  { id: "seed_registry_shape", value: { seed_registry: { step_1: { seed: 61, draw_index: 0 } } } },
]);

const PARITY_VECTOR_SHA256 = canonicalSha256(
  PARITY_VECTORS.map((vector) => ({ id: vector.id, value: vector.value })),
);

const FIXTURE_TURNS = deepFreeze([
  {
    turn_id: "turn_001",
    tick_id: "tick_001",
    user_text: "你觉得黑暗之魂怎么样",
    semantic_intent: "opinion_soulslike",
    locked_semantic_output: "bounded_preference_discussion",
    expression_name: "思考",
    pspc_scenario_id: "ordinary_opinion",
    numeric_signal: 0.125,
  },
  {
    turn_id: "turn_002",
    tick_id: "tick_002",
    user_text: "换句话说，你认为黑暗之魂如何",
    semantic_intent: "opinion_soulslike_paraphrase",
    locked_semantic_output: "bounded_preference_discussion",
    expression_name: "点头",
    pspc_scenario_id: "ordinary_opinion_paraphrase",
    numeric_signal: 0.25,
  },
  {
    turn_id: "turn_003",
    tick_id: "tick_003",
    user_text: "只记录状态，不要调用真实模型",
    semantic_intent: "replay_locked_instruction",
    locked_semantic_output: "no_live_llm_ack",
    expression_name: "记录",
    pspc_scenario_id: "replay_lock",
    numeric_signal: 0.375,
  },
]);

const CONFIG_FROZEN = deepFreeze({
  schema_version: "ego.r3_adoption.config_frozen.v0",
  task: TASK_ID,
  version_probe: "R3-ADOPTION-SLICE-001A rev-A 2026-07-07",
  claim_ceiling: CLAIM_CEILING,
  trace_block: {
    name: TRACE_BLOCK_NAME,
    additive_only: true,
    default_off: true,
    fields: ["state_before_hash", "state_after_hash", "step_id", "seed_context"],
  },
  parity_vectors: {
    count: 16,
    sha256: PARITY_VECTOR_SHA256,
    value_domain: "object/array/string/bool/null/safe-int; non-integer numerics encoded as fixed_6 decimal strings before hashing",
  },
  thresholds: {
    parity_required_equal: "16/16",
    replay_fresh_process_runs: 2,
    replay_resume: "floor(turns/2)",
    swap_ab_kernel_leak_floor: 0,
    leaky_renderer_positive_control_required: true,
    episodes: 2,
    guard_seconds: 1800,
  },
  llm_mode: "LLM_REPLAY_LOCKED",
});

function deterministicInt(label) {
  const digest = sha256Text(label);
  return parseInt(digest.slice(0, 12), 16);
}

function initialSubstate() {
  return {
    schema_version: "joi_loop_state_v0",
    fixture_family: "existing_joi_real_loop_trace_runner_fixture_v0",
    turn_count: 0,
    semantic_history: [],
    last_semantic_intent: "",
    last_locked_semantic_output: "",
    cumulative_observation_hash: "0".repeat(64),
    decimal_format: DECIMAL_STRING_FORMAT,
  };
}

function initialEnvelope({ runId, episodeId, rendererId = "A" }) {
  return createKernelStateEnvelope({
    runId,
    episodeId,
    stepId: 0,
    substate: initialSubstate(),
    seedRegistry: {
      base: {
        seed: deterministicInt(`${TASK_ID}:${runId}:${episodeId}:base`),
        draw_index: 0,
      },
    },
    ablations: {
      llm_mode: "replay_locked",
      renderer_family: rendererId === "C" ? "positive_control_c" : "swap_ab_semantic_locked",
    },
  });
}

function rendererSurface(turn, rendererId) {
  if (rendererId === "B") {
    return `B面回复：${turn.locked_semantic_output}`;
  }
  if (rendererId === "C") {
    return `C面泄漏控件：${turn.locked_semantic_output}`;
  }
  return `A面回复：${turn.locked_semantic_output}`;
}

function transitionEnvelope(before, turn, { runId, episodeId, rendererId = "A", leakyRenderer = false }) {
  const previous = before.substates[SUBSTATE_NAME] || initialSubstate();
  const nextStep = Number(before.step_id) + 1;
  const seedContext = {
    seed: deterministicInt(`${runId}:${episodeId}:${turn.turn_id}:draw`),
    draw_index: nextStep,
  };
  const semanticHistory = Array.isArray(previous.semantic_history)
    ? [...previous.semantic_history]
    : [];
  semanticHistory.push({
    turn_id: turn.turn_id,
    semantic_intent: turn.semantic_intent,
    locked_semantic_output: turn.locked_semantic_output,
  });
  const cumulativeObservationHash = canonicalSha256({
    previous: previous.cumulative_observation_hash || "",
    turn_id: turn.turn_id,
    semantic_intent: turn.semantic_intent,
    locked_semantic_output: turn.locked_semantic_output,
  });
  const substate = {
    schema_version: "joi_loop_state_v0",
    fixture_family: previous.fixture_family || "existing_joi_real_loop_trace_runner_fixture_v0",
    turn_count: nextStep,
    semantic_history: semanticHistory,
    last_semantic_intent: turn.semantic_intent,
    last_locked_semantic_output: turn.locked_semantic_output,
    cumulative_observation_hash: cumulativeObservationHash,
    decimal_format: DECIMAL_STRING_FORMAT,
    parity_decimal_signal: turn.numeric_signal,
  };
  if (leakyRenderer) {
    substate.renderer_identity_leak_positive_control = String(rendererId);
  }
  return {
    nextEnvelope: createKernelStateEnvelope({
      taskId: before.task_id,
      runId: before.run_id,
      episodeId: before.episode_id,
      stepId: nextStep,
      substate,
      seedRegistry: {
        ...before.seed_registry,
        [`${episodeId}_step_${nextStep}`]: seedContext,
      },
      ablations: before.ablations,
    }),
    seedContext,
  };
}

function buildTraceProjection({ runId, episodeId, turn, rendererId, stateBefore, stateAfter, seedContext }) {
  const block = buildKernelAdoptionBlock({
    stateBefore,
    stateAfter,
    stepId: stateAfter.step_id,
    seedContext,
  });
  const botText = rendererSurface(turn, rendererId);
  return {
    schema_version: "ego_desktop.joi_real_loop_r3_adoption_trace_row.v0",
    claim_ceiling: CLAIM_CEILING,
    run_id: runId,
    episode_id: episodeId,
    condition_id: "CURRENT_SHIM",
    turn_id: turn.turn_id,
    tick_id: turn.tick_id,
    chat_turn: {
      status: "ok",
      expression_name: turn.expression_name,
      bot_text_hash: canonicalSha256({ text: botText }),
      pspc_scenario_id: turn.pspc_scenario_id,
    },
    renderer_surface_text: botText,
    semantic_output_lock: turn.locked_semantic_output,
    kernel_adoption_v0: block,
  };
}

function simulateEpisode({
  runId = "r3_adoption_run",
  episodeId = "episode_001",
  rendererId = "A",
  leakyRenderer = false,
  initialState,
  inputLog = FIXTURE_TURNS,
} = {}) {
  let state = initialState ? cloneJson(initialState) : initialEnvelope({ runId, episodeId, rendererId });
  const traceRows = [];
  const checkpoints = [cloneJson(state)];
  for (const rawTurn of inputLog) {
    const turn = cloneJson(rawTurn);
    const before = cloneJson(state);
    const { nextEnvelope, seedContext } = transitionEnvelope(before, turn, {
      runId,
      episodeId,
      rendererId,
      leakyRenderer,
    });
    state = nextEnvelope;
    traceRows.push(buildTraceProjection({
      runId,
      episodeId,
      turn,
      rendererId,
      stateBefore: before,
      stateAfter: state,
      seedContext,
    }));
    checkpoints.push(cloneJson(state));
  }
  return {
    episode_id: episodeId,
    renderer_id: rendererId,
    initial_envelope: checkpoints[0],
    final_envelope: cloneJson(state),
    input_log: cloneJson(inputLog),
    checkpoints,
    trace_rows: traceRows,
  };
}

function rowReplayProjection(row) {
  return {
    turn_id: row.turn_id,
    tick_id: row.tick_id,
    condition_id: row.condition_id,
    chat_turn: row.chat_turn,
    semantic_output_lock: row.semantic_output_lock,
    kernel_adoption_v0: row.kernel_adoption_v0,
  };
}

function projectionList(rows) {
  return rows.map(rowReplayProjection);
}

function replayKernelAdoptionEpisode(payload = {}) {
  const replay = simulateEpisode({
    runId: payload.runId,
    episodeId: payload.episodeId,
    rendererId: payload.rendererId || "A",
    leakyRenderer: Boolean(payload.leakyRenderer),
    initialState: payload.initialEnvelope,
    inputLog: payload.inputLog || FIXTURE_TURNS,
  });
  return {
    trace_rows: replay.trace_rows,
    projection: projectionList(replay.trace_rows),
    final_envelope: replay.final_envelope,
  };
}

function runReplayInFreshProcess(payload) {
  const script = [
    `const adapter = require(${JSON.stringify(__filename)});`,
    "const payload = JSON.parse(process.argv[1]);",
    "process.stdout.write(JSON.stringify(adapter.replayKernelAdoptionEpisode(payload)));",
  ].join("\n");
  const child = spawnSync(process.execPath, ["-e", script, JSON.stringify(payload)], {
    encoding: "utf8",
  });
  if (child.status !== 0) {
    throw new Error(`fresh process replay failed: ${child.stderr}`);
  }
  return JSON.parse(child.stdout);
}

function countProjectionMismatches(expected, observed) {
  const left = canonicalJsonStringify(expected);
  const right = canonicalJsonStringify(observed);
  return left === right ? 0 : 1;
}

function runReplayChecks(episodes) {
  let freshProcessMismatchCount = 0;
  let resumeMismatchCount = 0;
  const perEpisode = [];
  for (const episode of episodes) {
    const expectedProjection = projectionList(episode.trace_rows);
    for (let replayIndex = 0; replayIndex < 2; replayIndex += 1) {
      const observed = runReplayInFreshProcess({
        runId: episode.trace_rows[0].run_id,
        episodeId: episode.episode_id,
        rendererId: episode.renderer_id,
        initialEnvelope: episode.initial_envelope,
        inputLog: episode.input_log,
      });
      freshProcessMismatchCount += countProjectionMismatches(expectedProjection, observed.projection);
    }
    const resumeIndex = Math.floor(episode.input_log.length / 2);
    const resumeObserved = runReplayInFreshProcess({
      runId: episode.trace_rows[0].run_id,
      episodeId: episode.episode_id,
      rendererId: episode.renderer_id,
      initialEnvelope: episode.checkpoints[resumeIndex],
      inputLog: episode.input_log.slice(resumeIndex),
    });
    const expectedResumeProjection = projectionList(episode.trace_rows.slice(resumeIndex));
    const resumeMismatch = countProjectionMismatches(expectedResumeProjection, resumeObserved.projection);
    resumeMismatchCount += resumeMismatch;
    perEpisode.push({
      episode_id: episode.episode_id,
      fresh_process_runs: 2,
      fresh_process_mismatches: 0,
      resume_index: resumeIndex,
      resume_mismatch_count: resumeMismatch,
    });
  }
  return {
    schema_version: "ego.r3_adoption.replay_report.v0",
    producer_function: "runReplayChecks",
    fresh_process_runs: 2,
    fresh_process_mismatch_count: freshProcessMismatchCount,
    resume_mismatch_count: resumeMismatchCount,
    mismatch_total: freshProcessMismatchCount + resumeMismatchCount,
    per_episode: perEpisode,
    aggregation_rule: "sum mismatches across two fresh-process replays and one resume replay per episode",
  };
}

function kernelFieldProjection(episode) {
  return episode.trace_rows.map((row) => ({
    turn_id: row.turn_id,
    kernel_adoption_v0: row.kernel_adoption_v0,
  }));
}

function countKernelFieldLeaks(left, right) {
  const a = kernelFieldProjection(left);
  const b = kernelFieldProjection(right);
  let leaks = 0;
  for (let index = 0; index < Math.max(a.length, b.length); index += 1) {
    if (canonicalJsonStringify(a[index] || null) !== canonicalJsonStringify(b[index] || null)) {
      leaks += 1;
    }
  }
  return leaks;
}

function runSwapInvarianceCheck({ runId = "r3_adoption_swap" } = {}) {
  const episodeA = simulateEpisode({ runId, episodeId: "swap_episode", rendererId: "A" });
  const episodeB = simulateEpisode({ runId, episodeId: "swap_episode", rendererId: "B" });
  const episodeC = simulateEpisode({
    runId,
    episodeId: "swap_episode",
    rendererId: "C",
    leakyRenderer: true,
  });
  const abLeakCount = countKernelFieldLeaks(episodeA, episodeB);
  const cLeakCount = countKernelFieldLeaks(episodeA, episodeC);
  return {
    schema_version: "ego.r3_adoption.swap_report.v0",
    producer_function: "runSwapInvarianceCheck",
    run_id: runId,
    ab_kernel_fields_identical: abLeakCount === 0,
    ab_kernel_field_leak_count: abLeakCount,
    renderer_surface_texts_differ: episodeA.trace_rows[0].renderer_surface_text !== episodeB.trace_rows[0].renderer_surface_text,
    positive_control_c_detected: cLeakCount > 0,
    leaky_renderer_c_leak_count: cLeakCount,
    aggregation_rule: "count per-turn kernel_adoption_v0 projection mismatches",
  };
}

function runKernelAdoptionFixture({ runId = "r3_adoption_fixture", episodeCount = 2, rendererId = "A" } = {}) {
  const episodes = [];
  for (let index = 0; index < episodeCount; index += 1) {
    episodes.push(simulateEpisode({
      runId,
      episodeId: `episode_${String(index + 1).padStart(3, "0")}`,
      rendererId,
    }));
  }
  return {
    schema_version: "ego.r3_adoption.fixture_result.v0",
    producer_function: "runKernelAdoptionFixture",
    run_id: runId,
    episode_count: episodeCount,
    input_artifacts: ["CONFIG_FROZEN", "PARITY_VECTORS", "FIXTURE_TURNS"],
    seed_context: episodes.map((episode) => ({
      episode_id: episode.episode_id,
      seed_registry: episode.final_envelope.seed_registry,
    })),
    episodes,
    replay_report: runReplayChecks(episodes),
    swap_report: runSwapInvarianceCheck({ runId: `${runId}_swap` }),
    aggregation_rule: "all episodes must replay with zero projection mismatch",
    code_path_hash: sha256Text(`${__filename}:${canonicalSha256(CONFIG_FROZEN)}`),
  };
}

module.exports = {
  CLAIM_CEILING,
  CONFIG_FROZEN,
  DECIMAL_STRING_FORMAT,
  FIXTURE_TURNS,
  KERNEL_STATE_SCHEMA_VERSION,
  PARITY_VECTORS,
  PARITY_VECTOR_SHA256,
  SUBSTATE_NAME,
  TASK_ID,
  TRACE_BLOCK_NAME,
  buildKernelAdoptionBlock,
  canonicalJsonStringify,
  canonicalSha256,
  createKernelStateEnvelope,
  replayKernelAdoptionEpisode,
  runKernelAdoptionFixture,
  runReplayChecks,
  runSwapInvarianceCheck,
  sanitizeForKernelState,
  simulateEpisode,
  stablePrettyJson,
};
