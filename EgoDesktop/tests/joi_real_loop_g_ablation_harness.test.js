const assert = require("node:assert/strict");
const test = require("node:test");

const {
  ALLOWED_VERDICTS,
  CLAIM_CEILING,
  REQUIRED_CONDITIONS,
  SAME_ACCESS_REPRODUCER_FAMILIES,
  buildBaselineEvaluationPlan,
  buildJoiRealLoopGAblationContract,
  buildJoiRealLoopTraceRow,
  decideJoiRealLoopVerdict,
  validateNoAuthorityFields,
} = require("../src/joiRealLoopGAblationHarness");

function validEnv(overrides = {}) {
  return {
    JOI_REAL_LOOP_G_ABLATION: "1",
    JOI_REAL_LOOP_CONDITION: "CREATURE_ON",
    JOI_REAL_LOOP_TRACE_DIR: "artifacts/egodesktop_joi_real_loop/run_001",
    JOI_REAL_LOOP_LLM_MODE: "replay_locked",
    JOI_REAL_LOOP_PROMPT_PACK: "prompt-pack-sha",
    JOI_REAL_LOOP_SPLIT: "heldout",
    ...overrides,
  };
}

function validTracePayload(overrides = {}) {
  return {
    runId: "run-001",
    conditionId: "CREATURE_ON",
    turnId: "turn-001",
    tickId: "tick-001",
    seed: "seed-001",
    sourceHashes: {
      ego_head: "ego-head",
      joi_demo_head: "joi-head",
      adapter_hash: "adapter-hash",
    },
    promptId: "prompt-001",
    promptPackHash: "prompt-pack-sha",
    splitId: "heldout",
    llmReplayId: "llm-replay-001",
    chatTurn: {
      status: "ok",
      expression_name: "记笔记",
      bot_text: "先记录一个可回放的输出。",
      pspc_scenario_id: "scenario-001",
    },
    creatureState: {
      schema_version: "creature_state.v0_2",
      surprise: 0.2,
      viability: 0.8,
    },
    adapterOutput: {
      source: "read_only_creature_state_adapter",
      live2d_params: [{ id: "ParamAngleX", value: 2.5 }],
    },
    publicInputs: {
      user_turn_id: "prompt-001",
      visible_history_hash: "history-sha",
      llm_replay_id: "llm-replay-001",
    },
    sameAccessReproducerId: "ema_history",
    baselineSplit: "heldout",
    live2dParameterSamples: [{ id: "ParamAngleX", value: 2.5, t: 1 }],
    rendererIdleParams: ["ParamMouthOpenY", "ParamJawOpen"],
    outputEvent: { order: 1, timestamp_ms: 100 },
    replayInputs: {
      serialized_state_hash: "state-sha",
      observation_hash: "observation-sha",
    },
    ...overrides,
  };
}

test("default contract is disabled and has no runtime authority", () => {
  const contract = buildJoiRealLoopGAblationContract({});

  assert.equal(contract.enabled, false);
  assert.equal(contract.status, "disabled_default_off");
  assert.equal(contract.runtime_authority, "none");
  assert.equal(contract.mainline_connected, false);
  assert.equal(contract.adapter_registered, false);
  assert.equal(contract.default_behavior_unchanged_when_disabled, true);
  assert.equal(contract.claim_ceiling, CLAIM_CEILING);
});

test("enabled contract blocks missing flags and unlocked LLM", () => {
  const missing = buildJoiRealLoopGAblationContract({
    JOI_REAL_LOOP_G_ABLATION: "1",
    JOI_REAL_LOOP_CONDITION: "CREATURE_ON",
  });

  assert.equal(missing.status, "blocked_invalid_contract");
  assert.ok(missing.missing_required_flags.includes("JOI_REAL_LOOP_TRACE_DIR"));
  assert.ok(missing.blockers.includes("missing_required_experiment_flags"));

  const unlocked = buildJoiRealLoopGAblationContract(validEnv({
    JOI_REAL_LOOP_LLM_MODE: "live",
  }));
  assert.equal(unlocked.status, "blocked_invalid_contract");
  assert.ok(unlocked.blockers.includes("llm_mode_not_replay_locked"));
});

test("enabled contract is ready only under explicit non-default flags", () => {
  const contract = buildJoiRealLoopGAblationContract(validEnv());

  assert.equal(contract.enabled, true);
  assert.equal(contract.status, "ready_for_explicit_harness_run");
  assert.equal(contract.condition, "CREATURE_ON");
  assert.equal(contract.llm_mode, "replay_locked");
  assert.equal(contract.runtime_authority, "none");
  assert.equal(contract.mainline_connected, false);
  assert.equal(contract.adapter_registered, false);
  assert.ok(contract.required_conditions.includes("OFF_STATIC_REPLAY_SAME_PACK"));
  assert.ok(contract.required_conditions.includes("OFF_STATIC_REPLAY_HELDOUT"));
  assert.ok(contract.required_conditions.includes("SAME_ACCESS_REPRODUCER_BATTERY"));
});

test("contract rejects recursive runtime authority fields", () => {
  assert.throws(
    () => validateNoAuthorityFields({ nested: { tool_call: { name: "run" } } }, "candidate"),
    /candidate contains runtime authority field/,
  );
  assert.throws(
    () => validateNoAuthorityFields({ safe: true, memory_write: false }, "candidate"),
    /candidate contains runtime authority field/,
  );
  assert.deepEqual(validateNoAuthorityFields({ safe: { value: 1 } }, "candidate"), { safe: { value: 1 } });
});

test("trace row records replay fields and renderer idle exclusion", () => {
  const row = buildJoiRealLoopTraceRow(validTracePayload());

  assert.equal(row.schema_version, "ego_desktop.joi_real_loop_trace_row.v0");
  assert.equal(row.condition_id, "CREATURE_ON");
  assert.equal(row.split_id, "heldout");
  assert.equal(row.llm_replay_id, "llm-replay-001");
  assert.equal(row.chat_turn.expression_name, "记笔记");
  assert.equal(row.public_inputs.user_turn_id, "prompt-001");
  assert.equal(row.same_access_reproducer_id, "ema_history");
  assert.equal(row.renderer_idle_excluded, true);
  assert.deepEqual(row.renderer_idle_params_excluded_from_d, ["ParamMouthOpenY", "ParamJawOpen"]);
  assert.match(row.creature_state_hash, /^[a-f0-9]{64}$/);
  assert.match(row.adapter_output_hash, /^[a-f0-9]{64}$/);
  assert.match(row.public_inputs_hash, /^[a-f0-9]{64}$/);
  assert.match(row.replay_inputs_hash, /^[a-f0-9]{64}$/);
  assert.match(row.row_hash, /^[a-f0-9]{64}$/);
});

test("trace row rejects unknown conditions and authority-bearing adapter payloads", () => {
  assert.throws(
    () => buildJoiRealLoopTraceRow(validTracePayload({ conditionId: "ROUTE_B_PASS" })),
    /conditionId is unknown/,
  );
  assert.throws(
    () => buildJoiRealLoopTraceRow(validTracePayload({
      adapterOutput: { action: "drive_live2d_directly" },
    })),
    /adapterOutput contains runtime authority field/,
  );
});

test("baseline plan preserves decisive floors and strongest same-access battery", () => {
  const plan = buildBaselineEvaluationPlan();

  assert.equal(
    plan.static_replay_policies.OFF_STATIC_REPLAY_SAME_PACK.can_support_positive_verdict,
    false,
  );
  assert.equal(
    plan.static_replay_policies.OFF_STATIC_REPLAY_SAME_PACK.role,
    "diagnostic_closure_floor",
  );
  assert.equal(
    plan.static_replay_policies.OFF_STATIC_REPLAY_HELDOUT.role,
    "decisive_input_blind_replay_floor",
  );
  assert.equal(
    plan.same_access_reproducer_battery.selection_rule,
    "report_best_or_closest_reproducer_on_heldout_split",
  );
  for (const family of ["ema_history", "hysteresis_history", "logistic_short_context", "fixed_shim_template"]) {
    assert.ok(SAME_ACCESS_REPRODUCER_FAMILIES.includes(family));
    assert.ok(plan.same_access_reproducer_battery.families.includes(family));
  }
});

test("verdict helper blocks positive attribution under closure and invalidity signals", () => {
  assert.equal(ALLOWED_VERDICTS.includes("real_loop_causal_path_attribution_pass"), true);
  assert.equal(decideJoiRealLoopVerdict({ missingRealLoopEntrypoint: true }), "blocked_missing_real_loop_entrypoint");
  assert.equal(decideJoiRealLoopVerdict({ leakageOrFutureInfo: true }), "invalid_leakage_or_future_info");
  assert.equal(decideJoiRealLoopVerdict({ privilegedStateGap: true }), "invalid_baseline_parity_or_privileged_state_leak");
  assert.equal(
    decideJoiRealLoopVerdict({ samePackReplayUsedAsPositiveEvidence: true }),
    "invalid_metric_uses_same_pack_static_replay_as_positive_evidence",
  );
  assert.equal(decideJoiRealLoopVerdict({ rendererIdleDrivesMetric: true }), "invalid_renderer_idle_drives_metric");
  assert.equal(decideJoiRealLoopVerdict({ llmUnlockedConfoundsMetric: true }), "invalid_llm_unlocked_confounds_metric");
  assert.equal(decideJoiRealLoopVerdict({ creatureEffectPresent: false }), "real_loop_g_ablation_fail_no_creature_effect");
  assert.equal(
    decideJoiRealLoopVerdict({ creatureEffectPresent: true, heldoutStaticReplayEquivalent: true }),
    "real_loop_g_ablation_baseline_saturated_stop",
  );
  assert.equal(
    decideJoiRealLoopVerdict({ creatureEffectPresent: true, sameAccessBestEquivalent: true }),
    "real_loop_g_ablation_baseline_saturated_stop",
  );
  assert.equal(
    decideJoiRealLoopVerdict({ creatureEffectPresent: true, partialCausalPathOnly: true }),
    "real_loop_g_ablation_partial_causal_path_only",
  );
  assert.equal(
    decideJoiRealLoopVerdict({ creatureEffectPresent: true }),
    "real_loop_causal_path_attribution_pass",
  );
});

test("required condition list preserves joi-demo real-loop contract surface", () => {
  for (const condition of [
    "CREATURE_ON",
    "CREATURE_FROZEN",
    "OFF_STATE_FLAT",
    "OFF_REACTIVE_ONLY",
    "OFF_STATIC_REPLAY_SAME_PACK",
    "OFF_STATIC_REPLAY_HELDOUT",
    "OFF_SHUFFLED_STATE",
    "CURRENT_SHIM",
    "SAME_ACCESS_REPRODUCER_BATTERY",
    "LLM_REPLAY_LOCKED",
  ]) {
    assert.ok(REQUIRED_CONDITIONS.includes(condition));
  }
});
