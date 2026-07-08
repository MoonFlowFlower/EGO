const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const {
  PET_MODE_FLAG,
  buildPetModeConfig,
  isPetModeRequested,
  runHeadlessPetSession,
  validatePetTraceRoundTrip,
} = require("../src/petMode");
const { buildLive2dObserverFrame } = require("../src/petLive2dObserverMap");

const repoRoot = path.resolve(__dirname, "..", "..");
const kernelTraceFields = [
  "task_id",
  "run_id",
  "episode_id",
  "step_id",
  "state_before_hash",
  "observation",
  "prediction",
  "action",
  "feedback",
  "prediction_error",
  "state_after_hash",
  "component_attribution",
  "seed_context",
];

test("pet mode is default-off and only enabled by the explicit developer flag", () => {
  assert.equal(PET_MODE_FLAG, "ego-pet-mode");
  assert.equal(isPetModeRequested({}), false);
  assert.equal(isPetModeRequested({ smoke: true }), false);
  assert.equal(isPetModeRequested({ [PET_MODE_FLAG]: true }), true);
  assert.equal(isPetModeRequested({ [PET_MODE_FLAG]: "1" }), true);
  assert.equal(isPetModeRequested({ [PET_MODE_FLAG]: "false" }), false);

  const disabled = buildPetModeConfig({ enabled: false });
  assert.equal(disabled.enabled, false);
  assert.equal(disabled.kernel_process_started, false);
  assert.equal(disabled.developer_flag, "--ego-pet-mode");
  assert.equal(disabled.claim_ceiling, "pet_p1_default_off_engineering_wiring_only");
});

test("main and preload expose exactly one additive pet hook each", () => {
  const main = fs.readFileSync(path.join(repoRoot, "EgoDesktop", "src", "main.js"), "utf8");
  const preload = fs.readFileSync(path.join(repoRoot, "EgoDesktop", "src", "preload.js"), "utf8");

  assert.equal((main.match(/require\("\.\/petMode"\)/g) || []).length, 1);
  assert.match(main, /args\["ego-pet-mode"\]/);
  assert.match(main, /viewer\/\$\{config\.petModeViewerPage \|\| "index\.html"\}/);

  assert.equal((preload.match(/petMode:/g) || []).length, 1);
  assert.match(preload, /ego-desktop:pet-get-snapshot/);
  assert.match(preload, /ego-desktop:pet-input/);
  assert.match(preload, /ego-desktop:pet-tick/);
});

test("kernel bridge is the tick authority, records tick-quantized inputs, and replays without viewer", async () => {
  const session = await runHeadlessPetSession({
    repoRoot,
    seed: 3101,
    runId: "egodesktop_pet_world_integration_001a_p1_test",
    episodeId: "p1_trace_roundtrip",
    ticks: 12,
    inputs: [
      { tick_index: 0.2, event_type: "feed", payload: { portion: "small" } },
      { tick_index: 2.7, event_type: "pet", payload: { intensity: "gentle" } },
      { tick_index: 5, event_type: "ablation_toggle", payload: { ablation_enabled: true } },
      { tick_index: 8, event_type: "ablation_toggle", payload: { ablation_enabled: false } },
    ],
  });

  assert.equal(session.trace_rows.length, 12);
  assert.equal(session.frames.length, 12);
  assert.deepEqual(Object.keys(session.trace_rows[0]), kernelTraceFields);
  assert.equal(session.frames.every((frame) => frame.kernel_adoption_v0), true);
  assert.equal(session.frames.every((frame) => frame.source === "python_kernel_process"), true);

  const admittedEvents = session.trace_rows
    .map((row) => row.component_attribution.input_event_decision)
    .filter(Boolean);
  assert.deepEqual(admittedEvents.map((event) => event.event_type), [
    "feed",
    "pet",
    "ablation_toggle",
    "ablation_toggle",
  ]);
  assert.deepEqual(admittedEvents.map((event) => event.tick_index), [0, 2, 5, 8]);

  const roundTrip = await validatePetTraceRoundTrip({ repoRoot, session });
  assert.equal(roundTrip.status, "pass");
  assert.equal(roundTrip.viewer_required, false);
  assert.equal(roundTrip.mismatch_count, 0);
});

test("Live2D pet observer map is pure renderer projection, not evidence", () => {
  const sourceState = {
    schema_version: "ego_desktop.pet_state_frame.v0",
    state_hash: "abc",
    pet_world_v0: {
      needs: { energy: 0.75, comfort: 0.25 },
      tick_index: 7,
    },
    user_facing_bubble: {
      text: "收到这个互动；可见气泡由静态 gate 控制。",
      template_id: "static_care_ack",
    },
  };
  const before = JSON.stringify(sourceState);
  const projected = buildLive2dObserverFrame(sourceState);

  assert.equal(JSON.stringify(sourceState), before);
  assert.equal(projected.claim_ceiling, "renderer_observer_projection_only_not_evidence");
  assert.equal(projected.input_authority, false);
  assert.equal(projected.evidence_authority, false);
  assert.equal(projected.live2d_params.ParamEnergy, 0.75);
  assert.equal(projected.live2d_params.ParamComfort, 0.25);
  assert.equal(projected.bubble.text, "收到这个互动；可见气泡由静态 gate 控制。");
});
