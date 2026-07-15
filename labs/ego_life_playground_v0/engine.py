"""One deterministic V0-descendant reducer for the V1 continuity playground.

The implementation deliberately exposes its cheap explanation: a hard-coded
toy outcome table, deficit scoring, a tabular EMA, and keyed memory bias.  It is
local product engineering evidence, not mechanism or subjectivity evidence.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping


STATE_KEYS = ("energy", "safety", "connection", "stimulation")
ACTIONS = ("approach", "explore", "forage", "rest", "withdraw")
CUES = ("resource", "contact", "novelty", "threat", "quiet")
TARGET_LEVEL = 0.72
EMA_ALPHA = 0.35
CONSOLIDATION_THRESHOLD = 3
EPISODE_SPAN_TICKS = 8

STATE_SCHEMA_VERSION = "ego.life_playground.state.v1"
RUN_SCHEMA_VERSION = "ego.life_playground.run.v1"
COMMAND_SCHEMA_VERSION = "ego.life_playground.command.v1"
TRACE_SCHEMA_VERSION = "ego.life_playground.trace.v1"

TRIGGER_SOURCES = (
    "ui_step_button",
    "ui_run_button",
    "headless_acceptance",
    "paired_intervention",
)
MEMORY_MODES = ("canonical", "off")
UPDATE_MODES = ("enabled", "frozen")
PROVENANCE_MODES = ("canonical", "shuffle_projection")
RUN_PRODUCER_FUNCTION = "ego_life_playground_v0.engine.compute_step"
RUN_AGGREGATION_RULE = "single_step_deterministic_one_step_argmax"
GOAL_SELECTION_REASONS = (
    "initial_max_deficit",
    "deficit_reappeared",
    "previous_goal_completed",
    "no_active_deficit",
)
ACTIVE_GOAL_SELECTION_REASONS = GOAL_SELECTION_REASONS[:-1]
_PROJECTION_REQUIRED_FIELDS = frozenset(
    {
        "cue",
        "current_goal",
        "action",
        "utility",
        "actual_delta",
        "source_episode_id",
        "source_command_hash",
        "source_sequence",
    }
)
DEFAULT_INTERVENTIONS = {
    "memory_mode": "canonical",
    "update_mode": "enabled",
    "provenance_mode": "canonical",
}

# Kept as a source-compatibility constant only.  It is never accepted in a V1
# command; the exact command schema uses DEFAULT_INTERVENTIONS above.
DEFAULT_TOGGLES = {
    "memory_on": True,
    "learning_on": True,
    "consolidation_on": True,
}

# These V0 constants are intentionally unchanged.
ACTION_PRIORS: dict[str, dict[str, float]] = {
    "forage": {"energy": 0.12, "safety": -0.03, "connection": 0.00, "stimulation": 0.02},
    "rest": {"energy": 0.09, "safety": 0.04, "connection": 0.00, "stimulation": -0.04},
    "approach": {"energy": -0.02, "safety": -0.02, "connection": 0.11, "stimulation": 0.03},
    "explore": {"energy": -0.05, "safety": -0.03, "connection": 0.00, "stimulation": 0.10},
    "withdraw": {"energy": -0.01, "safety": 0.10, "connection": -0.04, "stimulation": -0.03},
}

CUE_BONUSES: dict[str, dict[str, dict[str, float]]] = {
    "resource": {"forage": {"energy": 0.16}},
    "contact": {"approach": {"connection": 0.16}},
    "novelty": {"explore": {"stimulation": 0.16}},
    "threat": {
        "withdraw": {"safety": 0.18},
        "approach": {"safety": -0.09},
        "explore": {"safety": -0.08},
        "forage": {"safety": -0.07},
        "rest": {"safety": -0.05},
    },
    "quiet": {"rest": {"energy": 0.09, "safety": 0.04}},
}

ACTION_COSTS = {
    "approach": 0.018,
    "explore": 0.025,
    "forage": 0.020,
    "rest": 0.010,
    "withdraw": 0.015,
}


class EngineInvariantError(ValueError):
    """Raised when serialized causal input violates the frozen contract."""


@dataclass(frozen=True)
class StepResult:
    next_state: dict[str, Any]
    trace: dict[str, Any]


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def compute_code_path_hash() -> str:
    """Bind the canonical reducer and durable replay implementation."""

    source_paths = (Path(__file__), Path(__file__).with_name("store.py"))
    manifest = {
        "schema_version": "ego.life_playground.code_path.v1",
        "files": [
            {"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in source_paths
        ],
    }
    return canonical_hash(manifest)


def episode_id_for(run_id: str, episode_index: int) -> str:
    if type(run_id) is not str or not run_id:
        raise EngineInvariantError("run_id must be a non-empty string")
    if type(episode_index) is not int or episode_index < 0:
        raise EngineInvariantError("episode_index must be a non-negative integer")
    digest = canonical_hash(
        {"kind": "ego.life_playground.episode.v1", "run_id": run_id, "episode_index": episode_index}
    )[:16]
    return f"episode-{episode_index:06d}-{digest}"


def make_run_metadata(
    run_id: str, seed: int, episode_span_ticks: int = EPISODE_SPAN_TICKS
) -> dict[str, Any]:
    if type(run_id) is not str or not run_id:
        raise EngineInvariantError("run_id must be a non-empty string")
    if type(seed) is not int:
        raise EngineInvariantError("seed must be an integer")
    if type(episode_span_ticks) is not int:
        raise EngineInvariantError("episode_span_ticks must be an integer")
    if episode_span_ticks != EPISODE_SPAN_TICKS:
        raise EngineInvariantError("episode_span_ticks is frozen at 8")
    return {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "seed": seed,
        "episode_span_ticks": EPISODE_SPAN_TICKS,
        "producer_function": RUN_PRODUCER_FUNCTION,
        "aggregation_rule": RUN_AGGREGATION_RULE,
        "code_path_hash": compute_code_path_hash(),
        "science_weight": 0,
    }


def initial_state(
    organism: Mapping[str, float] | None = None, *, run_id: str = "manual-local"
) -> dict[str, Any]:
    values = {
        "energy": 0.45,
        "safety": 0.62,
        "connection": 0.50,
        "stimulation": 0.43,
    }
    if organism is not None:
        values.update({key: float(value) for key, value in organism.items()})
    if set(values) != set(STATE_KEYS):
        raise EngineInvariantError("organism state keys do not match canonical schema")
    normalized = {key: _clamp(values[key]) for key in STATE_KEYS}
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "clock": {
            "global_tick": 0,
            "episode_index": 0,
            "episode_id": episode_id_for(run_id, 0),
            "episode_tick": 0,
        },
        "organism": normalized,
        "current_goal": _select_goal(normalized, global_tick=0, reason="initial_max_deficit"),
        "model": {},
        "memory": {"episodic": [], "consolidated": []},
        "last_action": None,
        "last_command_hash": None,
        "last_trace_hash": None,
    }


def make_command(
    *,
    sequence: int,
    cue: str,
    trigger_source: str,
    interventions: Mapping[str, str],
    prev_command_hash: str | None,
) -> dict[str, Any]:
    if type(sequence) is not int or sequence <= 0:
        raise EngineInvariantError("command sequence must be a positive integer")
    if type(cue) is not str or cue not in CUES:
        raise EngineInvariantError(f"unknown cue: {cue}")
    if type(trigger_source) is not str or trigger_source not in TRIGGER_SOURCES:
        raise EngineInvariantError(f"unknown trigger_source: {trigger_source}")
    if sequence == 1 and prev_command_hash is not None:
        raise EngineInvariantError("first command prev_command_hash must be null")
    if sequence > 1 and not _is_sha256(prev_command_hash):
        raise EngineInvariantError("noninitial command prev_command_hash must be sha256")
    normalized = _normalize_interventions(interventions)
    payload: dict[str, Any] = {
        "schema_version": COMMAND_SCHEMA_VERSION,
        "sequence": sequence,
        "cue": cue,
        "trigger_source": trigger_source,
        "interventions": normalized,
        "prev_command_hash": prev_command_hash,
    }
    payload["command_hash"] = canonical_hash(payload)
    return payload


def verify_command(command: Mapping[str, Any], state: Mapping[str, Any]) -> None:
    allowed = {
        "schema_version",
        "sequence",
        "cue",
        "trigger_source",
        "interventions",
        "prev_command_hash",
        "command_hash",
    }
    if set(command) != allowed:
        extra = sorted(set(command) - allowed)
        missing = sorted(allowed - set(command))
        raise EngineInvariantError(f"command schema mismatch: extra={extra}, missing={missing}")
    if command["schema_version"] != COMMAND_SCHEMA_VERSION:
        raise EngineInvariantError("command schema_version is not canonical")
    sequence = command["sequence"]
    if isinstance(sequence, bool) or not isinstance(sequence, int):
        raise EngineInvariantError("command sequence must be an integer")
    if sequence <= 0:
        raise EngineInvariantError("command sequence must be positive")
    if sequence != int(state["clock"]["global_tick"]) + 1:
        raise EngineInvariantError("command sequence is not the next global tick")
    if command["prev_command_hash"] != state.get("last_command_hash"):
        raise EngineInvariantError("command chain mismatch")
    if command["cue"] not in CUES:
        raise EngineInvariantError("command cue is not canonical")
    if command["trigger_source"] not in TRIGGER_SOURCES:
        raise EngineInvariantError("command trigger_source is not canonical")
    _normalize_interventions(command["interventions"])
    unsigned = {key: command[key] for key in allowed if key != "command_hash"}
    if canonical_hash(unsigned) != command["command_hash"]:
        raise EngineInvariantError("command hash mismatch")


def state_hash(state: Mapping[str, Any]) -> str:
    """Hash causal state without the separately chained trace pointer."""

    causal_state = deepcopy(dict(state))
    causal_state.pop("last_trace_hash", None)
    return canonical_hash(causal_state)


def compute_trace_hash(trace: Mapping[str, Any]) -> str:
    return canonical_hash({key: value for key, value in trace.items() if key != "trace_hash"})


def compute_step(
    state: Mapping[str, Any], command: Mapping[str, Any], run_meta: Mapping[str, Any]
) -> StepResult:
    """Compute the sole live/replay/intervention state transition."""

    current_code_hash = compute_code_path_hash()
    _verify_run_metadata(run_meta, current_code_hash)
    _verify_state(state, run_id=str(run_meta["run_id"]))
    verify_command(command, state)

    before = deepcopy(dict(state))
    before_hash = state_hash(before)
    sequence = int(command["sequence"])
    cue = str(command["cue"])
    interventions = _normalize_interventions(command["interventions"])

    decision_state, episode_transition = _decision_state_for_tick(
        before, run_id=str(run_meta["run_id"]), sequence=sequence
    )
    decision_hash = state_hash(decision_state)
    goal_before = deepcopy(decision_state["current_goal"])
    current_goal = goal_before["state_variable"] or "homeostasis"
    context_key = f"{cue}|{current_goal}"

    memory_view, provenance_projection = _memory_read_view(
        decision_state["memory"],
        memory_mode=interventions["memory_mode"],
        provenance_mode=interventions["provenance_mode"],
        run_seed=int(run_meta["seed"]),
        global_tick=sequence,
    )
    candidates = [
        _score_candidate(
            state=decision_state,
            memory_view=memory_view,
            cue=cue,
            context_key=context_key,
            current_goal=goal_before,
            action=action,
            sequence=sequence,
            seed=int(run_meta["seed"]),
        )
        for action in ACTIONS
    ]
    candidates.sort(key=lambda item: item["action"])
    selected = max(
        candidates, key=lambda item: (item["total_score"], item["deterministic_tie"])
    )
    selected_action = str(selected["action"])
    predicted_delta = deepcopy(selected["predicted_delta"])
    actual_delta = _actual_delta(cue, selected_action)
    prediction_error = {
        key: _round(actual_delta[key] - predicted_delta[key]) for key in STATE_KEYS
    }

    next_state = deepcopy(decision_state)
    next_state["organism"] = _apply_delta(decision_state["organism"], actual_delta)
    next_state["last_action"] = selected_action
    next_state["last_command_hash"] = command["command_hash"]
    next_state["current_goal"], goal_progress, goal_transition = _advance_goal(
        goal_before,
        before_organism=decision_state["organism"],
        after_organism=next_state["organism"],
        global_tick=sequence,
    )

    updates_enabled = interventions["update_mode"] == "enabled"
    model_update = _update_model(
        next_state,
        context_key=context_key,
        action=selected_action,
        actual_delta=actual_delta,
        apply_update=updates_enabled,
    )
    memory_update = _update_memory(
        next_state,
        before_organism=decision_state["organism"],
        after_organism=next_state["organism"],
        actual_delta=actual_delta,
        cue=cue,
        current_goal=current_goal,
        action=selected_action,
        sequence=sequence,
        command_hash=str(command["command_hash"]),
        source_episode_id=str(decision_state["clock"]["episode_id"]),
        memory_enabled=interventions["memory_mode"] == "canonical",
        updates_enabled=updates_enabled,
    )

    after_hash = state_hash(next_state)
    trace: dict[str, Any] = {
        "schema_version": TRACE_SCHEMA_VERSION,
        "producer_function": RUN_PRODUCER_FUNCTION,
        "input_artifacts": [
            f"run:{run_meta['run_id']}",
            f"command:{command['command_hash']}",
        ],
        "run_id": run_meta["run_id"],
        "seed": int(run_meta["seed"]),
        "episode_id": decision_state["clock"]["episode_id"],
        "episode_index": decision_state["clock"]["episode_index"],
        "global_tick": sequence,
        "episode_tick": decision_state["clock"]["episode_tick"],
        "aggregation_rule": run_meta["aggregation_rule"],
        "sequence": sequence,
        "trigger_source": command["trigger_source"],
        "cue": cue,
        "interventions": interventions,
        "command": deepcopy(dict(command)),
        "command_hash": command["command_hash"],
        "prev_command_hash": command["prev_command_hash"],
        "state_before_hash": before_hash,
        "decision_state_hash": decision_hash,
        "state_after_hash": after_hash,
        "episode_before": deepcopy(before["clock"]),
        "episode_transition": episode_transition,
        "action_episode": deepcopy(decision_state["clock"]),
        "goal_before": goal_before,
        "goal_progress": goal_progress,
        "goal_transition": goal_transition,
        "goal_after": deepcopy(next_state["current_goal"]),
        "context_key": context_key,
        "goals": propose_goals(decision_state["organism"]),
        "candidates": candidates,
        "selected_action": selected_action,
        "prediction": predicted_delta,
        "model_ref": selected["model_ref"],
        "memory_refs": selected["memory_refs"],
        "actual_delta": actual_delta,
        "prediction_error": prediction_error,
        "model_update": model_update,
        "memory_update": memory_update,
        "consolidation_refs": memory_update["consolidation_refs"],
        "provenance_projection": provenance_projection,
        "code_path_hash": current_code_hash,
        "prev_trace_hash": before.get("last_trace_hash"),
    }
    trace["trace_hash"] = compute_trace_hash(trace)
    next_state["last_trace_hash"] = trace["trace_hash"]
    return StepResult(next_state=next_state, trace=trace)


def propose_goals(organism: Mapping[str, float]) -> list[dict[str, Any]]:
    goals = [
        {
            "state_variable": key,
            "current": _round(float(organism[key])),
            "target": TARGET_LEVEL,
            "deficit": _round(max(0.0, TARGET_LEVEL - float(organism[key]))),
            "state_key_order": index,
        }
        for index, key in enumerate(STATE_KEYS)
    ]
    goals.sort(key=lambda item: (-item["deficit"], item["state_key_order"]))
    for priority, goal in enumerate(goals, start=1):
        goal["priority"] = priority
        goal.pop("state_key_order")
    return goals


def _verify_run_metadata(run_meta: Mapping[str, Any], current_code_hash: str) -> None:
    required = {
        "schema_version",
        "run_id",
        "seed",
        "episode_span_ticks",
        "producer_function",
        "aggregation_rule",
        "code_path_hash",
        "science_weight",
    }
    if set(run_meta) != required:
        raise EngineInvariantError("run metadata schema mismatch")
    if run_meta["schema_version"] != RUN_SCHEMA_VERSION:
        raise EngineInvariantError("run metadata schema_version is not canonical")
    if type(run_meta["run_id"]) is not str or not run_meta["run_id"]:
        raise EngineInvariantError("run_id must be a non-empty string")
    if type(run_meta["seed"]) is not int:
        raise EngineInvariantError("seed must be an integer")
    if type(run_meta["episode_span_ticks"]) is not int:
        raise EngineInvariantError("episode_span_ticks must be an integer")
    if run_meta["episode_span_ticks"] != EPISODE_SPAN_TICKS:
        raise EngineInvariantError("episode_span_ticks is frozen at 8")
    if run_meta["producer_function"] != RUN_PRODUCER_FUNCTION:
        raise EngineInvariantError("producer_function is not canonical")
    if run_meta["aggregation_rule"] != RUN_AGGREGATION_RULE:
        raise EngineInvariantError("aggregation_rule is not canonical")
    if type(run_meta["science_weight"]) is not int:
        raise EngineInvariantError("science_weight must be an integer")
    if run_meta["science_weight"] != 0:
        raise EngineInvariantError("science_weight must remain zero")
    if run_meta.get("code_path_hash") != current_code_hash:
        raise EngineInvariantError("engine code-path hash differs from frozen run metadata")


def _verify_state(state: Mapping[str, Any], *, run_id: str) -> None:
    required = {
        "schema_version",
        "clock",
        "organism",
        "current_goal",
        "model",
        "memory",
        "last_action",
        "last_command_hash",
        "last_trace_hash",
    }
    if not isinstance(state, Mapping):
        raise EngineInvariantError("causal state must be an object")
    if set(state) != required or state.get("schema_version") != STATE_SCHEMA_VERSION:
        raise EngineInvariantError("causal state schema mismatch")
    clock = state["clock"]
    if not isinstance(clock, Mapping) or set(clock) != {
        "global_tick",
        "episode_index",
        "episode_id",
        "episode_tick",
    }:
        raise EngineInvariantError("clock schema mismatch")
    for field in ("global_tick", "episode_index", "episode_tick"):
        value = clock[field]
        if type(value) is not int or value < 0:
            raise EngineInvariantError(f"{field} must be a non-negative integer")
    if type(clock["episode_id"]) is not str or not clock["episode_id"]:
        raise EngineInvariantError("episode_id must be a non-empty string")
    tick = clock["global_tick"]
    expected_index = 0 if tick == 0 else (tick - 1) // EPISODE_SPAN_TICKS
    expected_episode_tick = 0 if tick == 0 else ((tick - 1) % EPISODE_SPAN_TICKS) + 1
    if clock["episode_index"] != expected_index:
        raise EngineInvariantError("episode_index does not match global_tick")
    if clock["episode_tick"] != expected_episode_tick:
        raise EngineInvariantError("episode_tick does not match global_tick")
    if clock["episode_id"] != episode_id_for(run_id, expected_index):
        raise EngineInvariantError("episode_id does not match run and episode_index")

    organism = state["organism"]
    if not isinstance(organism, Mapping) or set(organism) != set(STATE_KEYS):
        raise EngineInvariantError("organism state keys do not match canonical schema")
    for key in STATE_KEYS:
        value = organism[key]
        if type(value) is not float:
            raise EngineInvariantError(f"organism {key} must be a float")
        if not math.isfinite(value):
            raise EngineInvariantError(f"organism {key} must be finite")
        if not 0.0 <= value <= 1.0:
            raise EngineInvariantError(f"organism {key} is outside the canonical range")

    _verify_goal(state["current_goal"], global_tick=tick)
    _verify_model(state["model"])
    _verify_memory(state["memory"])

    last_action = state["last_action"]
    last_command_hash = state["last_command_hash"]
    last_trace_hash = state["last_trace_hash"]
    if tick == 0:
        if last_action is not None:
            raise EngineInvariantError("last_action must be null at the initial clock")
        if last_command_hash is not None:
            raise EngineInvariantError("last_command_hash must be null at the initial clock")
        if last_trace_hash is not None:
            raise EngineInvariantError("last_trace_hash must be null at the initial clock")
    else:
        if last_action is None:
            raise EngineInvariantError("last_action must be non-null after the initial clock")
        if type(last_action) is not str or last_action not in ACTIONS:
            raise EngineInvariantError("last_action is not canonical")
        if last_command_hash is None:
            raise EngineInvariantError("last_command_hash must be non-null after the initial clock")
        if not _is_sha256(last_command_hash):
            raise EngineInvariantError("last_command_hash must be sha256")
        if last_trace_hash is None:
            raise EngineInvariantError("last_trace_hash must be non-null after the initial clock")
        if not _is_sha256(last_trace_hash):
            raise EngineInvariantError("last_trace_hash must be sha256")


def _verify_model(model: Any) -> None:
    if not isinstance(model, Mapping):
        raise EngineInvariantError("model must be an object")
    for context_key, actions in model.items():
        if type(context_key) is not str or context_key.count("|") != 1:
            raise EngineInvariantError("model context key is not canonical")
        cue, goal = context_key.split("|", 1)
        if cue not in CUES or goal not in {*STATE_KEYS, "homeostasis"}:
            raise EngineInvariantError("model context key is not canonical")
        if not isinstance(actions, Mapping):
            raise EngineInvariantError("model context action table must be an object")
        for action, entry in actions.items():
            if type(action) is not str or action not in ACTIONS:
                raise EngineInvariantError("model action is not canonical")
            if not isinstance(entry, Mapping) or set(entry) != {"count", "ema_delta"}:
                raise EngineInvariantError("model entry schema mismatch")
            if type(entry["count"]) is not int or entry["count"] <= 0:
                raise EngineInvariantError("model count must be a positive integer")
            _verify_delta(entry["ema_delta"], "model ema_delta")


def _verify_memory(memory: Any) -> None:
    if not isinstance(memory, Mapping) or set(memory) != {"episodic", "consolidated"}:
        raise EngineInvariantError("memory schema mismatch")
    episodic = memory["episodic"]
    consolidated = memory["consolidated"]
    if not isinstance(episodic, list):
        raise EngineInvariantError("episodic memory must be a list")
    if not isinstance(consolidated, list):
        raise EngineInvariantError("consolidated memory must be a list")
    memory_ids: set[str] = set()
    for entry in episodic:
        _verify_episodic_memory_entry(entry)
        memory_id = str(entry["memory_id"])
        if memory_id in memory_ids:
            raise EngineInvariantError("memory_id must be unique")
        memory_ids.add(memory_id)
    for entry in consolidated:
        _verify_consolidated_memory_entry(entry)
        memory_id = str(entry["memory_id"])
        if memory_id in memory_ids:
            raise EngineInvariantError("memory_id must be unique")
        memory_ids.add(memory_id)


def _verify_episodic_memory_entry(entry: Any) -> None:
    required = {
        "memory_id",
        "kind",
        "cue",
        "current_goal",
        "action",
        "utility",
        "actual_delta",
        "source_episode_id",
        "source_command_hash",
        "source_sequence",
    }
    if not isinstance(entry, Mapping) or set(entry) != required:
        raise EngineInvariantError("episodic memory entry schema mismatch")
    if type(entry["memory_id"]) is not str or not entry["memory_id"]:
        raise EngineInvariantError("episodic memory_id must be a non-empty string")
    if entry["kind"] != "episodic":
        raise EngineInvariantError("episodic memory kind is not canonical")
    _verify_memory_slot(entry, "episodic memory")
    if type(entry["utility"]) is not float or not math.isfinite(entry["utility"]):
        raise EngineInvariantError("episodic memory utility must be a finite float")
    _verify_delta(entry["actual_delta"], "episodic actual_delta")
    if type(entry["source_episode_id"]) is not str or not entry["source_episode_id"]:
        raise EngineInvariantError("episodic source_episode_id must be a non-empty string")
    if not _is_sha256(entry["source_command_hash"]):
        raise EngineInvariantError("episodic source_command_hash must be sha256")
    if type(entry["source_sequence"]) is not int or entry["source_sequence"] <= 0:
        raise EngineInvariantError("episodic source_sequence must be a positive integer")


def _verify_consolidated_memory_entry(entry: Any) -> None:
    required = {
        "memory_id",
        "kind",
        "key",
        "cue",
        "current_goal",
        "action",
        "strength",
        "source_command_hashes",
        "source_episode_ids",
        "source_sequences",
        "episode_count",
    }
    if not isinstance(entry, Mapping) or set(entry) != required:
        raise EngineInvariantError("consolidated memory entry schema mismatch")
    if type(entry["memory_id"]) is not str or not entry["memory_id"]:
        raise EngineInvariantError("consolidated memory_id must be a non-empty string")
    if entry["kind"] != "consolidated":
        raise EngineInvariantError("consolidated memory kind is not canonical")
    _verify_memory_slot(entry, "consolidated memory")
    expected_key = f"{entry['cue']}|{entry['current_goal']}|{entry['action']}"
    if entry["key"] != expected_key:
        raise EngineInvariantError("consolidated memory key does not match its slot")
    if type(entry["strength"]) is not float or not math.isfinite(entry["strength"]):
        raise EngineInvariantError("consolidated memory strength must be a finite float")
    hashes = entry["source_command_hashes"]
    episode_ids = entry["source_episode_ids"]
    sequences = entry["source_sequences"]
    if not isinstance(hashes, list) or not hashes or not all(_is_sha256(value) for value in hashes):
        raise EngineInvariantError("consolidated source_command_hashes must be a non-empty sha256 list")
    if not isinstance(episode_ids, list) or not episode_ids or not all(
        type(value) is str and bool(value) for value in episode_ids
    ):
        raise EngineInvariantError("consolidated source_episode_ids must be a non-empty string list")
    if not isinstance(sequences, list) or not sequences or not all(
        type(value) is int and value > 0 for value in sequences
    ):
        raise EngineInvariantError("consolidated source_sequences must be a positive integer list")
    if not (len(hashes) == len(episode_ids) == len(sequences)):
        raise EngineInvariantError("consolidated provenance lists must have equal length")
    episode_count = entry["episode_count"]
    if type(episode_count) is not int or episode_count < CONSOLIDATION_THRESHOLD:
        raise EngineInvariantError("consolidated episode_count is below threshold")
    if episode_count != len(set(episode_ids)):
        raise EngineInvariantError("consolidated episode_count does not match source episodes")


def _verify_memory_slot(entry: Mapping[str, Any], label: str) -> None:
    if type(entry["cue"]) is not str or entry["cue"] not in CUES:
        raise EngineInvariantError(f"{label} cue is not canonical")
    if type(entry["current_goal"]) is not str or entry["current_goal"] not in {
        *STATE_KEYS,
        "homeostasis",
    }:
        raise EngineInvariantError(f"{label} current_goal is not canonical")
    if type(entry["action"]) is not str or entry["action"] not in ACTIONS:
        raise EngineInvariantError(f"{label} action is not canonical")


def _verify_delta(delta: Any, label: str) -> None:
    if not isinstance(delta, Mapping) or set(delta) != set(STATE_KEYS):
        raise EngineInvariantError(f"{label} schema mismatch")
    for key in STATE_KEYS:
        value = delta[key]
        if type(value) is not float:
            raise EngineInvariantError(f"{label} {key} must be a float")
        if not math.isfinite(value):
            raise EngineInvariantError(f"{label} {key} must be finite")
        if not -1.0 <= value <= 1.0:
            raise EngineInvariantError(f"{label} {key} is outside the canonical range")


def _is_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _verify_goal(goal: Mapping[str, Any], *, global_tick: int) -> None:
    required = {
        "state_variable",
        "target",
        "selected_global_tick",
        "entry_deficit",
        "status",
        "selection_reason",
    }
    if set(goal) != required:
        raise EngineInvariantError("current_goal schema mismatch")
    if type(goal["target"]) is not float or goal["target"] != TARGET_LEVEL:
        raise EngineInvariantError(f"current_goal target must equal {TARGET_LEVEL} as a float")
    if type(goal["selected_global_tick"]) is not int or goal["selected_global_tick"] < 0:
        raise EngineInvariantError("selected_global_tick must be a non-negative integer")
    if goal["selected_global_tick"] > global_tick:
        raise EngineInvariantError("selected_global_tick cannot exceed global_tick")
    if type(goal["entry_deficit"]) is not float or not math.isfinite(goal["entry_deficit"]):
        raise EngineInvariantError("entry_deficit must be a finite float")
    if not 0.0 <= goal["entry_deficit"] <= TARGET_LEVEL:
        raise EngineInvariantError("entry_deficit is outside the canonical range")
    if goal["status"] not in {"active", "homeostasis"}:
        raise EngineInvariantError("current_goal status is not canonical")
    if goal["selection_reason"] not in GOAL_SELECTION_REASONS:
        raise EngineInvariantError("current_goal selection_reason is not canonical")
    if goal["status"] == "active" and goal["state_variable"] not in STATE_KEYS:
        raise EngineInvariantError("active current_goal state variable is not canonical")
    if goal["status"] == "active" and goal["selection_reason"] not in ACTIVE_GOAL_SELECTION_REASONS:
        raise EngineInvariantError("active current_goal selection_reason is not canonical")
    if goal["status"] == "active" and goal["entry_deficit"] <= 0.0:
        raise EngineInvariantError("active current_goal entry_deficit must be positive")
    if goal["status"] == "homeostasis" and goal["state_variable"] is not None:
        raise EngineInvariantError("homeostasis current_goal must have null state variable")
    if goal["status"] == "homeostasis" and goal["selection_reason"] != "no_active_deficit":
        raise EngineInvariantError("homeostasis current_goal selection_reason is not canonical")
    if goal["status"] == "homeostasis" and goal["entry_deficit"] != 0.0:
        raise EngineInvariantError("homeostasis current_goal entry_deficit must be zero")


def _decision_state_for_tick(
    before: Mapping[str, Any], *, run_id: str, sequence: int
) -> tuple[dict[str, Any], dict[str, Any]]:
    episode_index = (sequence - 1) // EPISODE_SPAN_TICKS
    episode_tick = ((sequence - 1) % EPISODE_SPAN_TICKS) + 1
    decision = deepcopy(dict(before))
    decision["clock"] = {
        "global_tick": sequence,
        "episode_index": episode_index,
        "episode_id": episode_id_for(run_id, episode_index),
        "episode_tick": episode_tick,
    }
    applied = episode_index != int(before["clock"]["episode_index"])
    carry_checks = {
        "organism_unchanged": canonical_json(before["organism"]) == canonical_json(decision["organism"]),
        "model_unchanged": canonical_json(before["model"]) == canonical_json(decision["model"]),
        "memory_unchanged": canonical_json(before["memory"]) == canonical_json(decision["memory"]),
        "current_goal_unchanged": canonical_json(before["current_goal"])
        == canonical_json(decision["current_goal"]),
        "command_chain_unchanged": before.get("last_command_hash")
        == decision.get("last_command_hash"),
        "trace_chain_unchanged": before.get("last_trace_hash") == decision.get("last_trace_hash"),
    }
    return decision, {
        "applied": applied,
        "from_episode_index": int(before["clock"]["episode_index"]),
        "to_episode_index": episode_index,
        "rollover_global_tick": sequence if applied else None,
        "carry_checks": carry_checks,
    }


def _select_goal(
    organism: Mapping[str, float], *, global_tick: int, reason: str
) -> dict[str, Any]:
    deficits = [(key, max(0.0, TARGET_LEVEL - float(organism[key]))) for key in STATE_KEYS]
    state_variable, deficit = max(deficits, key=lambda item: item[1])
    if deficit <= 0.0:
        return {
            "state_variable": None,
            "target": TARGET_LEVEL,
            "selected_global_tick": int(global_tick),
            "entry_deficit": 0.0,
            "status": "homeostasis",
            "selection_reason": "no_active_deficit",
        }
    return {
        "state_variable": state_variable,
        "target": TARGET_LEVEL,
        "selected_global_tick": int(global_tick),
        "entry_deficit": _round(deficit),
        "status": "active",
        "selection_reason": reason,
    }


def _advance_goal(
    goal_before: Mapping[str, Any],
    *,
    before_organism: Mapping[str, float],
    after_organism: Mapping[str, float],
    global_tick: int,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    if goal_before["status"] == "homeostasis":
        next_goal = _select_goal(
            after_organism, global_tick=global_tick, reason="deficit_reappeared"
        )
        reappeared = next_goal["status"] == "active"
        if not reappeared:
            next_goal = deepcopy(dict(goal_before))
        return next_goal, {
            "state_variable": None,
            "deficit_before": 0.0,
            "deficit_after": 0.0,
            "deficit_reduction": 0.0,
            "completed": False,
        }, {
            "changed": reappeared,
            "kind": "deficit_reappeared" if reappeared else "homeostasis_carried",
        }

    key = str(goal_before["state_variable"])
    before_deficit = max(0.0, TARGET_LEVEL - float(before_organism[key]))
    after_deficit = max(0.0, TARGET_LEVEL - float(after_organism[key]))
    completed = after_deficit <= 0.0
    progress = {
        "state_variable": key,
        "deficit_before": _round(before_deficit),
        "deficit_after": _round(after_deficit),
        "deficit_reduction": _round(before_deficit - after_deficit),
        "completed": completed,
    }
    if not completed:
        return deepcopy(dict(goal_before)), progress, {"changed": False, "kind": "carried"}
    next_goal = _select_goal(
        after_organism, global_tick=global_tick, reason="previous_goal_completed"
    )
    kind = "completed_to_homeostasis" if next_goal["status"] == "homeostasis" else "previous_goal_completed"
    return next_goal, progress, {"changed": True, "kind": kind}


def _score_candidate(
    *,
    state: Mapping[str, Any],
    memory_view: Mapping[str, Any],
    cue: str,
    context_key: str,
    current_goal: Mapping[str, Any],
    action: str,
    sequence: int,
    seed: int,
) -> dict[str, Any]:
    model_entry = state["model"].get(context_key, {}).get(action)
    if model_entry and int(model_entry["count"]) > 0:
        predicted = {key: float(model_entry["ema_delta"][key]) for key in STATE_KEYS}
        model_ref = {
            "source": "tabular_ema",
            "context_key": context_key,
            "action": action,
            "count": int(model_entry["count"]),
        }
    else:
        predicted = _prior_prediction(cue, action)
        model_ref = {
            "source": "hardcoded_prior",
            "context_key": context_key,
            "action": action,
            "count": 0,
        }
    predicted_after = _apply_delta(state["organism"], predicted)
    goal_reduction = _current_goal_deficit_reduction(
        state["organism"], predicted_after, current_goal
    )
    total_reduction = _round(
        _total_deficit(state["organism"]) - _total_deficit(predicted_after)
    )
    memory_bias, memory_refs = _memory_bias(
        memory_view,
        cue=cue,
        current_goal=current_goal["state_variable"] or "homeostasis",
        action=action,
    )
    untried_bonus = 0.025 if model_ref["count"] == 0 else 0.0
    deterministic_tie = _deterministic_tie(seed, sequence, context_key, action)
    total_score = _round(
        goal_reduction
        + total_reduction
        + memory_bias
        + untried_bonus
        - ACTION_COSTS[action]
        + deterministic_tie,
        digits=9,
    )
    return {
        "action": action,
        "predicted_delta": {key: _round(predicted[key]) for key in STATE_KEYS},
        "current_goal_deficit_reduction": goal_reduction,
        "total_deficit_reduction": total_reduction,
        "memory_bias": _round(memory_bias),
        "untried_bonus": untried_bonus,
        "action_cost": ACTION_COSTS[action],
        "deterministic_tie": deterministic_tie,
        "total_score": total_score,
        "model_ref": model_ref,
        "memory_refs": memory_refs,
    }


def _prior_prediction(cue: str, action: str) -> dict[str, float]:
    prior = dict(ACTION_PRIORS[action])
    for key, bonus in CUE_BONUSES.get(cue, {}).get(action, {}).items():
        prior[key] += 0.5 * bonus
    return {key: _round(prior[key]) for key in STATE_KEYS}


def _actual_delta(cue: str, action: str) -> dict[str, float]:
    delta = dict(ACTION_PRIORS[action])
    for key, bonus in CUE_BONUSES.get(cue, {}).get(action, {}).items():
        delta[key] += bonus
    return {key: _round(delta[key]) for key in STATE_KEYS}


def _update_model(
    state: dict[str, Any],
    *,
    context_key: str,
    action: str,
    actual_delta: Mapping[str, float],
    apply_update: bool,
) -> dict[str, Any]:
    if not apply_update:
        return {
            "applied": False,
            "reason": "adaptive_updates_frozen",
            "context_key": context_key,
            "action": action,
        }
    context = state["model"].setdefault(context_key, {})
    previous = context.get(action)
    if previous is None:
        new_delta = {key: _round(float(actual_delta[key])) for key in STATE_KEYS}
        previous_count = 0
    else:
        previous_count = int(previous["count"])
        new_delta = {
            key: _round(
                (1.0 - EMA_ALPHA) * float(previous["ema_delta"][key])
                + EMA_ALPHA * float(actual_delta[key])
            )
            for key in STATE_KEYS
        }
    context[action] = {"count": previous_count + 1, "ema_delta": new_delta}
    return {
        "applied": True,
        "alpha": EMA_ALPHA,
        "context_key": context_key,
        "action": action,
        "previous_count": previous_count,
        "new_count": previous_count + 1,
        "ema_delta": new_delta,
    }


def _update_memory(
    state: dict[str, Any],
    *,
    before_organism: Mapping[str, float],
    after_organism: Mapping[str, float],
    actual_delta: Mapping[str, float],
    cue: str,
    current_goal: str,
    action: str,
    sequence: int,
    command_hash: str,
    source_episode_id: str,
    memory_enabled: bool,
    updates_enabled: bool,
) -> dict[str, Any]:
    if not memory_enabled:
        return {
            "applied": False,
            "episodic_write": None,
            "consolidation_applied": False,
            "consolidation_refs": [],
            "reason": "memory_disabled",
        }
    if not updates_enabled:
        return {
            "applied": False,
            "episodic_write": None,
            "consolidation_applied": False,
            "consolidation_refs": [],
            "reason": "adaptive_updates_frozen",
        }

    utility = _round(_total_deficit(before_organism) - _total_deficit(after_organism))
    memory_id = f"mem-{canonical_hash({'source_command_hash': command_hash, 'slot': [cue, current_goal, action]})[:20]}"
    episode = {
        "memory_id": memory_id,
        "kind": "episodic",
        "cue": cue,
        "current_goal": current_goal,
        "action": action,
        "utility": utility,
        "actual_delta": {key: _round(actual_delta[key]) for key in STATE_KEYS},
        "source_episode_id": source_episode_id,
        "source_command_hash": command_hash,
        "source_sequence": sequence,
    }
    state["memory"]["episodic"].append(episode)

    matching = [
        entry
        for entry in state["memory"]["episodic"]
        if entry["cue"] == cue
        and entry["current_goal"] == current_goal
        and entry["action"] == action
    ]
    distinct_episodes = {entry["source_episode_id"] for entry in matching}
    if len(distinct_episodes) < CONSOLIDATION_THRESHOLD:
        return {
            "applied": True,
            "episodic_write": memory_id,
            "consolidation_applied": False,
            "consolidation_refs": [],
            "reason": "threshold_not_met",
        }

    ordered = sorted(
        matching,
        key=lambda entry: (
            entry["source_episode_id"],
            entry["source_command_hash"],
            int(entry["source_sequence"]),
        ),
    )
    source_hashes = [entry["source_command_hash"] for entry in ordered]
    source_episode_ids = [entry["source_episode_id"] for entry in ordered]
    source_sequences = [int(entry["source_sequence"]) for entry in ordered]
    strength = _round(sum(float(entry["utility"]) for entry in ordered) / len(ordered))
    key = f"{cue}|{current_goal}|{action}"
    consolidated_id = f"con-{canonical_hash({'key': key, 'source_command_hashes': source_hashes})[:20]}"
    consolidated = {
        "memory_id": consolidated_id,
        "kind": "consolidated",
        "key": key,
        "cue": cue,
        "current_goal": current_goal,
        "action": action,
        "strength": strength,
        "source_command_hashes": source_hashes,
        "source_episode_ids": source_episode_ids,
        "source_sequences": source_sequences,
        "episode_count": len(distinct_episodes),
    }
    existing = state["memory"]["consolidated"]
    state["memory"]["consolidated"] = [item for item in existing if item["key"] != key]
    state["memory"]["consolidated"].append(consolidated)
    state["memory"]["consolidated"].sort(key=lambda item: item["key"])
    return {
        "applied": True,
        "episodic_write": memory_id,
        "consolidation_applied": True,
        "consolidation_refs": source_hashes,
        "consolidated_write": consolidated_id,
        "reason": "threshold_met",
    }


def _memory_read_view(
    memory: Mapping[str, Any],
    *,
    memory_mode: str,
    provenance_mode: str,
    run_seed: int,
    global_tick: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_hash = _semantic_memory_hash(memory)
    if memory_mode == "off":
        empty = {"episodic": [], "consolidated": []}
        return empty, {
            "mode": provenance_mode,
            "status": "memory_disabled",
            "source_memory_hash": source_hash,
            "projected_view_hash": _semantic_memory_hash(empty),
            "permutation_hash": None,
            "eligibility_count": 0,
            "cross_slot_moves": 0,
            "marginal_preservation": _compute_projection_marginals(empty, empty),
        }
    canonical = deepcopy(dict(memory))
    if provenance_mode == "canonical":
        return canonical, {
            "mode": "canonical",
            "status": "canonical",
            "source_memory_hash": source_hash,
            "projected_view_hash": source_hash,
            "permutation_hash": None,
            "eligibility_count": len(canonical.get("episodic", [])),
            "cross_slot_moves": 0,
            "marginal_preservation": _compute_projection_marginals(canonical, canonical),
        }
    return _shuffle_provenance_projection(canonical, run_seed=run_seed, global_tick=global_tick)


def _shuffle_provenance_projection(
    memory: Mapping[str, Any], *, run_seed: int, global_tick: int
) -> tuple[dict[str, Any], dict[str, Any]]:
    projected = deepcopy(dict(memory))
    eligible = _eligible_projection_records(projected)
    eligible.sort(key=lambda item: canonical_json(item["stable_key"]))
    slots = {item["slot"] for item in eligible}
    bundle_hashes = [canonical_hash(item["bundle"]) for item in eligible]
    source_hash = _semantic_memory_hash(memory)
    base_report = {
        "mode": "shuffle_projection",
        "source_memory_hash": source_hash,
        "eligibility_count": len(eligible),
        "marginal_preservation": _compute_projection_marginals(memory, projected),
    }
    if len(eligible) < 2 or len(slots) < 2 or len(set(bundle_hashes)) < 2:
        report = dict(base_report)
        report.update(
            {
                "status": "not_applied_insufficient_records",
                "projected_view_hash": source_hash,
                "permutation_hash": None,
                "cross_slot_moves": 0,
            }
        )
        return projected, report

    stable_keys = [item["stable_key"] for item in eligible]
    seed_hash = canonical_hash(
        {"run_seed": int(run_seed), "global_tick": int(global_tick), "stable_lineage_keys": stable_keys}
    )
    start_rotation = 1 + (int(seed_hash[:16], 16) % (len(eligible) - 1))
    rotations = [
        ((start_rotation - 1 + offset) % (len(eligible) - 1)) + 1
        for offset in range(len(eligible) - 1)
    ]
    rotation = rotations[0]
    for candidate_rotation in rotations:
        if any(
            eligible[(position - candidate_rotation) % len(eligible)]["slot"] != item["slot"]
            for position, item in enumerate(eligible)
        ):
            rotation = candidate_rotation
            break

    cross_slot_moves = 0
    for position, target in enumerate(eligible):
        source = eligible[(position - rotation) % len(eligible)]
        if source["slot"] != target["slot"]:
            cross_slot_moves += 1
        entry = projected["episodic"][target["index"]]
        for key, value in source["bundle"].items():
            entry[key] = deepcopy(value)
    marginals = _compute_projection_marginals(memory, projected)
    preserved = bool(
        marginals["slot_counts_preserved"] and marginals["bundle_multiset_preserved"]
    )
    report = dict(base_report)
    report.update(
        {
            "status": "applied" if cross_slot_moves > 0 and preserved else "projection_invariant_failed",
            "projected_view_hash": _semantic_memory_hash(projected),
            "permutation_hash": canonical_hash(
                {
                    "seed_hash": seed_hash,
                    "rotation": rotation,
                    "stable_lineage_keys": stable_keys,
                    "source_bundle_hashes": bundle_hashes,
                }
            ),
            "cross_slot_moves": cross_slot_moves,
            "marginal_preservation": marginals,
        }
    )
    return projected, report


def _eligible_projection_records(memory: Mapping[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, entry in enumerate(memory.get("episodic", [])):
        if not isinstance(entry, Mapping) or not _PROJECTION_REQUIRED_FIELDS <= set(entry):
            continue
        slot = (entry["cue"], entry["current_goal"], entry["action"])
        bundle = {
            "utility": entry["utility"],
            "actual_delta": deepcopy(entry["actual_delta"]),
            "source_episode_id": entry["source_episode_id"],
            "source_command_hash": entry["source_command_hash"],
        }
        records.append(
            {
                "index": index,
                "slot": slot,
                "stable_key": (
                    entry["source_episode_id"],
                    entry["source_command_hash"],
                    entry["source_sequence"],
                    slot,
                ),
                "bundle": bundle,
                "bundle_hash": canonical_hash(bundle),
            }
        )
    return records


def _compute_projection_marginals(
    before_memory: Mapping[str, Any], after_memory: Mapping[str, Any]
) -> dict[str, Any]:
    """Compute shuffle invariants from the actual eligible records on both sides."""

    before_records = _eligible_projection_records(before_memory)
    after_records = _eligible_projection_records(after_memory)

    def slot_counts(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        counts: dict[tuple[Any, Any, Any], int] = {}
        for record in records:
            slot = record["slot"]
            counts[slot] = counts.get(slot, 0) + 1
        return [
            {
                "slot": {"cue": slot[0], "current_goal": slot[1], "action": slot[2]},
                "count": count,
            }
            for slot, count in sorted(counts.items(), key=lambda item: canonical_json(item[0]))
        ]

    def bundle_hash_counts(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        counts: dict[str, int] = {}
        for record in records:
            bundle_hash = str(record["bundle_hash"])
            counts[bundle_hash] = counts.get(bundle_hash, 0) + 1
        return [
            {"bundle_hash": bundle_hash, "count": counts[bundle_hash]}
            for bundle_hash in sorted(counts)
        ]

    before_slots = slot_counts(before_records)
    after_slots = slot_counts(after_records)
    before_bundles = bundle_hash_counts(before_records)
    after_bundles = bundle_hash_counts(after_records)
    return {
        "slot_counts_preserved": before_slots == after_slots,
        "bundle_multiset_preserved": before_bundles == after_bundles,
        "eligible_records_before": len(before_records),
        "eligible_records_after": len(after_records),
        "slot_counts_before": before_slots,
        "slot_counts_after": after_slots,
        "bundle_hash_counts_before": before_bundles,
        "bundle_hash_counts_after": after_bundles,
    }


def _semantic_memory_hash(memory: Mapping[str, Any]) -> str:
    def strip(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {key: strip(item) for key, item in value.items() if key != "memory_id"}
        if isinstance(value, list):
            return [strip(item) for item in value]
        return value

    return canonical_hash(strip(memory))


def _memory_bias(
    memory: Mapping[str, Any], *, cue: str, current_goal: str, action: str
) -> tuple[float, list[str]]:
    bias = 0.0
    refs: list[str] = []
    for entry in memory.get("episodic", []):
        if (
            entry["cue"] == cue
            and entry["current_goal"] == current_goal
            and entry["action"] == action
        ):
            bias += 0.20 * float(entry["utility"])
            refs.append(str(entry["source_command_hash"]))
    for entry in memory.get("consolidated", []):
        if (
            entry["cue"] == cue
            and entry["current_goal"] == current_goal
            and entry["action"] == action
        ):
            bias += 0.65 * float(entry["strength"])
            refs.extend(str(value) for value in entry["source_command_hashes"])
    return max(-0.5, min(0.5, bias)), sorted(set(refs))


def _normalize_interventions(interventions: Mapping[str, str]) -> dict[str, str]:
    if not isinstance(interventions, Mapping) or set(interventions) != set(DEFAULT_INTERVENTIONS):
        raise EngineInvariantError("intervention keys do not match canonical schema")
    if any(type(interventions[key]) is not str for key in DEFAULT_INTERVENTIONS):
        raise EngineInvariantError("intervention enum values must be strings")
    normalized = {key: interventions[key] for key in sorted(DEFAULT_INTERVENTIONS)}
    if (
        normalized["memory_mode"] not in MEMORY_MODES
        or normalized["update_mode"] not in UPDATE_MODES
        or normalized["provenance_mode"] not in PROVENANCE_MODES
    ):
        raise EngineInvariantError("intervention enum mismatch")
    if (
        normalized["memory_mode"] == "off"
        and normalized["provenance_mode"] == "shuffle_projection"
    ):
        raise EngineInvariantError("invalid intervention combination: memory off with shuffle projection")
    return normalized


def _deterministic_tie(seed: int, sequence: int, context_key: str, action: str) -> float:
    digest = hashlib.sha256(f"{seed}|{sequence}|{context_key}|{action}".encode("utf-8")).digest()
    integer = int.from_bytes(digest[:8], "big")
    return _round((integer / float(2**64 - 1)) * 1e-6, digits=12)


def _current_goal_deficit_reduction(
    before: Mapping[str, float], after: Mapping[str, float], goal: Mapping[str, Any]
) -> float:
    if goal["status"] == "homeostasis":
        return 0.0
    key = str(goal["state_variable"])
    return _round(
        max(0.0, TARGET_LEVEL - float(before[key]))
        - max(0.0, TARGET_LEVEL - float(after[key]))
    )


def _apply_delta(organism: Mapping[str, float], delta: Mapping[str, float]) -> dict[str, float]:
    return {key: _round(_clamp(float(organism[key]) + float(delta[key]))) for key in STATE_KEYS}


def _total_deficit(organism: Mapping[str, float]) -> float:
    return sum(max(0.0, TARGET_LEVEL - float(organism[key])) for key in STATE_KEYS)


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _round(value: float, *, digits: int = 6) -> float:
    return round(float(value), digits)
