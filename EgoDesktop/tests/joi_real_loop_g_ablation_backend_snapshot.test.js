const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const { buildJoiRealLoopTraceRow, hashValue } = require("../src/joiRealLoopGAblationHarness");
const {
  buildJoiRealLoopBackendAdapterOutput,
} = require("../src/joiRealLoopGAblationTraceRunner");
const {
  evaluateTraceRows,
  renderEvaluationReport,
  summarizeReplayBlockerDelta,
} = require("../src/joiRealLoopGAblationReplayEvaluator");

const AUTHORITY_FIELD_NAMES = new Set([
  "action",
  "tool_call",
  "command",
  "user_message",
  "memory_write",
  "gate_decision",
  "approval_id",
  "transport",
  "send",
  "schedule",
  "enable",
  "mainline_authority",
  "runtime_registration",
  "proposal_id",
]);

function containsAuthorityField(value) {
  if (!value || typeof value !== "object") {
    return false;
  }
  if (Array.isArray(value)) {
    return value.some((item) => containsAuthorityField(item));
  }
  return Object.entries(value).some(([key, child]) => (
    AUTHORITY_FIELD_NAMES.has(key) || containsAuthorityField(child)
  ));
}

function desktopTurn(overrides = {}) {
  return {
    schema_version: "ego_desktop.chat_turn.v1",
    status: "ok",
    user_text: "snapshot prompt",
    bot_text: "snapshot reply",
    expression_name: "记笔记",
    backend_status: "ok",
    backend_reason: "",
    side_effects_executed: false,
    memory_write: false,
    tool_use: false,
    message_send: false,
    file_write: false,
    network_call: false,
    ...overrides,
  };
}

function backendSnapshot() {
  return {
    schema_version: "ego_desktop.joi_real_loop_backend_trace_snapshot.v0",
    source: "ego_operator_desktop_turn_trace_store",
    state_source: "ego_operator_runtime_trace_store",
    event_id: "evt-001",
    trace_record_hash: "a".repeat(64),
    trace_path_hash: "b".repeat(64),
    state_digest: {
      mode: "attend",
      focus: "desktop_chat",
      drives: { stability: 0.7 },
      revision_counter: 3,
      cycle_count: 4,
    },
    viability_state: { energy: 0.6 },
    subject_context_hash: "c".repeat(64),
    llm_meta_hash: "d".repeat(64),
    llm_replay_contract: "absent",
    side_effect_boundary: {
      side_effects_executed: false,
      memory_written: false,
      tools_used: false,
      messages_sent: false,
      files_written: false,
      network_used: false,
    },
    claim_ceiling: "egodesktop_real_loop_g_ablation_backend_trace_snapshot_contract_only",
  };
}

function rowWithBackendSnapshot() {
  const creatureState = backendSnapshot();
  const adapterOutput = buildJoiRealLoopBackendAdapterOutput({
    desktopTurn: desktopTurn(),
    backend: {
      status: "ok",
      reason: "",
      joi_real_loop_trace_snapshot: creatureState,
      joi_real_loop_llm_trace_id: "trace-not-replay",
    },
  });
  const publicInputs = {
    user_text_hash: hashValue("snapshot prompt"),
    condition: "CURRENT_SHIM",
    prompt_pack: "prompt-pack",
    split: "heldout",
    llm_mode: "replay_locked",
    desktop_session_context_hash: hashValue({}),
    desktop_recovery_context_hash: hashValue({}),
    entrypoint_provenance_hash: "e".repeat(64),
    entrypoint_provenance: {
      schema_version: "ego_desktop.joi_real_loop_entrypoint_provenance.v0",
      status: "ipc_event_observed",
      entrypoint_name: "window.egoDesktop.sendChatTurn",
      ipc_channel: "ego-desktop:chat-turn",
      ipc_handler: "ipcMain.handle",
    },
  };
  return buildJoiRealLoopTraceRow({
    runId: "run-006",
    conditionId: "CURRENT_SHIM",
    turnId: "turn-006",
    tickId: "tick-006",
    seed: "seed-006",
    sourceHashes: { harness_hash: "harness", trace_runner_hash: "trace-runner" },
    promptId: "prompt-006",
    promptPackHash: "prompt-pack",
    splitId: "heldout",
    llmReplayId: "none",
    chatTurn: { status: "ok", expression_name: "记笔记", bot_text: "snapshot reply" },
    creatureState,
    adapterOutput,
    publicInputs,
    replayInputs: {
      serialized_state_hash: hashValue(creatureState),
      observation_hash: hashValue(publicInputs),
      replay_policy: "trace_runner_v0_collect_only",
    },
    outputEvent: { order: 1, timestamp_ms: 1 },
  });
}

function placeholderPositiveControlRow() {
  const creatureState = {
    schema_version: "ego_desktop.joi_trace_runner.placeholder_state.v0",
    state_source: "not_connected_in_trace_runner_v0",
    condition: "CURRENT_SHIM",
  };
  const adapterOutput = {
    source: "joi_real_loop_trace_runner_v0",
    adapter_status: "not_connected_trace_runner_v0",
    output_authority: "none",
  };
  const publicInputs = {
    user_text_hash: hashValue("snapshot prompt"),
    condition: "CURRENT_SHIM",
    prompt_pack: "prompt-pack",
    split: "heldout",
    llm_mode: "replay_locked",
  };
  return buildJoiRealLoopTraceRow({
    runId: "run-placeholder-control",
    conditionId: "CURRENT_SHIM",
    turnId: "turn-placeholder-control",
    tickId: "tick-placeholder-control",
    seed: "seed-placeholder-control",
    sourceHashes: { harness_hash: "harness", trace_runner_hash: "trace-runner" },
    promptId: "prompt-placeholder-control",
    promptPackHash: "prompt-pack",
    splitId: "heldout",
    llmReplayId: "none",
    chatTurn: { status: "ok", expression_name: "记笔记", bot_text: "snapshot reply" },
    creatureState,
    adapterOutput,
    publicInputs,
    replayInputs: {
      serialized_state_hash: hashValue(creatureState),
      observation_hash: hashValue(publicInputs),
      replay_policy: "trace_runner_v0_collect_only",
    },
    outputEvent: { order: 1, timestamp_ms: 1 },
  });
}

test("backend adapter output is source-limited and carries no runtime authority", () => {
  const adapterOutput = buildJoiRealLoopBackendAdapterOutput({
    desktopTurn: desktopTurn(),
    backend: {
      status: "ok",
      reason: "",
      joi_real_loop_trace_snapshot: backendSnapshot(),
      joi_real_loop_llm_trace_id: "trace-not-replay",
    },
  });

  assert.equal(adapterOutput.schema_version, "ego_desktop.joi_real_loop_backend_adapter_output.v0");
  assert.equal(adapterOutput.adapter_status, "connected_real_backend_trace_snapshot");
  assert.equal(adapterOutput.output_authority, "none");
  assert.equal(adapterOutput.expression_name, "记笔记");
  assert.equal(adapterOutput.backend_trace_record_hash, "a".repeat(64));
  assert.equal(adapterOutput.llm_trace_id, "trace-not-replay");
  assert.equal(containsAuthorityField(adapterOutput), false);
});

test("evaluator removes placeholder blockers but still blocks collect-only non-replay rows", () => {
  const report = evaluateTraceRows([rowWithBackendSnapshot()], { runId: "eval-006" });

  assert.equal(report.status, "blocked_unreplayable_runtime_trace");
  assert.equal(report.row_results[0].hash_integrity_status, "pass");
  assert.equal(report.leakage_scan_status, "pass");
  assert.equal(report.leakage_positive_control_status, "pass");
  assert.equal(report.blockers.includes("placeholder_creature_state"), false);
  assert.equal(report.blockers.includes("placeholder_adapter_output"), false);
  assert.ok(report.blockers.includes("collect_only_replay_policy"));
  assert.ok(report.blockers.includes("missing_llm_replay_id"));

  const markdown = renderEvaluationReport(report);
  assert.doesNotMatch(markdown, /placeholder trace-runner state remains blocked/);
  assert.match(markdown, /replay blockers prevent verdicts/);
});

test("blocker delta gate uses placeholder positive control, not report wording", () => {
  const beforeReport = evaluateTraceRows([placeholderPositiveControlRow()], { runId: "eval-placeholder-control" });
  const afterReport = evaluateTraceRows([rowWithBackendSnapshot()], { runId: "eval-006" });

  const delta = summarizeReplayBlockerDelta({
    beforeReport,
    afterReport,
    beforeLabel: "placeholder_positive_control",
    afterLabel: "006_backend_snapshot",
  });

  assert.equal(delta.status, "placeholder_blockers_removed_replay_blockers_remain");
  assert.equal(delta.placeholder_positive_control_status, "pass");
  assert.equal(delta.placeholder_removed_status, "pass");
  assert.equal(delta.replay_blockers_preserved_status, "pass");
  assert.deepEqual(delta.removed_blockers, ["placeholder_adapter_output", "placeholder_creature_state"]);
  assert.deepEqual(delta.after_blockers, ["collect_only_replay_policy", "missing_llm_replay_id"]);
  assert.equal(delta.verdict_authorized, false);
});

test("blocker delta gate fails if placeholder positive control does not fire", () => {
  const beforeReport = evaluateTraceRows([rowWithBackendSnapshot()], { runId: "eval-bad-control" });
  const afterReport = evaluateTraceRows([rowWithBackendSnapshot()], { runId: "eval-006" });

  const delta = summarizeReplayBlockerDelta({
    beforeReport,
    afterReport,
    beforeLabel: "bad_placeholder_control",
    afterLabel: "006_backend_snapshot",
  });

  assert.equal(delta.status, "invalid_placeholder_positive_control_not_blocked");
  assert.equal(delta.placeholder_positive_control_status, "fail");
  assert.equal(delta.verdict_authorized, false);
});

test("main process passes backend snapshot at the existing chat-turn trace seam", () => {
  const mainSource = fs.readFileSync(path.join(__dirname, "..", "src", "main.js"), "utf8");

  assert.match(mainSource, /buildJoiRealLoopBackendAdapterOutput/);
  assert.match(mainSource, /creatureState:\s*backend\.joi_real_loop_trace_snapshot/);
  assert.match(mainSource, /adapterOutput:\s*buildJoiRealLoopBackendAdapterOutput\(/);
  assert.match(mainSource, /entrypointProvenance,/);
  assert.doesNotMatch(mainSource, /llmReplayId:\s*backend\.joi_real_loop_llm_trace_id/);
});
