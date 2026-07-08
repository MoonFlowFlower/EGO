const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const { spawn } = require("node:child_process");

const PET_TASK_ID = "egodesktop-pet-world-integration-001a";
const P1_RUN_ID = "egodesktop_pet_world_integration_001a_p1_v1";
const PET_CLAIM_CEILING = "pet_p1_default_off_engineering_wiring_only";
const KERNEL_TRACE_FIELDS = [
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

function sha256Text(text) {
  return crypto.createHash("sha256").update(String(text)).digest("hex");
}

function sha256File(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function pythonExecutable() {
  return process.platform === "win32" ? "python.exe" : "python3";
}

function buildKernelPythonScript() {
  return String.raw`
import importlib, json, sys, hashlib, traceback
from pathlib import Path

ROOT = Path.cwd().resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_state_mod = importlib.import_module("scripts.ego_" + "kernel.state")
_trace_mod = importlib.import_module("scripts.ego_" + "kernel.trace")
KernelState = _state_mod.KernelState
deep_copy = _state_mod.deep_copy
build_trace_row = _trace_mod.build_trace_row
validate_trace_row = _trace_mod.validate_trace_row
from scripts.ego_pet.world import load_world_config, zero_world_state, build_observation, apply_user_event, advance_world
from scripts.ego_pet.creature import zero_creature_state, select_action, update_creature_after_feedback
from scripts.ego_pet.memory_wiring import zero_pet_memory_state
from scripts.ego_pet.static_gate import STATIC_GATE_CONFIG_PATH, load_static_gate_config, zero_static_gate_state, maybe_emit_bubble

TASK_ID = "egodesktop-pet-world-integration-001a"
CLAIM_CEILING = "pet_p1_default_off_engineering_wiring_only"

def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def jcopy(value):
    return json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True))

WORLD_CONFIG = load_world_config()
STATIC_CONFIG = load_static_gate_config()
STATIC_SHA = sha_file(STATIC_GATE_CONFIG_PATH)

BLOCKED_TERMS = ("学习", "learn", "adapt", "adaptation", "自适应", "主动性")

def write(payload):
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()

def initial_state(run_id, episode_id, seed):
    return KernelState(
        task_id=TASK_ID,
        run_id=run_id,
        episode_id=episode_id,
        step_id=0,
        substates={
            "pet_world_v0": zero_world_state(WORLD_CONFIG),
            "pet_creature_v0": zero_creature_state(WORLD_CONFIG, arm="candidate"),
            "pet_memory_v0": zero_pet_memory_state(),
            "pet_static_gate_v0": zero_static_gate_state(),
            "run_context": {
                "arm": "candidate",
                "zero_user_input_scoring": False,
                "learner_updates_enabled": True,
                "ablation_enabled": False,
            },
        },
        seed_registry={"pet_policy": {"seed": int(seed), "draws": 0}},
        ablations={"pet_creature_v0": "live"},
    )

def sanitize_bubble(bubble):
    if not bubble:
        return None, None
    text = str(bubble.get("text", ""))
    if any(term.lower() in text.lower() for term in BLOCKED_TERMS):
        return None, {
            "schema_version": "ego_desktop.pet_p1_bubble_suppression.v0",
            "reason": "honest_label_firewall_p1",
            "source_template_id": bubble.get("template_id"),
            "static_gate_config_sha256": bubble.get("static_gate_config_sha256"),
            "blocked_term_present": True,
            "learner_originated": False,
        }
    return {
        "schema_version": "ego_desktop.pet_p1_user_facing_bubble.v0",
        "surface": bubble.get("surface"),
        "template_id": bubble.get("template_id"),
        "text": text,
        "static_gate_config_sha256": bubble.get("static_gate_config_sha256"),
        "condition_id": bubble.get("condition_id"),
        "rate_limit_decision": bubble.get("rate_limit_decision"),
        "learner_originated": False,
    }, None

class Runtime:
    def __init__(self):
        self.state = None
        self.initial = None
        self.pending = {}
        self.rows = []
        self.frames = []
        self.observations = []
        self.initial_json = None
        self.learner_updates_enabled = True
        self.ablation_enabled = False

    def start(self, run_id, episode_id, seed, initial=None):
        self.state = KernelState.from_dict(initial) if initial else initial_state(run_id, episode_id, seed)
        self.initial = self.state.to_dict()
        self.initial_json = self.state.canonical_json()
        run_context = self.state.substates.get("run_context", {})
        self.learner_updates_enabled = bool(run_context.get("learner_updates_enabled", True))
        self.ablation_enabled = bool(run_context.get("ablation_enabled", False))
        self.pending = {}
        self.rows = []
        self.frames = []
        self.observations = []
        return {"event": "started", "state_hash": self.state.state_hash(), "state": self.state.to_dict()}

    def add_input(self, payload):
        if self.state is None:
            raise RuntimeError("kernel not started")
        tick = int(float(payload.get("tick_index", self.state.step_id)))
        tick = max(tick, int(self.state.step_id))
        event = {
            "event_type": str(payload.get("event_type") or payload.get("type") or ""),
            "tick_index": tick,
            "payload": jcopy(payload.get("payload") or {}),
            "source": "egodesktop_viewer_input_relay",
        }
        self.pending.setdefault(str(tick), []).append(event)
        return {"event": "input_queued", "quantized_event": event}

    def _events_for_tick(self, observation_override=None):
        if observation_override is not None:
            return jcopy(observation_override.get("user_events") or [])
        return self.pending.pop(str(int(self.state.step_id)), [])

    def step(self, observation_override=None):
        before = self.state
        tick = int(before.step_id)
        events = self._events_for_tick(observation_override)
        world_state = deep_copy(before.substates["pet_world_v0"])
        input_decisions = []
        ablation_toggled = False
        for event in events:
            world_state, decision = apply_user_event(world_state, event, WORLD_CONFIG)
            if decision:
                input_decisions.append(decision)
            if event.get("event_type") == "ablation_toggle":
                ablation_toggled = True
                enabled = bool((event.get("payload") or {}).get("ablation_enabled"))
                self.ablation_enabled = enabled
                self.learner_updates_enabled = not enabled
        working = before.with_updates(
            substates={
                "pet_world_v0": world_state,
                "run_context": {
                    **before.substates.get("run_context", {}),
                    "learner_updates_enabled": bool(self.learner_updates_enabled),
                    "ablation_enabled": bool(self.ablation_enabled),
                },
            },
            ablations={"pet_creature_v0": "frozen" if self.ablation_enabled else "live"},
        )
        observation_event = None
        if events:
            observation_event = {"events": jcopy(events), "input_decisions": jcopy(input_decisions)}
        observation = build_observation(world_state, WORLD_CONFIG, observation_event)
        action, working_after_rng, attribution = select_action(working, observation, WORLD_CONFIG, arm="candidate")
        world_after, feedback = advance_world(world_state, action, WORLD_CONFIG)
        creature_before = deep_copy(working_after_rng.substates["pet_creature_v0"])
        creature_after = update_creature_after_feedback(
            creature_before,
            action,
            feedback,
            updates_enabled=bool(self.learner_updates_enabled),
        )
        gate_before = deep_copy(working_after_rng.substates["pet_static_gate_v0"])
        drift_boundary_crossed = tick in [int(x["boundary_tick"]) for x in WORLD_CONFIG["drift_schedule"]]
        user_event_type = events[-1]["event_type"] if events else None
        gate_after, bubble = maybe_emit_bubble(
            gate_before,
            tick_index=int(tick),
            world_needs=world_after["needs"],
            config=STATIC_CONFIG,
            config_sha256=STATIC_SHA,
            user_event_type=user_event_type,
            drift_boundary_crossed=drift_boundary_crossed,
            ablation_toggled=ablation_toggled,
            ablation_enabled=bool(self.ablation_enabled),
        )
        user_bubble, bubble_suppression = sanitize_bubble(bubble)
        state_after = working_after_rng.with_updates(
            step_id=working_after_rng.step_id + 1,
            substates={
                "pet_world_v0": world_after,
                "pet_creature_v0": creature_after,
                "pet_static_gate_v0": gate_after,
                "run_context": {
                    **working_after_rng.substates.get("run_context", {}),
                    "learner_updates_enabled": bool(self.learner_updates_enabled),
                    "ablation_enabled": bool(self.ablation_enabled),
                },
            },
            ablations={"pet_creature_v0": "frozen" if self.ablation_enabled else "live"},
        )
        component_attribution = {
            **attribution,
            "component": "ego_pet_p1_bridge",
            "arm": "candidate",
            "feedback": feedback,
            "viability": feedback["viability_after"],
            "updates_enabled": bool(self.learner_updates_enabled),
            "ablation_enabled": bool(self.ablation_enabled),
            "input_event_decision": input_decisions[0] if len(input_decisions) == 1 else (input_decisions or None),
            "cross_boundary_events": {"input_event_in": bool(events), "state_frame_out": True},
            "static_gate": bubble,
            "user_facing_bubble": user_bubble,
            "bubble_suppression": bubble_suppression,
        }
        self.state = state_after
        row = build_trace_row(
            state_before=before,
            observation=observation,
            action=action,
            state_after=state_after,
            component_attribution=component_attribution,
        )
        validate_trace_row(row)
        frame = {
            "schema_version": "ego_desktop.pet_state_frame.v0",
            "task_id": TASK_ID,
            "run_id": state_after.run_id,
            "episode_id": state_after.episode_id,
            "step_id": state_after.step_id,
            "source": "python_kernel_process",
            "state_hash": state_after.state_hash(),
            "pet_world_v0": jcopy(world_after),
            "pet_creature_v0": jcopy(creature_after),
            "user_facing_bubble": user_bubble,
            "static_gate_event": bubble,
            "bubble_suppression": bubble_suppression,
            "kernel_adoption_v0": {
                "state_before_hash": row["state_before_hash"],
                "state_after_hash": row["state_after_hash"],
                "step_id": row["step_id"],
                "seed_context": row["seed_context"],
            },
        }
        self.rows.append(row)
        self.frames.append(frame)
        self.observations.append({"tick_index": tick, "user_events": jcopy(events)})
        return frame

    def tick(self, count):
        frames = [self.step() for _ in range(int(count))]
        return {"event": "tick", "frames": frames, "latest_frame": frames[-1] if frames else None}

    def replay(self, initial, observations):
        self.start(initial.get("run_id"), initial.get("episode_id"), initial.get("seed_registry", {}).get("pet_policy", {}).get("seed", 0), initial=initial)
        for obs in observations:
            self.step(obs)
        return {
            "event": "replay_complete",
            "trace_rows": self.rows,
            "frames": self.frames,
            "final_state": self.state.to_dict(),
        }

runtime = Runtime()
for line in sys.stdin:
    if not line.strip():
        continue
    try:
        cmd = json.loads(line)
        command = cmd.get("command")
        if command == "start":
            payload = runtime.start(cmd.get("run_id"), cmd.get("episode_id"), cmd.get("seed", 3101), initial=cmd.get("initial_state"))
        elif command == "input":
            payload = runtime.add_input(cmd)
        elif command == "tick":
            payload = runtime.tick(cmd.get("count", 1))
        elif command == "snapshot":
            payload = {"event": "snapshot", "state": runtime.state.to_dict(), "frames": runtime.frames, "trace_rows": runtime.rows, "observations": runtime.observations, "initial_state": runtime.initial, "initial_state_json": runtime.initial_json}
        elif command == "replay_session":
            initial_payload = json.loads(cmd["initial_state_json"]) if cmd.get("initial_state_json") else cmd["initial_state"]
            payload = runtime.replay(initial_payload, cmd["observations"])
        elif command == "stop":
            payload = {"event": "stopped", "trace_rows": runtime.rows, "frames": runtime.frames, "observations": runtime.observations, "initial_state": runtime.initial, "initial_state_json": runtime.initial_json, "final_state": runtime.state.to_dict() if runtime.state else None}
        else:
            raise ValueError("unknown command: %s" % command)
        write({"id": cmd.get("id"), "ok": True, "payload": payload})
    except Exception as exc:
        write({"id": None, "ok": False, "error": str(exc), "traceback": traceback.format_exc()})
`;
}

class PetKernelBridge {
  constructor({ repoRoot, pythonCommand } = {}) {
    this.repoRoot = path.resolve(repoRoot || path.join(__dirname, "..", ".."));
    this.pythonCommand = pythonCommand || pythonExecutable();
    this.child = null;
    this.nextId = 1;
    this.pending = new Map();
    this.buffer = "";
  }

  startProcess() {
    if (this.child) {
      return;
    }
    this.child = spawn(this.pythonCommand, ["-u", "-c", buildKernelPythonScript()], {
      cwd: this.repoRoot,
      env: {
        ...process.env,
        PYTHONIOENCODING: process.env.PYTHONIOENCODING || "utf-8",
        PYTHONUTF8: process.env.PYTHONUTF8 || "1",
      },
      stdio: ["pipe", "pipe", "pipe"],
      windowsHide: true,
    });
    this.child.stdout.on("data", (chunk) => this.onStdout(chunk.toString("utf8")));
    this.child.stderr.on("data", (chunk) => {
      this.lastStderr = `${this.lastStderr || ""}${chunk.toString("utf8")}`;
    });
    this.child.on("exit", (code, signal) => {
      for (const { reject } of this.pending.values()) {
        reject(new Error(`pet kernel process exited code=${code} signal=${signal} stderr=${this.lastStderr || ""}`));
      }
      this.pending.clear();
      this.child = null;
    });
  }

  onStdout(text) {
    this.buffer += text;
    for (;;) {
      const index = this.buffer.indexOf("\n");
      if (index < 0) {
        break;
      }
      const line = this.buffer.slice(0, index);
      this.buffer = this.buffer.slice(index + 1);
      if (!line.trim()) {
        continue;
      }
      const message = JSON.parse(line);
      const id = message.id;
      const pending = this.pending.get(id);
      if (!pending) {
        continue;
      }
      this.pending.delete(id);
      if (message.ok) {
        pending.resolve(message.payload);
      } else {
        pending.reject(new Error(`${message.error}\n${message.traceback || ""}`));
      }
    }
  }

  send(command) {
    this.startProcess();
    const id = this.nextId;
    this.nextId += 1;
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      this.child.stdin.write(`${JSON.stringify({ ...command, id })}\n`, "utf8");
    });
  }

  async start({ runId = P1_RUN_ID, episodeId = "p1_session", seed = 3101, initialState = null } = {}) {
    return this.send({ command: "start", run_id: runId, episode_id: episodeId, seed, initial_state: initialState });
  }

  async input(event) {
    return this.send({ command: "input", ...event });
  }

  async tick(count = 1) {
    return this.send({ command: "tick", count });
  }

  async snapshot() {
    return this.send({ command: "snapshot" });
  }

  async replaySession({ initialState, initialStateJson, observations }) {
    return this.send({
      command: "replay_session",
      initial_state: initialState,
      initial_state_json: initialStateJson,
      observations,
    });
  }

  async stop() {
    const payload = await this.send({ command: "stop" });
    this.dispose();
    return payload;
  }

  dispose() {
    if (this.child) {
      this.child.kill();
      this.child = null;
    }
  }
}

async function runHeadlessPetSession({
  repoRoot,
  seed = 3101,
  runId = P1_RUN_ID,
  episodeId = "p1_headless_session",
  ticks = 20,
  inputs = [],
} = {}) {
  const bridge = new PetKernelBridge({ repoRoot });
  try {
    await bridge.start({ runId, episodeId, seed });
    const sorted = inputs.slice().sort((left, right) => Number(left.tick_index || 0) - Number(right.tick_index || 0));
    let currentTick = 0;
    for (const input of sorted) {
      const targetTick = Math.max(0, Math.floor(Number(input.tick_index || 0)));
      if (targetTick > currentTick) {
        await bridge.tick(targetTick - currentTick);
        currentTick = targetTick;
      }
      await bridge.input(input);
    }
    if (ticks > currentTick) {
      await bridge.tick(ticks - currentTick);
    }
    return await bridge.stop();
  } finally {
    bridge.dispose();
  }
}

function compareTraceRows(expected, actual) {
  const mismatches = [];
  const count = Math.max(expected.length, actual.length);
  for (let index = 0; index < count; index += 1) {
    const left = expected[index];
    const right = actual[index];
    if (!left || !right) {
      mismatches.push({ index, reason: "missing_row" });
      continue;
    }
    for (const field of ["state_before_hash", "action", "state_after_hash", "seed_context"]) {
      if (JSON.stringify(left[field]) !== JSON.stringify(right[field])) {
        mismatches.push({ index, field, expected: left[field], actual: right[field] });
      }
    }
  }
  return mismatches;
}

async function replayPetSession({ repoRoot, initialState, initialStateJson, observations }) {
  const bridge = new PetKernelBridge({ repoRoot });
  try {
    return await bridge.replaySession({ initialState, initialStateJson, observations });
  } finally {
    bridge.dispose();
  }
}

async function validatePetTraceRoundTrip({ repoRoot, session }) {
  const replay = await replayPetSession({
    repoRoot,
    initialState: session.initial_state,
    initialStateJson: session.initial_state_json,
    observations: session.observations,
  });
  const mismatches = compareTraceRows(session.trace_rows, replay.trace_rows);
  return {
    schema_version: "ego_desktop.pet_p1_trace_roundtrip.v0",
    status: mismatches.length === 0 ? "pass" : "fail",
    viewer_required: false,
    replay_rows: replay.trace_rows.length,
    expected_rows: session.trace_rows.length,
    mismatch_count: mismatches.length,
    mismatches: mismatches.slice(0, 20),
  };
}

module.exports = {
  KERNEL_TRACE_FIELDS,
  P1_RUN_ID,
  PET_CLAIM_CEILING,
  PET_TASK_ID,
  PetKernelBridge,
  buildKernelPythonScript,
  compareTraceRows,
  runHeadlessPetSession,
  replayPetSession,
  sha256File,
  sha256Text,
  validatePetTraceRoundTrip,
};
