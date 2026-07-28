"""One deterministic V0/V1-descendant reducer for the V2 P0/P1/P2 microworld.

The implementation deliberately exposes its cheap explanation: a hard-coded
toy outcome table, deficit scoring, a tabular EMA, and keyed memory bias. The
P1 adds private world dynamics and competing-claim reads while preserving this
single live/replay reducer. This is bounded local product engineering, not a
general learning, agency, or subjectivity claim.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Mapping

from . import claims as claim_memory
from . import predictive_control
from . import survival_learning
from .microworld import (
    ACTIONS as WORLD_ACTIONS,
    ALLOWED_WORLD_EVENTS,
    initial_world_state,
    observation_hash,
    observe_world_event,
    policy_observation,
    public_world_projection,
    reset_world_for_life,
    transition_world,
    verify_world_state,
    world_hash,
)


STATE_KEYS = ("energy", "safety", "connection", "stimulation")
ACTIONS = WORLD_ACTIONS
TARGET_LEVEL = 0.72
EMA_ALPHA = 0.35
DEFAULT_PROVENANCE_SHUFFLE_SEED = 17
DEFAULT_PRIVATE_WORLD_SEED = 1701
CONSOLIDATION_THRESHOLD = 3
EPISODE_SPAN_TICKS = 256
MAX_LIVES = 16
REENTRY_THRESHOLD = 0.60
CRITICAL_OVERRIDE_THRESHOLD = 0.15
VISUAL_TRANSITION_MODEL_KEY = "__visual_transition_counts__"

STATE_SCHEMA_VERSION = "ego.life_playground.state.v10"
RUN_SCHEMA_VERSION = "ego.life_playground.run.v10"
COMMAND_SCHEMA_VERSION = "ego.life_playground.command.v7"
TRACE_SCHEMA_VERSION = "ego.life_playground.trace.v15"
COMPONENT_HASH_SCHEMA_VERSION = "ego.life_playground.component_hashes.v2"

TRIGGER_SOURCES = (
    "ui_step_button",
    "ui_run_button",
    "headless_acceptance",
    "paired_intervention",
    "terminal_step",
    "terminal_run",
    "terminal_event",
)
MEMORY_MODES = ("canonical", "off")
UPDATE_MODES = ("canonical", "frozen")
PROVENANCE_MODES = ("canonical", "shuffle_projection")
CONSOLIDATION_MODES = ("canonical", "off_projection")
VISION_MODES = ("canonical", "no_occlusion")
HYSTERESIS_MODES = ("canonical", "no_hysteresis")
NOVELTY_MODES = ("canonical", "no_novelty")
OVERRIDE_MODES = ("canonical", "no_override")
SURVIVAL_LEARNING_MODES = survival_learning.POLICY_MODES
PREDICTIVE_CONTROL_MODES = ("off", "factored_mpc")
PREDICTIVE_HORIZON_MODES = ("h12", "h1")
RELATIVE_MAP_MODES = predictive_control.RELATIVE_MAP_MODES
GOAL_VALUE_MODES = predictive_control.GOAL_VALUE_MODES
RUN_PRODUCER_FUNCTION = "ego_life_playground_v0.engine.compute_step"
RUN_AGGREGATION_RULE = "single_reducer_command_transition_action_or_respawn"
GOAL_SELECTION_REASONS = (
    "previous_goal_completed",
    "initial_deficit_priority",
    "reentry_below_threshold",
    "critical_override_energy",
    "critical_override_body_deficit",
    "explore_no_eligible_body_goal",
    "ablation_max_deficit_retarget",
)
ACTIVE_GOAL_SELECTION_REASONS = tuple(
    reason for reason in GOAL_SELECTION_REASONS if reason != "explore_no_eligible_body_goal"
)
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
    "update_mode": "canonical",
    "provenance_mode": "canonical",
    "provenance_shuffle_seed": str(DEFAULT_PROVENANCE_SHUFFLE_SEED),
    "consolidation_mode": "canonical",
    "vision_mode": "canonical",
    "hysteresis_mode": "canonical",
    "novelty_mode": "canonical",
    "override_mode": "canonical",
    "survival_learning_mode": "off",
    "predictive_control_mode": "off",
    "predictive_horizon_mode": "h12",
    "relative_map_mode": "relative",
    "goal_value_mode": "contextual",
}

# These V0 constants are intentionally unchanged.
ACTION_COSTS = {
    "turn_left": 0.004,
    "turn_right": 0.004,
    "move_forward": 0.012,
    "interact": 0.008,
    "rest": 0.002,
}
INITIAL_ORGANISM = {
    "energy": 0.45,
    "safety": 0.62,
    "connection": 0.50,
    "stimulation": 0.43,
}

# Task-local V2 product metabolism constants. ACTION_COSTS remains the existing
# selector cost table and is also the physical per-action energy cost so the
# trace has one auditable cost value rather than a second hidden table.
PASSIVE_ENERGY_DECAY_PER_TICK = 0.010
CAUSE_DELTAS = {
    "resource": {"energy": 0.280, "safety": 0.0, "connection": 0.0, "stimulation": 0.0},
    "social": {"energy": 0.0, "safety": 0.0, "connection": 0.160, "stimulation": 0.020},
    "novelty": {"energy": 0.0, "safety": -0.020, "connection": 0.0, "stimulation": 0.160},
    "threat": {"energy": 0.0, "safety": -0.180, "connection": 0.0, "stimulation": 0.040},
    "shelter": {"energy": 0.0, "safety": 0.120, "connection": 0.0, "stimulation": 0.0},
}
REST_DELTA = {"energy": 0.0, "safety": 0.020, "connection": 0.0, "stimulation": 0.0}
METABOLISM_PRODUCER_FUNCTION = (
    "ego_life_playground_v0.engine.compute_metabolism_ledger"
)
METABOLISM_AGGREGATION_RULE = (
    "clamp01(energy_before-passive_decay-action_cost+resource_gain_if_successful_resource_interact)"
)


class EngineInvariantError(ValueError):
    """Raised when serialized causal input violates the frozen contract."""


@dataclass(frozen=True)
class StepResult:
    next_state: dict[str, Any]
    trace: dict[str, Any]


_COMPONENT_ABSENT = object()


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def compute_code_path_manifest() -> dict[str, Any]:
    """Return the exact current causal-producer file manifest."""

    source_paths = (
        Path(__file__),
        Path(__file__).with_name("microworld.py"),
        Path(__file__).with_name("claims.py"),
        Path(__file__).with_name("predictive_control.py"),
        Path(__file__).with_name("survival_learning.py"),
        Path(__file__).with_name("store.py"),
    )
    return {
        "schema_version": "ego.life_playground.code_path.v11",
        "files": [
            {"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in source_paths
        ],
    }


def compute_code_path_hash() -> str:
    """Bind the canonical reducer, microworld, and durable replay bytes."""

    return canonical_hash(compute_code_path_manifest())


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
        raise EngineInvariantError("episode_span_ticks is frozen at 256")
    return {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "seed": seed,
        "episode_span_ticks": EPISODE_SPAN_TICKS,
        "max_lives": MAX_LIVES,
        "survival_learning": survival_learning.hyperparameters(),
        "default_survival_learning_mode": DEFAULT_INTERVENTIONS[
            "survival_learning_mode"
        ],
        "predictive_control": predictive_control.hyperparameters(),
        "default_predictive_control_mode": DEFAULT_INTERVENTIONS[
            "predictive_control_mode"
        ],
        "producer_function": RUN_PRODUCER_FUNCTION,
        "aggregation_rule": RUN_AGGREGATION_RULE,
        "code_path_hash": compute_code_path_hash(),
        "science_weight": 0,
    }


def initial_state(
    organism: Mapping[str, float] | None = None,
    *,
    run_id: str = "manual-local",
    seed: int = 17,
    layout_id: str = "p0_cross_v1",
) -> dict[str, Any]:
    values = dict(INITIAL_ORGANISM)
    if organism is not None:
        values.update({key: float(value) for key, value in organism.items()})
    if set(values) != set(STATE_KEYS):
        raise EngineInvariantError("organism state keys do not match canonical schema")
    normalized = {key: _clamp(values[key]) for key in STATE_KEYS}
    model: dict[str, Any] = {}
    memory = {
        "episodic": [],
        "consolidated": [],
        **claim_memory.empty_claim_memory(),
    }
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "clock": {
            "global_tick": 0,
            "episode_index": 0,
            "episode_id": episode_id_for(run_id, 0),
            "episode_tick": 0,
        },
        "organism": normalized,
        "world": initial_world_state(seed=seed, layout_id=layout_id),
        "current_goal": _select_initial_goal(
            normalized,
            global_tick=0,
        ),
        "model": model,
        "memory": memory,
        "component_hashes": {
            "schema_version": COMPONENT_HASH_SCHEMA_VERSION,
            "model": canonical_hash(model),
            "memory": canonical_hash(memory),
            "predictive_control": canonical_hash(predictive_control.empty_state()),
        },
        "survival_learner": survival_learning.empty_survival_learner(),
        "predictive_control": predictive_control.empty_state(),
        "lifecycle": {
            "trial_status": "active",
            "life_index": 1,
            "awaiting_respawn": False,
            "life_results": [],
            "terminal_life_result": None,
        },
        "last_action": None,
        "last_command_hash": None,
        "last_trace_hash": None,
    }


def make_command(
    *,
    sequence: int,
    trigger_source: str,
    interventions: Mapping[str, str],
    prev_command_hash: str | None,
    injected_event: str | None = None,
) -> dict[str, Any]:
    if type(sequence) is not int or sequence <= 0:
        raise EngineInvariantError("command sequence must be a positive integer")
    if type(trigger_source) is not str or trigger_source not in TRIGGER_SOURCES:
        raise EngineInvariantError(f"unknown trigger_source: {trigger_source}")
    if sequence == 1 and prev_command_hash is not None:
        raise EngineInvariantError("first command prev_command_hash must be null")
    if sequence > 1 and not _is_sha256(prev_command_hash):
        raise EngineInvariantError("noninitial command prev_command_hash must be sha256")
    normalized = _normalize_interventions(interventions)
    if injected_event is not None:
        if type(injected_event) is not str or injected_event not in ALLOWED_WORLD_EVENTS:
            raise EngineInvariantError("injected_event is not canonical")
    payload: dict[str, Any] = {
        "schema_version": COMMAND_SCHEMA_VERSION,
        "sequence": sequence,
        "injected_event": injected_event,
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
        "injected_event",
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
    injected_event = command["injected_event"]
    if injected_event is not None and (
        type(injected_event) is not str or injected_event not in ALLOWED_WORLD_EVENTS
    ):
        raise EngineInvariantError("command injected_event is not canonical")
    if command["trigger_source"] not in TRIGGER_SOURCES:
        raise EngineInvariantError("command trigger_source is not canonical")
    _normalize_interventions(command["interventions"])
    unsigned = {key: command[key] for key in allowed if key != "command_hash"}
    if canonical_hash(unsigned) != command["command_hash"]:
        raise EngineInvariantError("command hash mismatch")


def state_hash(state: Mapping[str, Any]) -> str:
    """Hash causal state without the separately chained trace pointer."""

    # The hash serializer is read-only.  Copying the complete, growing model and
    # memory before serializing it doubled the cost without changing the bytes.
    causal_state = dict(state)
    causal_state.pop("last_trace_hash", None)
    component_hashes = state.get("component_hashes", {})
    model = state.get("model", {})
    memory = state.get("memory", {})
    causal_state["model"] = {
        "component_hash": component_hashes.get("model"),
        "context_count": len(model) if isinstance(model, Mapping) else None,
        "visual_observation_count": len(
            model.get(VISUAL_TRANSITION_MODEL_KEY, {})
        )
        if isinstance(model, Mapping)
        and isinstance(model.get(VISUAL_TRANSITION_MODEL_KEY, {}), Mapping)
        else None,
    }
    causal_state["memory"] = {
        "component_hash": component_hashes.get("memory"),
        "episodic_count": len(memory.get("episodic", []))
        if isinstance(memory, Mapping)
        else None,
        "consolidated_count": len(memory.get("consolidated", []))
        if isinstance(memory, Mapping)
        else None,
        "claim_event_count": len(memory.get("claim_events", []))
        if isinstance(memory, Mapping)
        else None,
        "competing_claim_count": len(memory.get("competing_claims", []))
        if isinstance(memory, Mapping)
        else None,
    }
    predictive = state.get("predictive_control", {})
    causal_state["predictive_control"] = {
        "component_hash": component_hashes.get("predictive_control"),
        "model_update_count": (
            predictive.get("model", {}).get("update_count")
            if isinstance(predictive, Mapping)
            else None
        ),
        "belief_observation_count": (
            predictive.get("belief", {}).get("observation_count")
            if isinstance(predictive, Mapping)
            else None
        ),
    }
    return canonical_hash(causal_state)


def compute_trace_hash(trace: Mapping[str, Any]) -> str:
    return canonical_hash({key: value for key, value in trace.items() if key != "trace_hash"})


def verify_replay_boundary(
    state: Mapping[str, Any], run_meta: Mapping[str, Any]
) -> None:
    """Validate serialized run metadata and state before command recomputation."""

    current_code_hash = compute_code_path_hash()
    _verify_run_metadata(run_meta, current_code_hash)
    _verify_state(state, run_id=str(run_meta["run_id"]))


def _initial_organism() -> dict[str, float]:
    return {key: float(value) for key, value in INITIAL_ORGANISM.items()}


def _life_result(*, life_index: int, survival_ticks: int, censored: bool, termination: str) -> dict[str, Any]:
    return {
        "life_index": life_index,
        "survival_ticks": survival_ticks,
        "censored": censored,
        "termination": termination,
    }


def _component_receipt(before_value: Any, after_value: Any, expected_value: Any) -> dict[str, Any]:
    before_absent = before_value is _COMPONENT_ABSENT
    after_absent = after_value is _COMPONENT_ABSENT
    expected_absent = expected_value is _COMPONENT_ABSENT
    before_hash = None if before_absent else canonical_hash(before_value)
    after_hash = None if after_absent else canonical_hash(after_value)
    expected_hash = None if expected_absent else canonical_hash(expected_value)
    return {
        "before_hash": before_hash,
        "after_hash": after_hash,
        "expected_hash": expected_hash,
        "matches_expected": after_hash == expected_hash and after_absent == expected_absent,
        "changed": before_hash != after_hash or before_absent != after_absent,
        "absent_before": before_absent,
        "absent_after": after_absent,
        "expected_absent": expected_absent,
    }


def _respawn_trace(
    before: Mapping[str, Any],
    next_state: Mapping[str, Any],
    *,
    command: Mapping[str, Any],
    run_meta: Mapping[str, Any],
    current_code_hash: str,
    sequence: int,
    before_hash: str,
    after_hash: str,
    carry_reset_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    expected_world_after = reset_world_for_life(before["world"], int(next_state["lifecycle"]["life_index"]))
    carry_checks = {
        "organism_reset_applied": canonical_json(before["organism"]) != canonical_json(next_state["organism"]),
        "model_unchanged": canonical_json(before["model"]) == canonical_json(next_state["model"]),
        "memory_unchanged": canonical_json(before["memory"]) == canonical_json(next_state["memory"]),
        "survival_q_unchanged": canonical_json(
            before["survival_learner"]["q_values"]
        )
        == canonical_json(next_state["survival_learner"]["q_values"]),
        "survival_visits_unchanged": canonical_json(
            before["survival_learner"]["visit_counts"]
        )
        == canonical_json(next_state["survival_learner"]["visit_counts"]),
        "survival_eligibility_cleared": next_state["survival_learner"][
            "eligibility"
        ]
        == {},
        "current_goal_reset_applied": canonical_json(before["current_goal"])
        != canonical_json(next_state["current_goal"]),
        "world_reset_applied": canonical_json(before["world"]) != canonical_json(next_state["world"]),
        "world_matches_expected_reset": canonical_json(next_state["world"])
        == canonical_json(expected_world_after),
        "command_chain_continued": command["prev_command_hash"] == before.get("last_command_hash"),
        "trace_chain_continued": False,
    }
    trace: dict[str, Any] = {
        "schema_version": TRACE_SCHEMA_VERSION,
        "producer_function": RUN_PRODUCER_FUNCTION,
        "input_artifacts": [
            f"run:{run_meta['run_id']}",
            f"command:{command['command_hash']}",
        ],
        "run_id": run_meta["run_id"],
        "seed": int(run_meta["seed"]),
        "episode_id": next_state["clock"]["episode_id"],
        "episode_index": next_state["clock"]["episode_index"],
        "global_tick": sequence,
        "episode_tick": next_state["clock"]["episode_tick"],
        "aggregation_rule": run_meta["aggregation_rule"],
        "sequence": sequence,
        "trigger_source": command["trigger_source"],
        "injected_event": None,
        "interventions": _normalize_interventions(command["interventions"]),
        "command": deepcopy(dict(command)),
        "command_hash": command["command_hash"],
        "prev_command_hash": command["prev_command_hash"],
        "state_before_hash": before_hash,
        "decision_state_hash": None,
        "state_after_hash": after_hash,
        "world_before_hash": world_hash(before["world"]),
        "world_decision_hash": None,
        "world_after_hash": world_hash(next_state["world"]),
        "world_observation": None,
        "observation": None,
        "observation_hash": None,
        "policy_projection": None,
        "policy_projection_hash": None,
        "policy_decision_input_hash": None,
        "candidate_actions": [],
        "world_transition": None,
        "episode_before": deepcopy(before["clock"]),
        "episode_transition": {
            "applied": True,
            "from_episode_index": before["clock"]["episode_index"],
            "to_episode_index": next_state["clock"]["episode_index"],
            "rollover_global_tick": sequence,
            "carry_checks": carry_checks,
        },
        "action_episode": None,
        "goal_before": deepcopy(before["current_goal"]),
        "goal_progress": None,
        "goal_transition": None,
        "goal_after": deepcopy(next_state["current_goal"]),
        "context_key": None,
        "candidates": [],
        "selected_action": None,
        "prediction": None,
        "model_ref": None,
        "memory_refs": [],
        "claim_retrieval": None,
        "actual_delta": None,
        "energy_before": None,
        "passive_decay": None,
        "action_cost": None,
        "food_gain": None,
        "energy_after": None,
        "downstream_effect": None,
        "metabolism": None,
        "prediction_error": None,
        "model_update": {"applied": False, "reason": "pure_respawn"},
        "memory_update": {"applied": False, "reason": "pure_respawn", "consolidation_refs": []},
        "claim_update": {"applied": False, "reason": "pure_respawn"},
        "survival_learning": {
            "selection": None,
            "update": None,
            "respawn_eligibility_cleared": True,
            "learner_hash_after": survival_learning.learner_state_hash(
                next_state["survival_learner"]
            ),
            "q_table_size": survival_learning.q_table_size(
                next_state["survival_learner"]
            ),
            "update_count": int(next_state["survival_learner"]["update_count"]),
        },
        "predictive_control": {
            "schema_version": "ego.life_playground.predictive_control_trace.v4",
            "mode": command["interventions"]["predictive_control_mode"],
            "belief_observation": {
                "applied": True,
                "reason": "episode_relative_belief_reset",
            },
            "belief_hash": canonical_hash(
                next_state["predictive_control"]["belief"]
            ),
            "model_hash": canonical_hash(
                next_state["predictive_control"]["model"]
            ),
            "exploration_hash": canonical_hash(
                next_state["predictive_control"]["exploration"]
            ),
            "model_update_count": int(
                next_state["predictive_control"]["model"]["update_count"]
            ),
            "plan": None,
            "update": {
                "applied": False,
                "reason": "pure_respawn",
            },
        },
        "model_bytes": {
            "before_hash": canonical_hash(before["model"]),
            "after_hash": canonical_hash(next_state["model"]),
            "changed": canonical_hash(before["model"]) != canonical_hash(next_state["model"]),
        },
        "memory_bytes": {
            "before_hash": canonical_hash(before["memory"]),
            "after_hash": canonical_hash(next_state["memory"]),
            "changed": canonical_hash(before["memory"]) != canonical_hash(next_state["memory"]),
        },
        "consolidation_refs": [],
        "provenance_projection": None,
        "vision_ablation": {
            "requested_mode": command["interventions"]["vision_mode"],
            "applied": False,
        },
        "code_path_hash": current_code_hash,
        "prev_trace_hash": before.get("last_trace_hash"),
        "transition_kind": "respawn",
        "policy_invoked": False,
        "lifecycle_before": deepcopy(before["lifecycle"]),
        "lifecycle_after": deepcopy(next_state["lifecycle"]),
        "life_termination": deepcopy(before["lifecycle"]["life_results"][-1]),
        "command_chain": {
            "before_last_command_hash": before.get("last_command_hash"),
            "command_prev_matches_before": command["prev_command_hash"] == before.get("last_command_hash"),
            "after_last_command_hash": next_state.get("last_command_hash"),
            "after_matches_command_hash": next_state.get("last_command_hash") == command["command_hash"],
        },
        "trace_chain": {
            "before_last_trace_hash": before.get("last_trace_hash"),
            "trace_prev_matches_before": before.get("last_trace_hash") is not None,
        },
        "carry_reset_receipt": deepcopy(carry_reset_receipt),
    }
    trace["episode_transition"]["carry_checks"]["trace_chain_continued"] = (
        trace["prev_trace_hash"] == before.get("last_trace_hash")
    )
    trace["trace_chain"]["trace_prev_matches_before"] = (
        trace["prev_trace_hash"] == before.get("last_trace_hash")
    )
    trace["trace_hash"] = compute_trace_hash(trace)
    return trace


def compute_step(
    state: Mapping[str, Any], command: Mapping[str, Any], run_meta: Mapping[str, Any]
) -> StepResult:
    """Compute the sole live/replay/intervention state transition."""

    current_code_hash = compute_code_path_hash()
    _verify_run_metadata(run_meta, current_code_hash)
    _verify_state(state, run_id=str(run_meta["run_id"]))
    verify_command(command, state)

    # Treat the verified input as immutable and copy only components that this
    # transition changes.  This is the online form of the same reducer, not a
    # checkpoint or alternate state-transition path.
    before = dict(state)
    before_hash = state_hash(before)
    sequence = int(command["sequence"])
    interventions = _normalize_interventions(command["interventions"])
    lifecycle_before = deepcopy(before["lifecycle"])

    if lifecycle_before["trial_status"] == "terminal":
        raise EngineInvariantError("trial is terminal")
    if lifecycle_before["awaiting_respawn"]:
        if command["injected_event"] is not None:
            raise EngineInvariantError("respawn command must reject injected_event")
        next_life_index = int(lifecycle_before["life_index"]) + 1
        if next_life_index > MAX_LIVES:
            raise EngineInvariantError("trial cannot respawn beyond max_lives")
        next_state = deepcopy(before)
        expected_world_after = reset_world_for_life(before["world"], next_life_index)
        next_state["clock"] = {
            "global_tick": sequence,
            "episode_index": next_life_index - 1,
            "episode_id": episode_id_for(str(run_meta["run_id"]), next_life_index - 1),
            "episode_tick": 0,
        }
        next_state["organism"] = _initial_organism()
        next_state["world"] = deepcopy(expected_world_after)
        next_state["current_goal"] = _select_initial_goal(
            next_state["organism"],
            global_tick=sequence,
        )
        next_state["survival_learner"] = (
            survival_learning.clear_eligibility_for_respawn(
                before["survival_learner"]
            )
        )
        next_state["predictive_control"] = predictive_control.reset_for_respawn(
            before["predictive_control"], episode_index=next_life_index - 1
        )
        component_hashes = dict(before["component_hashes"])
        component_hashes["predictive_control"] = canonical_hash(
            next_state["predictive_control"]
        )
        next_state["component_hashes"] = component_hashes
        next_state["lifecycle"] = {
            "trial_status": "active",
            "life_index": next_life_index,
            "awaiting_respawn": False,
            "life_results": deepcopy(lifecycle_before["life_results"]),
            "terminal_life_result": deepcopy(
                lifecycle_before["terminal_life_result"]
            ),
        }
        next_state["last_action"] = None
        next_state["last_command_hash"] = command["command_hash"]
        carry_reset_receipt = {
            "model": _component_receipt(before["model"], next_state["model"], before["model"]),
            "memory_schema_version": _component_receipt(
                before["memory"]["schema_version"],
                next_state["memory"]["schema_version"],
                before["memory"]["schema_version"],
            ),
            "memory_episodic": _component_receipt(
                before["memory"]["episodic"],
                next_state["memory"]["episodic"],
                before["memory"]["episodic"],
            ),
            "memory_consolidated": _component_receipt(
                before["memory"]["consolidated"],
                next_state["memory"]["consolidated"],
                before["memory"]["consolidated"],
            ),
            "memory_claim_events": _component_receipt(
                before["memory"]["claim_events"],
                next_state["memory"]["claim_events"],
                before["memory"]["claim_events"],
            ),
            "memory_competing_claims": _component_receipt(
                before["memory"]["competing_claims"],
                next_state["memory"]["competing_claims"],
                before["memory"]["competing_claims"],
            ),
            "survival_q_values": _component_receipt(
                before["survival_learner"]["q_values"],
                next_state["survival_learner"]["q_values"],
                before["survival_learner"]["q_values"],
            ),
            "survival_visit_counts": _component_receipt(
                before["survival_learner"]["visit_counts"],
                next_state["survival_learner"]["visit_counts"],
                before["survival_learner"]["visit_counts"],
            ),
            "survival_update_count": _component_receipt(
                before["survival_learner"]["update_count"],
                next_state["survival_learner"]["update_count"],
                before["survival_learner"]["update_count"],
            ),
            "survival_eligibility": _component_receipt(
                before["survival_learner"]["eligibility"],
                next_state["survival_learner"]["eligibility"],
                {},
            ),
            "predictive_model": _component_receipt(
                before["predictive_control"]["model"],
                next_state["predictive_control"]["model"],
                before["predictive_control"]["model"],
            ),
            "predictive_belief": _component_receipt(
                before["predictive_control"]["belief"],
                next_state["predictive_control"]["belief"],
                predictive_control.empty_state()["belief"]
                | {"episode_index": next_life_index - 1},
            ),
            "token_mapping": _component_receipt(
                before["world"]["trial"]["token_mapping"],
                next_state["world"]["trial"]["token_mapping"],
                before["world"]["trial"]["token_mapping"],
            ),
            "organism": _component_receipt(before["organism"], next_state["organism"], _initial_organism()),
            "world": _component_receipt(
                before["world"],
                next_state["world"],
                expected_world_after,
            ),
            "agent_position": _component_receipt(
                before["world"]["agent"]["position"],
                next_state["world"]["agent"]["position"],
                expected_world_after["agent"]["position"],
            ),
            "agent_facing": _component_receipt(
                before["world"]["agent"]["facing"],
                next_state["world"]["agent"]["facing"],
                expected_world_after["agent"]["facing"],
            ),
            "object_positions": _component_receipt(
                {
                    cause: item["position"]
                    for cause, item in before["world"]["objects_by_cause"].items()
                },
                {
                    cause: item["position"]
                    for cause, item in next_state["world"]["objects_by_cause"].items()
                },
                {
                    cause: item["position"]
                    for cause, item in expected_world_after["objects_by_cause"].items()
                },
            ),
            "object_spawn_counts": _component_receipt(
                {
                    cause: item["spawn_count"]
                    for cause, item in before["world"]["objects_by_cause"].items()
                },
                {
                    cause: item["spawn_count"]
                    for cause, item in next_state["world"]["objects_by_cause"].items()
                },
                {
                    cause: item["spawn_count"]
                    for cause, item in expected_world_after["objects_by_cause"].items()
                },
            ),
            "object_injection_counts": _component_receipt(
                {
                    cause: item["injection_count"]
                    for cause, item in before["world"]["objects_by_cause"].items()
                },
                {
                    cause: item["injection_count"]
                    for cause, item in next_state["world"]["objects_by_cause"].items()
                },
                {
                    cause: item["injection_count"]
                    for cause, item in expected_world_after["objects_by_cause"].items()
                },
            ),
            "current_goal": _component_receipt(
                before["current_goal"],
                next_state["current_goal"],
                _select_initial_goal(_initial_organism(), global_tick=sequence),
            ),
            "goal_completed_latches": _component_receipt(
                before["current_goal"]["completed_latches"],
                next_state["current_goal"]["completed_latches"],
                _select_initial_goal(_initial_organism(), global_tick=sequence)[
                    "completed_latches"
                ],
            ),
            "last_action": _component_receipt(before.get("last_action"), next_state.get("last_action"), None),
            "episode_tick": _component_receipt(
                before["clock"]["episode_tick"],
                next_state["clock"]["episode_tick"],
                0,
            ),
            "working_spatial_state": _component_receipt(
                _COMPONENT_ABSENT,
                _COMPONENT_ABSENT,
                _COMPONENT_ABSENT,
            ),
        }
        after_hash = state_hash(next_state)
        trace = _respawn_trace(
            before,
            next_state,
            command=command,
            run_meta=run_meta,
            current_code_hash=current_code_hash,
            sequence=sequence,
            before_hash=before_hash,
            after_hash=after_hash,
            carry_reset_receipt=carry_reset_receipt,
        )
        next_state["last_trace_hash"] = trace["trace_hash"]
        return StepResult(next_state=next_state, trace=trace)

    decision_state, episode_transition = _decision_state_for_tick(
        before, run_id=str(run_meta["run_id"]), sequence=sequence
    )
    world_before = deepcopy(decision_state["world"])
    injected_event = command["injected_event"]
    if injected_event is not None:
        try:
            decision_state["world"] = observe_world_event(world_before, injected_event)
        except ValueError as exc:
            raise EngineInvariantError(str(exc)) from exc
    try:
        world_observation = policy_observation(
            decision_state["world"],
            occlusion=interventions["vision_mode"] == "canonical",
        )
    except ValueError as exc:
        raise EngineInvariantError(str(exc)) from exc
    predictive_belief_receipt: dict[str, Any] = {
        "applied": False,
        "reason": "predictive_control_off",
        "belief_hash_before": canonical_hash(
            decision_state["predictive_control"]["belief"]
        ),
        "belief_hash_after": canonical_hash(
            decision_state["predictive_control"]["belief"]
        ),
    }
    if interventions["predictive_control_mode"] == "factored_mpc":
        decision_state = dict(decision_state)
        try:
            (
                decision_state["predictive_control"],
                predictive_belief_receipt,
            ) = predictive_control.observe_belief(
                decision_state["predictive_control"],
                observation=world_observation,
                episode_index=int(decision_state["clock"]["episode_index"]),
                mode=interventions["relative_map_mode"],
            )
        except predictive_control.PredictiveControlInvariantError as exc:
            raise EngineInvariantError(str(exc)) from exc
        component_hashes = dict(decision_state["component_hashes"])
        component_hashes["predictive_control"] = canonical_hash(
            decision_state["predictive_control"]
        )
        decision_state["component_hashes"] = component_hashes
    decision_hash = state_hash(decision_state)
    observation_key = observation_hash(world_observation)
    goal_before = deepcopy(decision_state["current_goal"])
    current_goal = _goal_context_key(goal_before)
    context_key = f"{observation_key}|{current_goal}"
    _verify_model_access(
        decision_state["model"],
        context_key=context_key,
        observation_key=observation_key,
    )
    try:
        survival_state_key = survival_learning.build_state_key(
            observation_key,
            float(decision_state["organism"]["energy"]),
        )
    except survival_learning.SurvivalLearningInvariantError as exc:
        raise EngineInvariantError(str(exc)) from exc

    model_before_hash = str(decision_state["component_hashes"]["model"])
    memory_before_hash = str(decision_state["component_hashes"]["memory"])
    memory_view, provenance_projection = _memory_read_view(
        decision_state["memory"],
        source_memory_hash=memory_before_hash,
        memory_mode=interventions["memory_mode"],
        provenance_mode=interventions["provenance_mode"],
        provenance_shuffle_seed=int(interventions["provenance_shuffle_seed"]),
        consolidation_mode=interventions["consolidation_mode"],
    )
    claim_retrieval = claim_memory.retrieve_competing_claims(
        memory_view,
        observation=world_observation,
        current_goal=current_goal,
        prevalidated=True,
    )
    if interventions["memory_mode"] == "off":
        claim_retrieval["status"] = "memory_disabled"
    memory_summary = _policy_memory_summary(
        memory_view,
        cue=observation_key,
        current_goal=current_goal,
    )
    audited_memory_by_action = _memory_biases(
        memory_view,
        cue=observation_key,
        current_goal=current_goal,
    )
    claim_summary = deepcopy(claim_retrieval["policy_summary"])
    decision_policy_projection = {
        "schema_version": "ego.life_playground.policy_projection.v3",
        "observation": world_observation,
        "organism": decision_state["organism"],
        "current_goal": _sanitized_goal(goal_before),
        "model": decision_state["model"],
        "memory_summary": memory_summary,
        "claim_summary": claim_summary,
    }
    deterministic_ties = _deterministic_ties(decision_policy_projection)
    policy_decision_input_hash = canonical_hash(decision_policy_projection)
    model_access = {
        "component_hash": model_before_hash,
        "context_key": context_key,
        "entries_by_action": {
            action: deepcopy(
                decision_state["model"].get(context_key, {}).get(action)
            )
            for action in ACTIONS
        },
        "transition_counts": _transition_counts_for_observation(
            decision_state["model"], observation_key
        ),
    }
    policy_projection = {
        "schema_version": "ego.life_playground.policy_projection.v4",
        "observation": deepcopy(world_observation),
        "organism": deepcopy(decision_state["organism"]),
        "current_goal": _sanitized_goal(goal_before),
        "model_access": model_access,
        "memory_summary": memory_summary,
        "claim_summary": claim_summary,
        "decision_input_hash": policy_decision_input_hash,
    }
    candidates = [
        _score_candidate(
            organism=decision_state["organism"],
            model=decision_state["model"],
            memory_summary=memory_summary,
            claim_summary=claim_summary,
            observation=world_observation,
            context_key=context_key,
            current_goal=goal_before,
            action=action,
            deterministic_tie=deterministic_ties[action],
            novelty_mode=interventions["novelty_mode"],
        )
        for action in ACTIONS
    ]
    for candidate in candidates:
        action = str(candidate["action"])
        audit_bias, legacy_refs = audited_memory_by_action[action]
        if _round(audit_bias) != candidate["legacy_memory_bias"]:
            raise EngineInvariantError("policy memory summary differs from audited memory view")
        claim_refs = sorted(
            {
                str(event_id)
                for item in claim_retrieval.get("claims", [])
                if item.get("value") == action
                for event_id in item.get("eligible_provenance_event_ids", [])
            }
        )
        candidate["claim_refs"] = _reference_receipt(claim_refs)
        candidate["memory_refs"] = _reference_receipt(
            sorted(set(legacy_refs) | set(claim_refs))
        )
    candidates.sort(key=lambda item: item["action"])
    candidate_scores = {
        str(candidate["action"]): float(candidate["total_score"])
        for candidate in candidates
    }
    predictive_plan: dict[str, Any] | None = None
    selection_scores = candidate_scores
    selection_learning_mode = interventions["survival_learning_mode"]
    if interventions["predictive_control_mode"] == "factored_mpc":
        active_goal = _goal_context_key(goal_before)
        try:
            predictive_plan = predictive_control.plan_action(
                state=decision_state["predictive_control"],
                observation=world_observation,
                organism=decision_state["organism"],
                active_goal=active_goal,
                heuristic_scores=candidate_scores,
                horizon=(
                    predictive_control.HORIZON
                    if interventions["predictive_horizon_mode"] == "h12"
                    else 1
                ),
                beam_width=predictive_control.BEAM_WIDTH,
                discount=predictive_control.DISCOUNT,
                relative_map_mode=interventions["relative_map_mode"],
                goal_value_mode=interventions["goal_value_mode"],
                action_costs=ACTION_COSTS,
                run_seed=int(run_meta["seed"]),
                episode_index=int(decision_state["clock"]["episode_index"]),
                sequence=sequence,
            )
            # The existing survival selector remains the sole downstream
            # action-selection receipt.  In factored mode its score surface is
            # a delegation receipt for the plan's bounded-explore/MPC choice;
            # the unmodified expected values remain in predictive_plan.
            selection_scores = {
                action: 1.0 if action == predictive_plan["selected_action"] else 0.0
                for action in ACTIONS
            }
            selection_learning_mode = "off"
        except predictive_control.PredictiveControlInvariantError as exc:
            raise EngineInvariantError(str(exc)) from exc
    try:
        selected_action, survival_selection = survival_learning.select_action(
            decision_state["survival_learner"],
            state_key=survival_state_key,
            candidate_scores=selection_scores,
            run_seed=int(run_meta["seed"]),
            episode_index=int(decision_state["clock"]["episode_index"]),
            sequence=sequence,
            life_index=int(lifecycle_before["life_index"]),
            mode=selection_learning_mode,
        )
    except survival_learning.SurvivalLearningInvariantError as exc:
        raise EngineInvariantError(str(exc)) from exc
    if predictive_plan is not None:
        if selected_action != str(predictive_plan["selected_action"]):
            raise EngineInvariantError(
                "predictive plan and deterministic selection receipt differ"
            )
        survival_selection["selection_mode"] = "delegated_factored_mpc"
    selected = next(
        candidate for candidate in candidates if candidate["action"] == selected_action
    )
    for candidate in candidates:
        candidate["survival_q"] = survival_selection["q_by_action"][
            candidate["action"]
        ]
        candidate["selected"] = candidate["action"] == selected_action
    predicted_delta = deepcopy(selected["predicted_delta"])

    next_state = dict(decision_state)
    try:
        next_state["world"], world_transition = transition_world(
            decision_state["world"],
            selected_action,
            source_sequence=sequence,
            source_episode_id=str(decision_state["clock"]["episode_id"]),
            source_command_hash=str(command["command_hash"]),
        )
    except ValueError as exc:
        raise EngineInvariantError(str(exc)) from exc
    actual_delta = compute_actual_delta(
        world_transition,
        selected_action=selected_action,
    )
    energy_before = _round(float(decision_state["organism"]["energy"]))
    metabolism = compute_metabolism_ledger(
        energy_before=energy_before,
        selected_action=selected_action,
        world_before=decision_state["world"],
        world_after=next_state["world"],
        world_transition=world_transition,
        run_meta=run_meta,
        episode_id=str(decision_state["clock"]["episode_id"]),
        command_hash=str(command["command_hash"]),
        code_path_hash=current_code_hash,
    )
    actual_delta["energy"] = metabolism["energy_delta"]
    prediction_error = {
        key: _round(actual_delta[key] - predicted_delta[key]) for key in STATE_KEYS
    }
    next_state["organism"] = _apply_delta(decision_state["organism"], actual_delta)
    if next_state["organism"]["energy"] != metabolism["energy_after"]:
        raise EngineInvariantError("metabolism ledger differs from applied organism energy")
    next_state["last_action"] = selected_action
    next_state["last_command_hash"] = command["command_hash"]
    next_observation = policy_observation(
        next_state["world"],
        occlusion=interventions["vision_mode"] == "canonical",
    )
    next_observation_hash = observation_hash(next_observation)
    next_state["current_goal"], goal_progress, goal_transition = _advance_goal(
        goal_before,
        before_organism=decision_state["organism"],
        after_organism=next_state["organism"],
        global_tick=sequence,
        interventions=interventions,
        observation_key=observation_key,
        model=decision_state["model"],
    )

    life_termination = None
    if next_state["organism"]["energy"] == 0.0:
        life_termination = _life_result(
            life_index=int(lifecycle_before["life_index"]),
            survival_ticks=int(next_state["clock"]["episode_tick"]),
            censored=False,
            termination="death",
        )
    elif int(next_state["clock"]["episode_tick"]) == EPISODE_SPAN_TICKS:
        life_termination = _life_result(
            life_index=int(lifecycle_before["life_index"]),
            survival_ticks=EPISODE_SPAN_TICKS,
            censored=True,
            termination="censored",
        )

    predictive_update: dict[str, Any] = {
        "schema_version": predictive_control.UPDATE_SCHEMA_VERSION,
        "producer_function": (
            "ego_life_playground_v0.predictive_control.update_after_transition"
        ),
        "applied": False,
        "reason": "predictive_control_off",
        "model_hash_before": canonical_hash(
            decision_state["predictive_control"]["model"]
        ),
        "model_hash_after": canonical_hash(
            decision_state["predictive_control"]["model"]
        ),
        "belief_hash_after": canonical_hash(
            decision_state["predictive_control"]["belief"]
        ),
        "update_count_after": int(
            decision_state["predictive_control"]["model"]["update_count"]
        ),
    }
    if interventions["predictive_control_mode"] == "factored_mpc":
        try:
            (
                next_state["predictive_control"],
                predictive_update,
            ) = predictive_control.update_after_transition(
                decision_state["predictive_control"],
                observation=world_observation,
                organism_before=decision_state["organism"],
                action=selected_action,
                actual_outcome_type=str(world_transition["outcome_type"]),
                actual_delta=actual_delta,
                terminal=life_termination is not None,
                resource_interaction=float(metabolism["food_gain"]) > 0.0,
                next_observation=next_observation,
                episode_index=int(decision_state["clock"]["episode_index"]),
                relative_map_mode=interventions["relative_map_mode"],
                updates_enabled=interventions["update_mode"] == "canonical",
            )
        except predictive_control.PredictiveControlInvariantError as exc:
            raise EngineInvariantError(str(exc)) from exc
        component_hashes = dict(next_state["component_hashes"])
        component_hashes["predictive_control"] = canonical_hash(
            next_state["predictive_control"]
        )
        next_state["component_hashes"] = component_hashes

    try:
        next_survival_state_key = survival_learning.build_state_key(
            next_observation_hash,
            float(next_state["organism"]["energy"]),
        )
        next_state["survival_learner"], survival_update = (
            survival_learning.update_expected_sarsa_lambda(
                decision_state["survival_learner"],
                state_key=survival_state_key,
                action=selected_action,
                reward=1.0 if float(next_state["organism"]["energy"]) > 0.0 else 0.0,
                next_state_key=next_survival_state_key,
                next_candidate_scores=candidate_scores,
                next_life_index=int(lifecycle_before["life_index"]),
                terminal=life_termination is not None,
                updates_enabled=(
                    interventions["survival_learning_mode"]
                    == survival_learning.ALGORITHM
                    and interventions["update_mode"] == "canonical"
                ),
            )
        )
    except survival_learning.SurvivalLearningInvariantError as exc:
        raise EngineInvariantError(str(exc)) from exc
    if interventions["survival_learning_mode"] == "off":
        if life_termination is not None and interventions["update_mode"] == "canonical":
            next_state["survival_learner"] = (
                survival_learning.clear_eligibility_for_respawn(
                    next_state["survival_learner"]
                )
            )
            survival_update.update(
                {
                    "reason": "survival_learning_off_terminal_reset",
                    "eligibility_reset_applied": True,
                    "q_table_hash_after": survival_learning.q_table_hash(
                        next_state["survival_learner"]
                    ),
                    "eligibility_hash_after": survival_learning.eligibility_hash(
                        next_state["survival_learner"]
                    ),
                    "learner_hash_after": survival_learning.learner_state_hash(
                        next_state["survival_learner"]
                    ),
                }
            )
        else:
            survival_update["reason"] = "survival_learning_off"
            survival_update["eligibility_reset_applied"] = False

    updates_enabled = interventions["update_mode"] == "canonical"
    model_update = _update_model(
        next_state,
        context_key=context_key,
        action=selected_action,
        prediction_before=predicted_delta,
        actual_delta=actual_delta,
        apply_update=updates_enabled,
        observation_key=observation_key,
        next_observation_hash=next_observation_hash,
    )
    goal_progress["novelty_counter_hash_after"] = canonical_hash(
        _transition_counts_for_observation(next_state["model"], observation_key)
    )
    goal_progress["novelty_transition_update"] = deepcopy(
        model_update["visual_transition_update"]
    )
    memory_update = _update_memory(
        next_state,
        before_organism=decision_state["organism"],
        after_organism=next_state["organism"],
        actual_delta=actual_delta,
        cue=observation_key,
        current_goal=current_goal,
        action=selected_action,
        sequence=sequence,
        command_hash=str(command["command_hash"]),
        source_episode_id=str(decision_state["clock"]["episode_id"]),
        memory_enabled=interventions["memory_mode"] == "canonical",
        updates_enabled=updates_enabled,
    )
    claim_update = _update_claim_memory(
        next_state,
        observation=world_observation,
        current_goal=current_goal,
        action=selected_action,
        actual_delta=actual_delta,
        sequence=sequence,
        command_hash=str(command["command_hash"]),
        source_episode_id=str(decision_state["clock"]["episode_id"]),
        memory_enabled=interventions["memory_mode"] == "canonical",
        updates_enabled=updates_enabled,
    )
    _advance_memory_component_hash(
        next_state,
        previous_hash=memory_before_hash,
        memory_update=memory_update,
        claim_update=claim_update,
    )
    model_after_hash = str(next_state["component_hashes"]["model"])
    memory_after_hash = str(next_state["component_hashes"]["memory"])
    if life_termination is None:
        next_state["lifecycle"] = deepcopy(lifecycle_before)
    else:
        life_results = deepcopy(lifecycle_before["life_results"])
        life_results.append(life_termination)
        if int(lifecycle_before["life_index"]) < MAX_LIVES:
            next_state["lifecycle"] = {
                "trial_status": "awaiting_respawn",
                "life_index": int(lifecycle_before["life_index"]),
                "awaiting_respawn": True,
                "life_results": life_results,
                "terminal_life_result": None,
            }
        else:
            next_state["lifecycle"] = {
                "trial_status": "terminal",
                "life_index": MAX_LIVES,
                "awaiting_respawn": False,
                "life_results": life_results,
                "terminal_life_result": {
                    "survival_ticks": min(int(life_termination["survival_ticks"]), EPISODE_SPAN_TICKS),
                    "censored": bool(life_termination["censored"]),
                },
            }

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
        "aggregation_rule": run_meta["aggregation_rule"],
        "sequence": sequence,
        "trigger_source": command["trigger_source"],
        "injected_event": injected_event,
        "interventions": interventions,
        "command": deepcopy(dict(command)),
        "command_hash": command["command_hash"],
        "prev_command_hash": command["prev_command_hash"],
        "state_before_hash": before_hash,
        "decision_state_hash": decision_hash,
        "state_after_hash": after_hash,
        "world_before_hash": world_hash(world_before),
        "world_decision_hash": world_hash(decision_state["world"]),
        "world_after_hash": world_hash(next_state["world"]),
        "observation": world_observation,
        "observation_hash": observation_hash(world_observation),
        "policy_projection": policy_projection,
        "policy_projection_hash": canonical_hash(policy_projection),
        "candidate_actions": list(ACTIONS),
        "world_transition": world_transition,
        "episode_transition": episode_transition,
        "action_episode": deepcopy(decision_state["clock"]),
        "goal_before": goal_before,
        "goal_progress": goal_progress,
        "goal_transition": goal_transition,
        "goal_after": deepcopy(next_state["current_goal"]),
        "context_key": context_key,
        "candidates": candidates,
        "selected_action": selected_action,
        "prediction": predicted_delta,
        "model_ref": selected["model_ref"],
        "memory_refs": selected["memory_refs"],
        "claim_retrieval": _compact_claim_retrieval(claim_retrieval),
        "actual_delta": actual_delta,
        "energy_before": metabolism["energy_before"],
        "passive_decay": metabolism["passive_decay"],
        "action_cost": metabolism["action_cost"],
        "food_gain": metabolism["food_gain"],
        "energy_after": metabolism["energy_after"],
        "downstream_effect": metabolism["downstream_effect"],
        "metabolism": metabolism,
        "prediction_error": prediction_error,
        "model_update": model_update,
        "memory_update": _compact_memory_update(memory_update),
        "claim_update": _compact_claim_update(claim_update),
        "survival_learning": {
            "schema_version": "ego.life_playground.survival_trace.v1",
            "producer_function": RUN_PRODUCER_FUNCTION,
            "state_key_inputs": {
                "policy_observation_hash": observation_key,
                "energy_milli": round(
                    float(decision_state["organism"]["energy"]) * 1000
                ),
            },
            "state_key": survival_state_key,
            "next_state_key": next_survival_state_key,
            "selection": survival_selection,
            "update": survival_update,
            "successful_resource_interaction": (
                world_transition.get("outcome_type") == "interacted"
                and world_transition.get("cause") == "resource"
            ),
            "learner_hash_after": survival_learning.learner_state_hash(
                next_state["survival_learner"]
            ),
            "q_table_size": survival_learning.q_table_size(
                next_state["survival_learner"]
            ),
            "update_count": int(next_state["survival_learner"]["update_count"]),
        },
        "predictive_control": {
            "schema_version": "ego.life_playground.predictive_control_trace.v4",
            "mode": interventions["predictive_control_mode"],
            "belief_observation": predictive_belief_receipt,
            "belief_hash": canonical_hash(
                next_state["predictive_control"]["belief"]
            ),
            "model_hash": canonical_hash(
                next_state["predictive_control"]["model"]
            ),
            "exploration_hash": canonical_hash(
                next_state["predictive_control"]["exploration"]
            ),
            "model_update_count": int(
                next_state["predictive_control"]["model"]["update_count"]
            ),
            "plan": _compact_predictive_plan(predictive_plan),
            "update": _compact_predictive_update(predictive_update),
        },
        "model_bytes": {
            "before_hash": model_before_hash,
            "after_hash": model_after_hash,
            "changed": model_before_hash != model_after_hash,
        },
        "memory_bytes": {
            "before_hash": memory_before_hash,
            "after_hash": memory_after_hash,
            "changed": memory_before_hash != memory_after_hash,
        },
        "consolidation_refs": _reference_receipt(
            memory_update["consolidation_refs"]
        ),
        "provenance_projection": _compact_provenance_projection(
            provenance_projection
        ),
        "vision_ablation": {
            "mode": interventions["vision_mode"],
            "applied": interventions["vision_mode"] != "canonical",
        },
        "code_path_hash": current_code_hash,
        "prev_trace_hash": before.get("last_trace_hash"),
        "transition_kind": "action",
        "policy_invoked": True,
        "lifecycle_before": lifecycle_before,
        "lifecycle_after": deepcopy(next_state["lifecycle"]),
        "life_termination": life_termination,
        "carry_reset_receipt": None,
    }
    trace["trace_hash"] = compute_trace_hash(trace)
    next_state["last_trace_hash"] = trace["trace_hash"]
    return StepResult(next_state=next_state, trace=trace)


def compute_metabolism_ledger(
    *,
    energy_before: float,
    selected_action: str,
    world_before: Mapping[str, Any],
    world_after: Mapping[str, Any],
    world_transition: Mapping[str, Any],
    run_meta: Mapping[str, Any],
    episode_id: str,
    command_hash: str,
    code_path_hash: str,
) -> dict[str, Any]:
    if type(energy_before) is not float or not math.isfinite(energy_before):
        raise EngineInvariantError("metabolism energy_before must be a finite float")
    if not 0.0 <= energy_before <= 1.0:
        raise EngineInvariantError("metabolism energy_before is outside range")
    if selected_action not in ACTIONS:
        raise EngineInvariantError("metabolism selected action is not canonical")
    if not isinstance(world_before, Mapping) or not isinstance(world_after, Mapping):
        raise EngineInvariantError("metabolism world states must be objects")
    if not isinstance(world_transition, Mapping):
        raise EngineInvariantError("metabolism world transition must be an object")
    _verify_metabolism_world_transition(
        selected_action,
        world_before=world_before,
        world_after=world_after,
        world_transition=world_transition,
    )
    if type(episode_id) is not str or not episode_id:
        raise EngineInvariantError("metabolism episode_id must be non-empty")
    if not _is_sha256(command_hash) or not _is_sha256(code_path_hash):
        raise EngineInvariantError("metabolism provenance hashes must be sha256")

    passive_decay = PASSIVE_ENERGY_DECAY_PER_TICK
    action_cost = ACTION_COSTS[selected_action]
    food_gain = (
        CAUSE_DELTAS["resource"]["energy"]
        if world_transition["outcome_type"] == "interacted"
        and world_transition["cause"] == "resource"
        else 0.0
    )
    energy_after = _round(
        _clamp(energy_before - passive_decay - action_cost + food_gain)
    )
    downstream_effect = {
        "producer_function": METABOLISM_PRODUCER_FUNCTION,
        "effect": "passive_and_action_cost_applied",
    }
    return {
        "schema_version": "ego.life_playground.metabolism_ledger.v1",
        "producer_function": METABOLISM_PRODUCER_FUNCTION,
        "input_artifacts": [
            f"run:{run_meta['run_id']}",
            f"command:{command_hash}",
            f"world_before:{world_hash(world_before)}",
            f"world_after:{world_hash(world_after)}",
            f"world_transition:{canonical_hash(world_transition)}",
        ],
        "run_id": run_meta["run_id"],
        "seed": int(run_meta["seed"]),
        "episode_id": episode_id,
        "aggregation_rule": METABOLISM_AGGREGATION_RULE,
        "code_path_hash": code_path_hash,
        "selected_action": selected_action,
        "food_obtained": bool(food_gain > 0.0),
        "energy_before": energy_before,
        "passive_decay": passive_decay,
        "action_cost": action_cost,
        "food_gain": food_gain,
        "energy_after": energy_after,
        "energy_delta": _round(energy_after - energy_before),
        "downstream_effect": downstream_effect,
    }


def _verify_metabolism_world_transition(
    selected_action: str,
    *,
    world_before: Mapping[str, Any],
    world_after: Mapping[str, Any],
    world_transition: Mapping[str, Any],
) -> None:
    """Recompute the action transition so cause/token/location cannot be forged."""

    try:
        verify_world_state(world_before)
        verify_world_state(world_after)
        expected_world, expected_transition = transition_world(
            world_before,
            selected_action,
        )
    except ValueError as exc:
        raise EngineInvariantError(str(exc)) from exc
    if canonical_json(expected_transition) != canonical_json(world_transition):
        raise EngineInvariantError(
            "metabolism world transition does not match the selected action"
        )
    if canonical_json(expected_world) != canonical_json(world_after):
        raise EngineInvariantError(
            "metabolism world-after state does not match the selected action"
        )


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
        "max_lives",
        "survival_learning",
        "default_survival_learning_mode",
        "predictive_control",
        "default_predictive_control_mode",
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
        raise EngineInvariantError("episode_span_ticks is frozen at 256")
    if type(run_meta["max_lives"]) is not int or run_meta["max_lives"] != MAX_LIVES:
        raise EngineInvariantError("max_lives must match the fixed product lifecycle")
    if canonical_json(run_meta["survival_learning"]) != canonical_json(
        survival_learning.hyperparameters()
    ):
        raise EngineInvariantError("survival learning metadata mismatch")
    if run_meta["default_survival_learning_mode"] != "off":
        raise EngineInvariantError("survival learner default must remain off before acceptance")
    if canonical_json(run_meta["predictive_control"]) != canonical_json(
        predictive_control.hyperparameters()
    ):
        raise EngineInvariantError("predictive control metadata mismatch")
    if run_meta["default_predictive_control_mode"] != "off":
        raise EngineInvariantError("predictive control default must remain off")
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
        "world",
        "current_goal",
        "model",
        "memory",
        "component_hashes",
        "survival_learner",
        "predictive_control",
        "lifecycle",
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
    component_hashes = state["component_hashes"]
    if (
        not isinstance(component_hashes, Mapping)
        or set(component_hashes)
        != {"schema_version", "model", "memory", "predictive_control"}
        or component_hashes.get("schema_version") != COMPONENT_HASH_SCHEMA_VERSION
        or not _is_sha256(component_hashes.get("model"))
        or not _is_sha256(component_hashes.get("memory"))
        or not _is_sha256(component_hashes.get("predictive_control"))
    ):
        raise EngineInvariantError("component hash schema mismatch")
    if tick == 0 and (
        component_hashes["model"] != canonical_hash(state["model"])
        or component_hashes["memory"] != canonical_hash(state["memory"])
        or component_hashes["predictive_control"]
        != canonical_hash(state["predictive_control"])
    ):
        raise EngineInvariantError("initial component hash mismatch")
    lifecycle = state["lifecycle"]
    _verify_lifecycle(lifecycle)
    expected_index = int(lifecycle["life_index"]) - 1
    if clock["episode_index"] != expected_index:
        raise EngineInvariantError("episode_index does not match life_index")
    if clock["episode_id"] != episode_id_for(run_id, expected_index):
        raise EngineInvariantError("episode_id does not match run and life_index")
    if int(state["world"]["trial"]["life_index"]) != int(lifecycle["life_index"]):
        raise EngineInvariantError("world life_index does not match lifecycle")
    completed_tick_sum = sum(int(item["survival_ticks"]) for item in lifecycle["life_results"])
    completed_respawns = int(lifecycle["life_index"]) - 1
    episode_tick = int(clock["episode_tick"])
    if lifecycle["trial_status"] == "active":
        if not 0 <= episode_tick <= EPISODE_SPAN_TICKS - 1:
            raise EngineInvariantError("active episode_tick must be within 0..255")
        expected_global_tick = completed_tick_sum + completed_respawns + episode_tick
    else:
        latest_survival = int(lifecycle["life_results"][-1]["survival_ticks"])
        if episode_tick != latest_survival:
            raise EngineInvariantError("terminal/awaiting episode_tick must equal latest recorded survival")
        expected_global_tick = completed_tick_sum + completed_respawns
    if tick != expected_global_tick:
        raise EngineInvariantError("global_tick does not match lifecycle command-count equation")

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
    if lifecycle["trial_status"] == "active" and organism["energy"] <= 0.0:
        raise EngineInvariantError("active lifecycle requires positive energy")
    if lifecycle["trial_status"] != "active":
        latest_termination = lifecycle["life_results"][-1]["termination"]
        if latest_termination == "death" and organism["energy"] != 0.0:
            raise EngineInvariantError("death terminal/awaiting lifecycle requires zero energy")
        if latest_termination == "censored" and organism["energy"] <= 0.0:
            raise EngineInvariantError("censored terminal/awaiting lifecycle requires positive energy")

    try:
        verify_world_state(state["world"])
    except ValueError as exc:
        raise EngineInvariantError(str(exc)) from exc

    _verify_goal(state["current_goal"], global_tick=tick)
    _verify_model(state["model"], full=tick == 0)
    _verify_memory(state["memory"])
    try:
        survival_learning.validate_survival_learner(state["survival_learner"])
    except survival_learning.SurvivalLearningInvariantError as exc:
        raise EngineInvariantError(str(exc)) from exc
    try:
        predictive_control.validate_state(state["predictive_control"])
    except predictive_control.PredictiveControlInvariantError as exc:
        raise EngineInvariantError(str(exc)) from exc
    if tick == 0 and canonical_json(state["survival_learner"]) != canonical_json(
        survival_learning.empty_survival_learner()
    ):
        raise EngineInvariantError("initial survival learner must be empty")

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
            if lifecycle["trial_status"] != "active" or int(clock["episode_tick"]) != 0:
                raise EngineInvariantError("last_action may be null only for active life start/respawn")
        elif type(last_action) is not str or last_action not in ACTIONS:
            raise EngineInvariantError("last_action is not canonical")
        if last_command_hash is None:
            raise EngineInvariantError("last_command_hash must be non-null after the initial clock")
        if not _is_sha256(last_command_hash):
            raise EngineInvariantError("last_command_hash must be sha256")
        if last_trace_hash is None:
            raise EngineInvariantError("last_trace_hash must be non-null after the initial clock")
        if not _is_sha256(last_trace_hash):
            raise EngineInvariantError("last_trace_hash must be sha256")
    if last_action is None and episode_tick != 0:
        raise EngineInvariantError("episode_tick must be zero when last_action is null")
    if last_action is not None:
        max_episode_tick = EPISODE_SPAN_TICKS - 1 if lifecycle["trial_status"] == "active" else EPISODE_SPAN_TICKS
        if not 1 <= episode_tick <= max_episode_tick:
            raise EngineInvariantError("episode_tick must be within the lifecycle-allowed range")


def _verify_model(model: Any, *, full: bool = True) -> None:
    if not isinstance(model, Mapping):
        raise EngineInvariantError("model must be an object")
    if type(full) is not bool:
        raise EngineInvariantError("model full verification flag must be boolean")
    if not full:
        transition_counts = model.get(VISUAL_TRANSITION_MODEL_KEY, {})
        if not isinstance(transition_counts, Mapping):
            raise EngineInvariantError("visual transition counts must be an object")
        return
    for context_key, actions in model.items():
        if context_key == VISUAL_TRANSITION_MODEL_KEY:
            _verify_visual_transition_counts(actions)
            continue
        if type(context_key) is not str or context_key.count("|") != 1:
            raise EngineInvariantError("model context key is not canonical")
        observation_key, goal = context_key.split("|", 1)
        if not _is_sha256(observation_key) or goal not in {*STATE_KEYS, "explore"}:
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


def _verify_model_access(
    model: Mapping[str, Any], *, context_key: str, observation_key: str
) -> None:
    """Validate only model rows that can affect this decision."""

    accessed: dict[str, Any] = {}
    if context_key in model:
        accessed[context_key] = model[context_key]
    visual = model.get(VISUAL_TRANSITION_MODEL_KEY, {})
    if isinstance(visual, Mapping) and observation_key in visual:
        accessed[VISUAL_TRANSITION_MODEL_KEY] = {
            observation_key: visual[observation_key]
        }
    _verify_model(accessed, full=True)


def _verify_memory(memory: Any) -> None:
    if not isinstance(memory, Mapping) or set(memory) != {
        "schema_version",
        "episodic",
        "consolidated",
        "claim_events",
        "competing_claims",
    }:
        raise EngineInvariantError("memory schema mismatch")
    episodic = memory["episodic"]
    consolidated = memory["consolidated"]
    if not isinstance(episodic, list):
        raise EngineInvariantError("episodic memory must be a list")
    if not isinstance(consolidated, list):
        raise EngineInvariantError("consolidated memory must be a list")
    # The reducer appends exactly one immutable row.  Startup/recovery begins
    # from an empty validated initial state and recomputes all prior rows, so
    # the hot path validates the append boundary rather than rescanning the
    # complete history on every tick.
    if episodic:
        _verify_episodic_memory_entry(episodic[-1])
    memory_ids: set[str] = {
        str(episodic[-1]["memory_id"])
    } if episodic else set()
    for entry in consolidated:
        _verify_consolidated_memory_entry(entry)
        memory_id = str(entry["memory_id"])
        if memory_id in memory_ids:
            raise EngineInvariantError("memory_id must be unique")
        memory_ids.add(memory_id)
    try:
        claim_memory.verify_claim_memory(memory, full=False)
    except ValueError as exc:
        raise EngineInvariantError(str(exc)) from exc


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
    if type(entry["cue"]) is not str or not _is_sha256(entry["cue"]):
        raise EngineInvariantError(f"{label} cue is not canonical")
    if type(entry["current_goal"]) is not str or entry["current_goal"] not in {
        *STATE_KEYS,
        "explore",
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


def _empty_completed_latches() -> dict[str, bool]:
    return {key: False for key in STATE_KEYS}


def _verify_completed_latches(value: Any) -> None:
    if not isinstance(value, Mapping) or set(value) != set(STATE_KEYS):
        raise EngineInvariantError("completed_latches schema mismatch")
    for key in STATE_KEYS:
        if type(value[key]) is not bool:
            raise EngineInvariantError("completed_latches values must be booleans")


def _verify_visual_transition_counts(value: Any) -> None:
    if not isinstance(value, Mapping):
        raise EngineInvariantError("visual transition counts must be an object")
    for observation_key, by_action in value.items():
        if not _is_sha256(observation_key):
            raise EngineInvariantError("visual transition observation key must be sha256")
        if not isinstance(by_action, Mapping):
            raise EngineInvariantError("visual transition action table must be an object")
        for action, entry in by_action.items():
            if action not in ACTIONS or not isinstance(entry, Mapping):
                raise EngineInvariantError("visual transition action entry is not canonical")
            if set(entry) != {"total", "next_counts"}:
                raise EngineInvariantError("visual transition entry schema mismatch")
            total = entry["total"]
            next_counts = entry["next_counts"]
            if type(total) is not int or total < 0:
                raise EngineInvariantError("visual transition total must be a non-negative integer")
            if not isinstance(next_counts, Mapping):
                raise EngineInvariantError("visual transition next_counts must be an object")
            rebuilt_total = 0
            for next_observation_hash, count in next_counts.items():
                if not _is_sha256(next_observation_hash):
                    raise EngineInvariantError("visual transition next observation hash must be sha256")
                if type(count) is not int or count <= 0:
                    raise EngineInvariantError("visual transition next observation count must be positive")
                rebuilt_total += count
            if rebuilt_total != total:
                raise EngineInvariantError("visual transition total must match next_counts sum")


def _verify_lifecycle(lifecycle: Any) -> None:
    required = {
        "trial_status",
        "life_index",
        "awaiting_respawn",
        "life_results",
        "terminal_life_result",
    }
    if not isinstance(lifecycle, Mapping) or set(lifecycle) != required:
        raise EngineInvariantError("lifecycle schema mismatch")
    if lifecycle["trial_status"] not in {"active", "awaiting_respawn", "terminal"}:
        raise EngineInvariantError("lifecycle trial_status is not canonical")
    if type(lifecycle["life_index"]) is not int or not 1 <= lifecycle["life_index"] <= MAX_LIVES:
        raise EngineInvariantError("lifecycle life_index must be within max_lives")
    if type(lifecycle["awaiting_respawn"]) is not bool:
        raise EngineInvariantError("lifecycle awaiting_respawn must be boolean")
    if lifecycle["awaiting_respawn"] != (lifecycle["trial_status"] == "awaiting_respawn"):
        raise EngineInvariantError("lifecycle awaiting_respawn does not match trial_status")
    results = lifecycle["life_results"]
    if not isinstance(results, list):
        raise EngineInvariantError("lifecycle life_results must be a list")
    for expected_life_index, item in enumerate(results, start=1):
        if not isinstance(item, Mapping) or set(item) != {
            "life_index",
            "survival_ticks",
            "censored",
            "termination",
        }:
            raise EngineInvariantError("life result schema mismatch")
        if item["life_index"] != expected_life_index:
            raise EngineInvariantError("life results must be ordered by life_index")
        if type(item["survival_ticks"]) is not int or not 1 <= item["survival_ticks"] <= EPISODE_SPAN_TICKS:
            raise EngineInvariantError("life result survival_ticks must be within one life")
        if type(item["censored"]) is not bool:
            raise EngineInvariantError("life result censored must be boolean")
        if item["termination"] not in {"death", "censored"}:
            raise EngineInvariantError("life result termination is not canonical")
        if item["censored"] != (item["termination"] == "censored"):
            raise EngineInvariantError("life result censor flag does not match termination")
    if lifecycle["trial_status"] == "active" and len(results) != lifecycle["life_index"] - 1:
        raise EngineInvariantError("active lifecycle must have completed prior lives only")
    if lifecycle["trial_status"] == "awaiting_respawn" and len(results) != lifecycle["life_index"]:
        raise EngineInvariantError("awaiting_respawn lifecycle must include current life result")
    if lifecycle["trial_status"] == "terminal" and len(results) != MAX_LIVES:
        raise EngineInvariantError("terminal lifecycle must include exactly max_lives results")
    terminal_result = lifecycle["terminal_life_result"]
    if terminal_result is None:
        if lifecycle["trial_status"] == "terminal":
            raise EngineInvariantError("terminal lifecycle requires terminal_life_result")
        return
    if lifecycle["trial_status"] != "terminal":
        raise EngineInvariantError("terminal_life_result is only allowed for terminal lifecycle")
    if not isinstance(terminal_result, Mapping) or set(terminal_result) != {"survival_ticks", "censored"}:
        raise EngineInvariantError("terminal_life_result schema mismatch")
    if type(terminal_result["survival_ticks"]) is not int or not 1 <= terminal_result["survival_ticks"] <= EPISODE_SPAN_TICKS:
        raise EngineInvariantError("terminal_life_result survival_ticks must be within one life")
    if type(terminal_result["censored"]) is not bool:
        raise EngineInvariantError("terminal_life_result censored must be boolean")
    if not results:
        raise EngineInvariantError("terminal_life_result requires recorded life results")
    last = results[-1]
    if last["life_index"] != MAX_LIVES:
        raise EngineInvariantError("terminal_life_result requires the final life record")
    if terminal_result["survival_ticks"] != min(int(last["survival_ticks"]), EPISODE_SPAN_TICKS):
        raise EngineInvariantError("terminal_life_result survival_ticks mismatch")
    if terminal_result["censored"] != bool(last["censored"]):
        raise EngineInvariantError("terminal_life_result censored mismatch")


def _verify_goal(goal: Mapping[str, Any], *, global_tick: int) -> None:
    required = {
        "state_variable",
        "target",
        "selected_global_tick",
        "entry_deficit",
        "status",
        "selection_reason",
        "completed_latches",
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
    if goal["status"] not in {"active", "explore"}:
        raise EngineInvariantError("current_goal status is not canonical")
    if goal["selection_reason"] not in GOAL_SELECTION_REASONS:
        raise EngineInvariantError("current_goal selection_reason is not canonical")
    _verify_completed_latches(goal["completed_latches"])
    if goal["status"] == "active" and goal["state_variable"] not in STATE_KEYS:
        raise EngineInvariantError("active current_goal state variable is not canonical")
    if goal["status"] == "active" and goal["selection_reason"] not in ACTIVE_GOAL_SELECTION_REASONS:
        raise EngineInvariantError("active current_goal selection_reason is not canonical")
    if goal["status"] == "active" and goal["entry_deficit"] <= 0.0:
        raise EngineInvariantError("active current_goal entry_deficit must be positive")
    if goal["status"] == "active" and goal["completed_latches"][goal["state_variable"]]:
        raise EngineInvariantError("active current_goal cannot also be completed-latched")
    if goal["status"] == "explore" and goal["state_variable"] is not None:
        raise EngineInvariantError("explore current_goal must have null state variable")
    if goal["status"] == "explore" and goal["selection_reason"] != "explore_no_eligible_body_goal":
        raise EngineInvariantError("explore current_goal selection_reason is not canonical")
    if goal["status"] == "explore" and goal["entry_deficit"] != 0.0:
        raise EngineInvariantError("explore current_goal entry_deficit must be zero")


def _decision_state_for_tick(
    before: Mapping[str, Any], *, run_id: str, sequence: int
) -> tuple[dict[str, Any], dict[str, Any]]:
    life_index = int(before["lifecycle"]["life_index"])
    episode_index = life_index - 1
    episode_tick = int(before["clock"]["episode_tick"]) + 1
    decision = dict(before)
    decision["clock"] = {
        "global_tick": sequence,
        "episode_index": episode_index,
        "episode_id": episode_id_for(run_id, episode_index),
        "episode_tick": episode_tick,
    }
    carry_checks = {
        "organism_unchanged": before["organism"] is decision["organism"],
        "model_unchanged": before["model"] is decision["model"],
        "memory_unchanged": before["memory"] is decision["memory"],
        "survival_learner_unchanged": before["survival_learner"]
        is decision["survival_learner"],
        "predictive_control_unchanged": before["predictive_control"]
        is decision["predictive_control"],
        "current_goal_unchanged": before["current_goal"] is decision["current_goal"],
        "command_chain_unchanged": before.get("last_command_hash")
        == decision.get("last_command_hash"),
        "trace_chain_unchanged": before.get("last_trace_hash") == decision.get("last_trace_hash"),
    }
    return decision, {
        "applied": False,
        "from_episode_index": int(before["clock"]["episode_index"]),
        "to_episode_index": episode_index,
        "rollover_global_tick": None,
        "carry_checks": carry_checks,
    }


def _select_goal(
    organism: Mapping[str, float], *, global_tick: int, reason: str, completed_latches: Mapping[str, bool]
) -> dict[str, Any]:
    latches = _normalize_completed_latches(completed_latches)
    candidates = _eligible_goal_candidates(organism, latches)
    if not candidates:
        return {
            "state_variable": None,
            "target": TARGET_LEVEL,
            "selected_global_tick": int(global_tick),
            "entry_deficit": 0.0,
            "status": "explore",
            "selection_reason": "explore_no_eligible_body_goal",
            "completed_latches": latches,
        }
    state_variable = candidates[0]["state_variable"]
    deficit = candidates[0]["deficit"]
    return {
        "state_variable": state_variable,
        "target": TARGET_LEVEL,
        "selected_global_tick": int(global_tick),
        "entry_deficit": _round(deficit),
        "status": "active",
        "selection_reason": reason,
        "completed_latches": latches,
    }


def _select_initial_goal(
    organism: Mapping[str, float], *, global_tick: int
) -> dict[str, Any]:
    latches = {
        key: float(organism[key]) >= TARGET_LEVEL for key in STATE_KEYS
    }
    override = _critical_override_candidate(organism)
    if override is not None:
        reason = (
            "critical_override_energy"
            if override == "energy"
            else "critical_override_body_deficit"
        )
        return _goal_record(
            override,
            organism,
            global_tick=global_tick,
            reason=reason,
            completed_latches=latches,
        )
    return _select_goal(
        organism,
        global_tick=global_tick,
        reason="initial_deficit_priority",
        completed_latches=latches,
    )


def _advance_goal(
    goal_before: Mapping[str, Any],
    *,
    before_organism: Mapping[str, float],
    after_organism: Mapping[str, float],
    global_tick: int,
    interventions: Mapping[str, str],
    observation_key: str,
    model: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    before_latches = _normalize_completed_latches(goal_before.get("completed_latches"))
    after_latches, reentered_variables = _updated_completed_latches(before_latches, after_organism)
    severe_after = _severe_variables(after_organism)
    eligible_after = _eligible_goal_candidates(after_organism, after_latches)
    eligible_names = [item["state_variable"] for item in eligible_after]
    transition_counts = _transition_counts_for_observation(model, observation_key)
    progress = {
        "state_variable": goal_before.get("state_variable"),
        "deficit_before": 0.0,
        "deficit_after": 0.0,
        "deficit_reduction": 0.0,
        "completed": False,
        "completed_latches_before": deepcopy(before_latches),
        "completed_latches_after": deepcopy(after_latches),
        "reentered_variables": reentered_variables,
        "severe_variables_after": severe_after,
        "eligible_body_goals": [
            name for name in eligible_names if name != goal_before.get("state_variable")
        ],
        "variable_states_before": _goal_variable_states(
            before_organism, before_latches
        ),
        "variable_states_after": _goal_variable_states(
            after_organism, after_latches
        ),
        "novelty_counter_hash_before": canonical_hash(transition_counts),
        "novelty_counter_hash_after": canonical_hash(transition_counts),
    }
    if goal_before["status"] == "active":
        key = str(goal_before["state_variable"])
        before_deficit = max(0.0, TARGET_LEVEL - float(before_organism[key]))
        after_deficit = max(0.0, TARGET_LEVEL - float(after_organism[key]))
        completed = after_deficit <= 0.0
        progress.update(
            {
                "state_variable": key,
                "deficit_before": _round(before_deficit),
                "deficit_after": _round(after_deficit),
                "deficit_reduction": _round(before_deficit - after_deficit),
                "completed": completed,
            }
        )

    override_candidate = _critical_override_candidate(after_organism)
    if interventions["override_mode"] == "canonical" and override_candidate is not None:
        reason = (
            "critical_override_energy"
            if override_candidate == "energy"
            else "critical_override_body_deficit"
        )
        changed = not (
            goal_before.get("status") == "active"
            and goal_before.get("state_variable") == override_candidate
        )
        next_goal = (
            _goal_record(
                override_candidate,
                after_organism,
                global_tick=global_tick,
                reason=reason,
                completed_latches=after_latches,
            )
            if changed
            else {
                **deepcopy(dict(goal_before)),
                "completed_latches": deepcopy(after_latches),
            }
        )
        return next_goal, progress, {
            "changed": changed,
            "kind": "critical_override" if changed else "critical_goal_carried",
            "reason": reason,
        }

    if interventions["hysteresis_mode"] == "no_hysteresis":
        ablated_latches = {
            key: float(after_organism[key]) >= TARGET_LEVEL for key in STATE_KEYS
        }
        next_goal = _select_goal(
            after_organism,
            global_tick=global_tick,
            reason="ablation_max_deficit_retarget",
            completed_latches=ablated_latches,
        )
        return next_goal, progress, {
            "changed": canonical_json(next_goal) != canonical_json(dict(goal_before)),
            "kind": "ablation_retargeted" if next_goal["status"] == "active" else "explore_carried",
            "reason": "ablation_max_deficit_retarget",
        }

    if goal_before["status"] == "active" and progress["completed"] is False:
        carried = {
            **deepcopy(dict(goal_before)),
            "completed_latches": deepcopy(after_latches),
        }
        return carried, progress, {"changed": False, "kind": "carried_active_goal", "reason": "hysteresis_carry"}

    if eligible_after:
        if progress["completed"]:
            reason = "previous_goal_completed"
        else:
            reason = "reentry_below_threshold"
        next_goal = _select_goal(
            after_organism,
            global_tick=global_tick,
            reason=reason,
            completed_latches=after_latches,
        )
        kind = (
            "completed_goal_to_body_goal"
            if progress["completed"]
            else "reentry"
        )
        return next_goal, progress, {"changed": True, "kind": kind, "reason": reason}

    if progress["completed"]:
        next_goal = _select_goal(
            after_organism,
            global_tick=global_tick,
            reason="explore_no_eligible_body_goal",
            completed_latches=after_latches,
        )
        return next_goal, progress, {
            "changed": True,
            "kind": "completed_goal_to_explore",
            "reason": "completed_goal_to_explore",
        }
    carried_explore = {
        **deepcopy(dict(goal_before)),
        "completed_latches": deepcopy(after_latches),
    }
    return carried_explore, progress, {
        "changed": False,
        "kind": "explore_carried",
        "reason": "explore_no_eligible_body_goal",
    }


def _normalize_completed_latches(value: Any) -> dict[str, bool]:
    if value is None:
        return _empty_completed_latches()
    _verify_completed_latches(value)
    return {key: bool(value[key]) for key in STATE_KEYS}


def _eligible_goal_candidates(
    organism: Mapping[str, float], completed_latches: Mapping[str, bool]
) -> list[dict[str, float | str]]:
    candidates = []
    for index, key in enumerate(STATE_KEYS):
        deficit = max(0.0, TARGET_LEVEL - float(organism[key]))
        if deficit <= 0.0 or bool(completed_latches[key]):
            continue
        candidates.append(
            {
                "state_variable": key,
                "deficit": _round(deficit),
                "state_key_order": index,
            }
        )
    candidates.sort(key=lambda item: (-float(item["deficit"]), int(item["state_key_order"])))
    return candidates


def _goal_variable_states(
    organism: Mapping[str, float], completed_latches: Mapping[str, bool]
) -> dict[str, dict[str, Any]]:
    latches = _normalize_completed_latches(completed_latches)
    return {
        key: {
            "value": _round(float(organism[key])),
            "deficit": _round(max(0.0, TARGET_LEVEL - float(organism[key]))),
            "latched": bool(latches[key]),
            "eligible": bool(
                float(organism[key]) < TARGET_LEVEL and not latches[key]
            ),
            "severe": bool(
                float(organism[key]) <= CRITICAL_OVERRIDE_THRESHOLD
            ),
        }
        for key in STATE_KEYS
    }


def _updated_completed_latches(
    completed_latches: Mapping[str, bool], organism: Mapping[str, float]
) -> tuple[dict[str, bool], list[str]]:
    updated = _normalize_completed_latches(completed_latches)
    reentered: list[str] = []
    for key in STATE_KEYS:
        current = float(organism[key])
        if current >= TARGET_LEVEL:
            updated[key] = True
        elif updated[key] and current < REENTRY_THRESHOLD:
            updated[key] = False
            reentered.append(key)
    return updated, reentered


def _severe_variables(organism: Mapping[str, float]) -> list[str]:
    return [key for key in STATE_KEYS if float(organism[key]) <= CRITICAL_OVERRIDE_THRESHOLD]


def _critical_override_candidate(organism: Mapping[str, float]) -> str | None:
    severe = _severe_variables(organism)
    if not severe:
        return None
    if "energy" in severe:
        return "energy"
    return min(severe, key=lambda key: (float(organism[key]), STATE_KEYS.index(key)))


def _goal_record(
    state_variable: str,
    organism: Mapping[str, float],
    *,
    global_tick: int,
    reason: str,
    completed_latches: Mapping[str, bool],
    selected_tick: int | None = None,
) -> dict[str, Any]:
    return {
        "state_variable": state_variable,
        "target": TARGET_LEVEL,
        "selected_global_tick": int(global_tick if selected_tick is None else selected_tick),
        "entry_deficit": _round(max(0.0, TARGET_LEVEL - float(organism[state_variable]))),
        "status": "active",
        "selection_reason": reason,
        "completed_latches": _normalize_completed_latches(completed_latches),
    }


def _goal_context_key(goal: Mapping[str, Any]) -> str:
    if goal.get("status") == "active" and goal.get("state_variable") in STATE_KEYS:
        return str(goal["state_variable"])
    return "explore"


def _score_candidate(
    *,
    organism: Mapping[str, float],
    model: Mapping[str, Any],
    memory_summary: Mapping[str, Any],
    claim_summary: Mapping[str, Any],
    observation: Mapping[str, Any],
    context_key: str,
    current_goal: Mapping[str, Any],
    action: str,
    deterministic_tie: float,
    novelty_mode: str,
) -> dict[str, Any]:
    model_entry = model.get(context_key, {}).get(action)
    if model_entry and int(model_entry["count"]) > 0:
        predicted = {key: float(model_entry["ema_delta"][key]) for key in STATE_KEYS}
        model_ref = {"source": "tabular_ema", "context_key": context_key, "action": action, "count": int(model_entry["count"])}
    else:
        predicted = _prior_prediction(observation, action)
        model_ref = {"source": "visual_prior", "context_key": context_key, "action": action, "count": 0}
    predicted_after = _apply_delta(organism, predicted)
    goal_reduction = _current_goal_deficit_reduction(organism, predicted_after, current_goal)
    total_reduction = _round(_total_deficit(organism) - _total_deficit(predicted_after))
    legacy_memory_bias = float(memory_summary["legacy_bias_by_action"][action])
    claim_memory_bias = claim_memory.memory_bias_for_action(
        {
            "claims": [{}] * int(claim_summary["claim_count"]),
            "support_by_action": claim_summary["support_by_action"],
        },
        action,
    )
    memory_bias = max(-0.5, min(0.5, legacy_memory_bias + claim_memory_bias))
    transition_counts = _transition_counts_for_observation(model, observation_hash(observation))
    novelty = _explore_novelty_score(
        transition_counts,
        action,
        enabled=current_goal.get("status") == "explore",
        novelty_mode=novelty_mode,
    )
    total_score = _round(
        goal_reduction
        + total_reduction
        + memory_bias
        + novelty["score"]
        - ACTION_COSTS[action]
        + deterministic_tie,
        digits=9,
    )
    return {
        "action": action,
        "predicted_delta": {key: _round(predicted[key]) for key in STATE_KEYS},
        "current_goal_deficit_reduction": goal_reduction,
        "total_deficit_reduction": total_reduction,
        "legacy_memory_bias": _round(legacy_memory_bias),
        "claim_memory_bias": _round(claim_memory_bias),
        "memory_bias": _round(memory_bias),
        "explore_score": novelty["score"],
        "explore_novelty": novelty["novelty"],
        "explore_uncertainty": novelty["uncertainty"],
        "novelty_total_count": novelty["total"],
        "novelty_unique_next_observation_count": novelty["unique"],
        "novelty_counter_hash": novelty["counter_hash"],
        "action_cost": ACTION_COSTS[action],
        "deterministic_tie": deterministic_tie,
        "total_score": total_score,
        "model_ref": model_ref,
        "memory_refs": [],
        "claim_refs": [],
        "selected": False,
    }


def _prior_prediction(observation: Mapping[str, Any], action: str) -> dict[str, float]:
    visual = observation.get("visual", [])
    flat = [token for row in visual for token in row]
    front = visual[1][2] if isinstance(visual, list) and len(visual) == 5 else "wall"
    predicted = {key: 0.0 for key in STATE_KEYS}
    if action == "rest":
        predicted["safety"] = REST_DELTA["safety"]
    elif action == "interact" and front in {"v0", "v1", "v2", "v3", "v4"}:
        predicted["energy"] = 0.18
        predicted["connection"] = 0.02
        predicted["stimulation"] = 0.02
    elif action == "move_forward" and front == "empty":
        predicted["stimulation"] = 0.03
    elif action in {"turn_left", "turn_right"}:
        predicted["stimulation"] = 0.01
    if flat.count("occluded") >= 4 and action == "move_forward":
        predicted["stimulation"] += 0.02
    return {key: _round(predicted[key]) for key in STATE_KEYS}


def compute_actual_delta(
    world_transition: Mapping[str, Any], *, selected_action: str
) -> dict[str, float]:
    """Compute the observed non-metabolic organism delta for live and evaluation use."""

    delta = {key: 0.0 for key in STATE_KEYS}
    if selected_action == "rest":
        delta.update(REST_DELTA)
    if world_transition.get("outcome_type") == "interacted":
        cause = world_transition.get("cause")
        if cause not in CAUSE_DELTAS:
            raise EngineInvariantError("interact cause is not canonical")
        for key, value in CAUSE_DELTAS[str(cause)].items():
            delta[key] += float(value)
    delta["energy"] = 0.0
    return {key: _round(delta[key]) for key in STATE_KEYS}


def _actual_delta(
    world_transition: Mapping[str, Any], *, selected_action: str
) -> dict[str, float]:
    """Compatibility wrapper for the former private boundary."""

    return compute_actual_delta(world_transition, selected_action=selected_action)


def _update_model(
    state: dict[str, Any],
    *,
    context_key: str,
    action: str,
    prediction_before: Mapping[str, float],
    actual_delta: Mapping[str, float],
    apply_update: bool,
    observation_key: str,
    next_observation_hash: str,
) -> dict[str, Any]:
    source_model = state["model"]
    before_hash = str(state["component_hashes"]["model"])
    context_before = source_model.get(context_key, {})
    previous = context_before.get(action)
    previous_count = 0 if previous is None else int(previous["count"])
    signed_error = {
        key: _round(float(actual_delta[key]) - float(prediction_before[key]))
        for key in STATE_KEYS
    }
    if not apply_update:
        return {
            "applied": False,
            "reason": "adaptive_updates_frozen",
            "context_key": context_key,
            "action": action,
            "alpha": EMA_ALPHA,
            "previous_count": previous_count,
            "new_count": previous_count,
            "prediction_before": {key: _round(float(prediction_before[key])) for key in STATE_KEYS},
            "prediction_error": signed_error,
            "applied_delta": {key: 0.0 for key in STATE_KEYS},
            "prediction_after": {key: _round(float(prediction_before[key])) for key in STATE_KEYS},
            "model_before_hash": before_hash,
            "model_after_hash": before_hash,
            "visual_transition_update": {
                "applied": False,
                "observation_hash": observation_key,
                "next_observation_hash": next_observation_hash,
                "action": action,
            },
        }
    # Copy only the two branches updated by this observation.  The verified
    # input model remains immutable so a failed SQLite commit cannot leak a
    # provisional update back into the controller's current state.
    model = dict(source_model)
    context = dict(context_before)
    model[context_key] = context
    transition_counts = dict(source_model.get(VISUAL_TRANSITION_MODEL_KEY, {}))
    observation_counts = dict(transition_counts.get(observation_key, {}))
    transition_entry = dict(
        observation_counts.get(action, {"total": 0, "next_counts": {}})
    )
    transition_entry["next_counts"] = dict(transition_entry["next_counts"])
    observation_counts[action] = transition_entry
    transition_counts[observation_key] = observation_counts
    model[VISUAL_TRANSITION_MODEL_KEY] = transition_counts
    state["model"] = model
    applied_delta = {key: _round(EMA_ALPHA * signed_error[key]) for key in STATE_KEYS}
    new_delta = {
        key: _round(float(prediction_before[key]) + applied_delta[key])
        for key in STATE_KEYS
    }
    context[action] = {"count": previous_count + 1, "ema_delta": new_delta}
    transition_update = _update_visual_transition_counts(
        model,
        observation_key=observation_key,
        action=action,
        next_observation_hash=next_observation_hash,
    )
    after_hash = canonical_hash(
        {
            "schema_version": "ego.life_playground.model_chain_update.v1",
            "previous_hash": before_hash,
            "context_key": context_key,
            "action": action,
            "context_entry": context[action],
            "visual_transition_update": transition_update,
        }
    )
    component_hashes = dict(state["component_hashes"])
    component_hashes["model"] = after_hash
    state["component_hashes"] = component_hashes
    return {
        "applied": True,
        "alpha": EMA_ALPHA,
        "context_key": context_key,
        "action": action,
        "previous_count": previous_count,
        "new_count": previous_count + 1,
        "ema_delta": new_delta,
        "prediction_before": {key: _round(float(prediction_before[key])) for key in STATE_KEYS},
        "prediction_error": signed_error,
        "applied_delta": applied_delta,
        "prediction_after": new_delta,
        "model_before_hash": before_hash,
        "model_after_hash": after_hash,
        "visual_transition_update": transition_update,
    }


def rebuild_consolidated_memory(
    episodic: list[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Deterministically rebuild derived consolidation from ordered source records.

    Episodic records remain the authority.  Consolidation never overwrites or
    removes them (or the separate competing-claim store); it is a pure indexed
    view with exact command/episode/sequence lineage.
    """

    if not isinstance(episodic, list):
        raise EngineInvariantError("episodic source must be a list")
    grouped: dict[tuple[str, str, str], list[Mapping[str, Any]]] = {}
    for entry in episodic:
        _verify_episodic_memory_entry(entry)
        slot = (str(entry["cue"]), str(entry["current_goal"]), str(entry["action"]))
        grouped.setdefault(slot, []).append(entry)
    rebuilt: list[dict[str, Any]] = []
    for (cue, current_goal, action), matching in sorted(grouped.items()):
        consolidated = _build_consolidated_memory_entry(
            cue=cue,
            current_goal=current_goal,
            action=action,
            matching=matching,
        )
        if consolidated is None:
            continue
        rebuilt.append(consolidated)
    return rebuilt


def _build_consolidated_memory_entry(
    *,
    cue: str,
    current_goal: str,
    action: str,
    matching: list[Mapping[str, Any]],
) -> dict[str, Any] | None:
    """Build one canonical slot from its sources.

    The full rebuild remains available to verifiers.  The live append path uses
    this same builder for only the affected slot, avoiding a full-table rebuild
    while preserving the exact derived bytes.
    """

    distinct_episodes = {str(entry["source_episode_id"]) for entry in matching}
    if len(distinct_episodes) < CONSOLIDATION_THRESHOLD:
        return None
    ordered = sorted(
        matching,
        key=lambda entry: (
            str(entry["source_episode_id"]),
            str(entry["source_command_hash"]),
            int(entry["source_sequence"]),
        ),
    )
    source_hashes = [str(entry["source_command_hash"]) for entry in ordered]
    source_episode_ids = [str(entry["source_episode_id"]) for entry in ordered]
    source_sequences = [int(entry["source_sequence"]) for entry in ordered]
    key = f"{cue}|{current_goal}|{action}"
    consolidated_id = (
        f"con-{canonical_hash({'key': key, 'source_command_hashes': source_hashes})[:20]}"
    )
    return {
        "memory_id": consolidated_id,
        "kind": "consolidated",
        "key": key,
        "cue": cue,
        "current_goal": current_goal,
        "action": action,
        "strength": _round(
            sum(float(entry["utility"]) for entry in ordered) / len(ordered)
        ),
        "source_command_hashes": source_hashes,
        "source_episode_ids": source_episode_ids,
        "source_sequences": source_sequences,
        "episode_count": len(distinct_episodes),
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
    source_memory = state["memory"]
    memory = dict(source_memory)
    episodic = list(source_memory["episodic"])
    episodic.append(episode)
    memory["episodic"] = episodic
    key = f"{cue}|{current_goal}|{action}"
    source_consolidated = source_memory["consolidated"]
    previous_consolidated = next(
        (item for item in source_consolidated if item["key"] == key),
        None,
    )
    before_consolidated = canonical_hash(previous_consolidated)
    matching = [
        entry
        for entry in episodic
        if entry["cue"] == cue
        and entry["current_goal"] == current_goal
        and entry["action"] == action
    ]
    selected_consolidated = _build_consolidated_memory_entry(
        cue=cue,
        current_goal=current_goal,
        action=action,
        matching=matching,
    )
    consolidated = [item for item in source_consolidated if item["key"] != key]
    if selected_consolidated is not None:
        consolidated.append(selected_consolidated)
        consolidated.sort(
            key=lambda item: (item["cue"], item["current_goal"], item["action"])
        )
    memory["consolidated"] = consolidated
    state["memory"] = memory
    after_consolidated = canonical_hash(selected_consolidated)
    if selected_consolidated is None:
        return {
            "applied": True,
            "episodic_write": memory_id,
            "slot_key": key,
            "consolidation_applied": False,
            "consolidation_refs": [],
            "reason": "threshold_not_met",
            "rebuild_producer": "ego_life_playground_v0.engine.rebuild_consolidated_memory",
            "consolidated_before_hash": before_consolidated,
            "consolidated_after_hash": after_consolidated,
        }
    source_hashes = list(selected_consolidated["source_command_hashes"])
    return {
        "applied": True,
        "episodic_write": memory_id,
        "slot_key": key,
        "consolidation_applied": True,
        "consolidation_refs": source_hashes,
        "consolidated_write": selected_consolidated["memory_id"],
        "reason": "threshold_met",
        "rebuild_producer": "ego_life_playground_v0.engine.rebuild_consolidated_memory",
        "consolidated_before_hash": before_consolidated,
        "consolidated_after_hash": after_consolidated,
    }


def _update_claim_memory(
    state: dict[str, Any],
    *,
    observation: Mapping[str, Any],
    current_goal: str,
    action: str,
    actual_delta: Mapping[str, Any],
    sequence: int,
    command_hash: str,
    source_episode_id: str,
    memory_enabled: bool,
    updates_enabled: bool,
) -> dict[str, Any]:
    if not memory_enabled:
        return {
            "applied": False,
            "event_id": None,
            "claim_id": None,
            "reason": "memory_disabled",
        }
    if not updates_enabled:
        return {
            "applied": False,
            "event_id": None,
            "claim_id": None,
            "reason": "adaptive_updates_frozen",
        }
    event_id = f"claim-event-{canonical_hash({'command_hash': command_hash, 'action': action})[:20]}"
    updated, report = claim_memory.record_outcome_evidence(
        state["memory"],
        subject="visual_context",
        predicate="preferred_action",
        value=action,
        evidence_strength=float(actual_delta.get(current_goal, 0.0)),
        event_id=event_id,
        source_episode_id=source_episode_id,
        source_command_hash=command_hash,
        source_sequence=sequence,
        observed_public_features={
            "observation_hash": observation_hash(observation),
            "visual": deepcopy(observation.get("visual")),
            "current_goal": current_goal,
            "interoception_delta": {
                key: _round(float(actual_delta[key])) for key in STATE_KEYS
            },
        },
        prevalidated=True,
    )
    state["memory"] = updated
    result = dict(report)
    result["reason"] = "visual_outcome_recorded"
    return result


def _advance_memory_component_hash(
    state: dict[str, Any],
    *,
    previous_hash: str,
    memory_update: Mapping[str, Any],
    claim_update: Mapping[str, Any],
) -> None:
    """Advance the memory hash from the exact rows changed this tick."""

    if not memory_update.get("applied") and not claim_update.get("applied"):
        return
    memory = state["memory"]
    memory_id = memory_update.get("episodic_write")
    slot_key = memory_update.get("slot_key")
    event_id = claim_update.get("event_id")
    claim_id = claim_update.get("claim_id")
    episodic_write = next(
        (item for item in memory["episodic"] if item["memory_id"] == memory_id),
        None,
    )
    consolidated_write = next(
        (item for item in memory["consolidated"] if item["key"] == slot_key),
        None,
    )
    claim_event = next(
        (item for item in memory["claim_events"] if item["event_id"] == event_id),
        None,
    )
    competing_claim = next(
        (item for item in memory["competing_claims"] if item["claim_id"] == claim_id),
        None,
    )
    after_hash = canonical_hash(
        {
            "schema_version": "ego.life_playground.memory_chain_update.v1",
            "previous_hash": previous_hash,
            "episodic_write": episodic_write,
            "consolidated_write": consolidated_write,
            "claim_event": claim_event,
            "competing_claim": competing_claim,
        }
    )
    component_hashes = dict(state["component_hashes"])
    component_hashes["memory"] = after_hash
    state["component_hashes"] = component_hashes


def _memory_read_view(
    memory: Mapping[str, Any],
    *,
    source_memory_hash: str,
    memory_mode: str,
    provenance_mode: str,
    provenance_shuffle_seed: int,
    consolidation_mode: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if not _is_sha256(source_memory_hash):
        raise EngineInvariantError("source memory hash must be sha256")
    source_hash = source_memory_hash
    if memory_mode == "off":
        empty = {
            "episodic": [],
            "consolidated": [],
            **claim_memory.empty_claim_memory(),
        }
        return empty, {
            "mode": provenance_mode,
            "consolidation_mode": consolidation_mode,
            "status": "memory_disabled",
            "source_memory_hash": source_hash,
            "projected_view_hash": _semantic_memory_hash(empty),
            "permutation_hash": None,
            "eligibility_count": 0,
            "cross_slot_moves": 0,
            "marginal_preservation": _identity_projection_marginals(empty),
        }
    canonical = dict(memory)
    if consolidation_mode == "off_projection":
        canonical["consolidated"] = []
    projected_hash = (
        source_hash
        if consolidation_mode == "canonical"
        else _semantic_memory_hash(canonical)
    )
    if provenance_mode == "canonical":
        return canonical, {
            "mode": "canonical",
            "consolidation_mode": consolidation_mode,
            "status": "canonical"
            if consolidation_mode == "canonical"
            else "consolidation_off_projection",
            "source_memory_hash": source_hash,
            "projected_view_hash": projected_hash,
            "permutation_hash": None,
            "eligibility_count": len(canonical.get("episodic", [])),
            "cross_slot_moves": 0,
            "marginal_preservation": _identity_projection_marginals(canonical),
        }
    if len(canonical.get("competing_claims", [])) >= 2:
        projected, report = claim_memory.shuffle_provenance(
            canonical, seed=int(provenance_shuffle_seed)
        )
        enriched = deepcopy(report)
        enriched.update(
            {
                "mode": "shuffle_projection",
                "consolidation_mode": consolidation_mode,
                "source_memory_hash": source_hash,
                "projected_view_hash": _semantic_memory_hash(projected),
                "permutation_hash": canonical_hash(
                    {
                        "seed": int(provenance_shuffle_seed),
                        "changed_json_pointers": report.get("changed_json_pointers", []),
                    }
                ),
                "cross_slot_moves": len(report.get("changed_json_pointers", [])),
                "marginal_preservation": _compute_projection_marginals(
                    canonical, projected
                ),
            }
        )
        return projected, enriched
    projected, report = _shuffle_provenance_projection(
        canonical, seed=provenance_shuffle_seed
    )
    report["consolidation_mode"] = consolidation_mode
    return projected, report


def _identity_projection_marginals(memory: Mapping[str, Any]) -> dict[str, Any]:
    """Return computed invariants for an identity projection in O(1)."""

    # _verify_state has already established that each canonical episodic row is
    # eligible; projected-off views preserve that same list.
    eligible_count = len(memory.get("episodic", []))
    return {
        "slot_counts_preserved": eligible_count == eligible_count,
        "bundle_multiset_preserved": eligible_count == eligible_count,
        "eligible_records_before": eligible_count,
        "eligible_records_after": eligible_count,
        "identity_projection": True,
    }


def _compact_provenance_projection(report: Mapping[str, Any]) -> dict[str, Any]:
    """Persist a bounded receipt while retaining recomputable projection hashes."""

    marginals = report.get("marginal_preservation", {})
    compact_marginals = {
        key: deepcopy(marginals.get(key))
        for key in (
            "slot_counts_preserved",
            "bundle_multiset_preserved",
            "eligible_records_before",
            "eligible_records_after",
        )
    }
    source_hash = report.get("source_memory_hash")
    return {
        key: deepcopy(report.get(key))
        for key in (
            "mode",
            "seed",
            "consolidation_mode",
            "status",
            "source_memory_hash",
            "projected_view_hash",
            "permutation_hash",
            "eligibility_count",
            "cross_slot_moves",
        )
    } | {
        "component_hash": source_hash,
        "marginal_preservation": compact_marginals,
        "marginal_details_hash": canonical_hash(marginals),
    }


def _reference_receipt(values: Any) -> dict[str, Any]:
    refs = sorted({str(value) for value in values}) if isinstance(values, list) else []
    return {
        "count": len(refs),
        "chain_hash": canonical_hash(refs),
        "latest": refs[-1] if refs else None,
    }


def _compact_claim_retrieval(retrieval: Mapping[str, Any]) -> dict[str, Any]:
    claims = []
    for item in retrieval.get("claims", []):
        eligible_refs = item.get("eligible_provenance_event_ids", [])
        withheld_refs = item.get("withheld_provenance_event_ids", [])
        source_episodes = item.get("source_episode_ids", [])
        claims.append(
            {
                key: deepcopy(item.get(key))
                for key in (
                    "claim_id",
                    "conflict_set_id",
                    "subject",
                    "predicate",
                    "value",
                    "support",
                    "raw_support",
                    "eligible_support",
                    "context_eligible",
                    "retrieval_score",
                    "first_seen_tick",
                    "last_supported_tick",
                )
            }
            | {
                "eligible_provenance": _reference_receipt(eligible_refs),
                "withheld_provenance": _reference_receipt(withheld_refs),
                "source_episodes": _reference_receipt(source_episodes),
            }
        )
    withheld_claims = retrieval.get("withheld_claims", [])
    return {
        "schema_version": "ego.life_playground.claim_retrieval.compact.v1",
        "source_schema_version": retrieval.get("schema_version"),
        "status": retrieval.get("status"),
        "producer_function": retrieval.get("producer_function"),
        "query": deepcopy(retrieval.get("query")),
        "claims": claims,
        "withheld_claim_count": len(withheld_claims),
        "withheld_claims_hash": canonical_hash(withheld_claims),
        "support_by_action": deepcopy(retrieval.get("support_by_action", {})),
        "raw_support_by_action": deepcopy(
            retrieval.get("raw_support_by_action", {})
        ),
        "support_margin": retrieval.get("support_margin"),
        "uncertainty": retrieval.get("uncertainty"),
        "provenance": _reference_receipt(
            retrieval.get("provenance_event_ids", [])
        ),
        "withheld_provenance": _reference_receipt(
            retrieval.get("withheld_provenance_event_ids", [])
        ),
        "source_episodes": _reference_receipt(
            retrieval.get("source_episode_ids", [])
        ),
        "policy_summary": deepcopy(retrieval.get("policy_summary", {})),
    }


def _compact_memory_update(report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: deepcopy(report.get(key))
        for key in (
            "applied",
            "episodic_write",
            "slot_key",
            "consolidation_applied",
            "consolidated_write",
            "reason",
            "rebuild_producer",
            "consolidated_before_hash",
            "consolidated_after_hash",
        )
    } | {
        "consolidation_refs": _reference_receipt(
            report.get("consolidation_refs", [])
        )
    }


def _compact_claim_update(report: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: deepcopy(report.get(key))
        for key in (
            "applied",
            "producer_function",
            "event_id",
            "claim_id",
            "conflict_set_id",
            "support_after",
            "reason",
        )
    } | {
        "provenance": _reference_receipt(
            report.get("provenance_event_ids", [])
        ),
        "source_episodes": _reference_receipt(
            report.get("source_episode_ids", [])
        ),
    }


def _compact_predictive_plan(
    plan: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(plan, Mapping):
        return None
    predictions: dict[str, Any] = {}
    predictor_contexts: set[tuple[Any, Any]] = set()
    for action, prediction in (plan.get("predictions_by_action") or {}).items():
        if not isinstance(prediction, Mapping):
            continue
        predictor_contexts.add(
            (prediction.get("input_hash"), prediction.get("feature_hash"))
        )
        predictions[str(action)] = {
            key: deepcopy(prediction.get(key))
            for key in (
                "outcome_probabilities",
                "predicted_delta",
                "conditional_delta_hash",
                "resource_interaction_probability",
                "terminal_risk",
            )
        } | {"prediction_hash": canonical_hash(prediction)}
    if len(predictor_contexts) > 1:
        raise EngineInvariantError("predictive root actions do not share one context")
    predictor_context_hash = (
        None
        if not predictor_contexts
        else canonical_hash(
            {
                "input_hash": next(iter(predictor_contexts))[0],
                "feature_hash": next(iter(predictor_contexts))[1],
            }
        )
    )
    candidate_values = deepcopy(plan.get("candidate_values"))
    beam = plan.get("beam_receipt") or {}
    root_actions_by_depth = beam.get("root_actions_by_depth") or []
    compact_beam = {
        "expanded_by_depth": deepcopy(beam.get("expanded_by_depth")),
        "retained_by_depth": deepcopy(beam.get("retained_by_depth")),
        "root_action_counts_by_depth": [
            len(set(actions)) for actions in root_actions_by_depth
        ],
        "all_probability_mass_normalized": deepcopy(
            beam.get("all_probability_mass_normalized")
        ),
    }
    return {
        key: deepcopy(plan.get(key))
        for key in (
            "schema_version",
            "horizon",
            "beam_width",
            "discount",
            "relative_map_mode",
            "goal_value_mode",
            "active_goal",
            "predictor_input_goal_independent",
            "selected_action",
            "planned_actions",
            "mpc_selected_action",
            "selection_mode",
            "exploration_reason",
            "action_exposure_counts",
            "token_interaction_counts",
            "coverage_step",
            "exploration_hash",
            "tie_break_used",
            "tie_break_source",
            "model_hash",
            "belief_hash",
        )
    } | {
        "predictor_context_hash": predictor_context_hash,
        "predictions_by_action": predictions,
        "candidate_values": candidate_values,
        "beam_receipt": compact_beam,
    }


def _compact_predictive_update(report: Mapping[str, Any]) -> dict[str, Any]:
    compact = {
        key: deepcopy(report.get(key))
        for key in (
            "schema_version",
            "applied",
            "reason",
            "action",
            "actual_outcome_type",
            "resource_interaction",
            "terminal",
            "outcome_brier",
            "outcome_nll",
            "delta_error",
            "delta_outcome_updated",
            "delta_projection_by_state",
            "delta_base_hash_before",
            "delta_base_hash_after",
            "delta_outcome_offset_hash_before",
            "delta_outcome_offset_hash_after",
            "conditional_delta_hash_before",
            "conditional_delta_hash_after",
            "model_hash_before",
            "model_hash_after",
            "belief_hash_after",
            "exploration_hash_before",
            "exploration_hash_after",
            "action_exposure_counts_after",
            "token_interaction_counts_after",
            "coverage_step_after",
            "update_count_after",
        )
        if key in report
    }
    for field in ("prediction_before", "prediction_after"):
        if isinstance(report.get(field), Mapping):
            compact[f"{field}_hash"] = canonical_hash(report[field])
    return compact


def _shuffle_provenance_projection(
    memory: Mapping[str, Any], *, seed: int
) -> tuple[dict[str, Any], dict[str, Any]]:
    projected = deepcopy(dict(memory))
    eligible = _eligible_projection_records(projected)
    eligible.sort(key=lambda item: canonical_json(item["stable_key"]))
    slots = {item["slot"] for item in eligible}
    bundle_hashes = [canonical_hash(item["bundle"]) for item in eligible]
    source_hash = _semantic_memory_hash(memory)
    base_report = {
        "mode": "shuffle_projection",
        "seed": int(seed),
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
    seed_hash = canonical_hash({"seed": int(seed), "stable_lineage_keys": stable_keys})
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
    return _memory_biases(memory, cue=cue, current_goal=current_goal)[action]


def _memory_biases(
    memory: Mapping[str, Any], *, cue: str, current_goal: str
) -> dict[str, tuple[float, list[str]]]:
    biases = {action: 0.0 for action in ACTIONS}
    refs = {action: [] for action in ACTIONS}
    for entry in memory.get("episodic", []):
        if (
            entry["cue"] == cue
            and entry["current_goal"] == current_goal
        ):
            action = str(entry["action"])
            biases[action] += 0.20 * float(entry["utility"])
            refs[action].append(str(entry["source_command_hash"]))
    for entry in memory.get("consolidated", []):
        if (
            entry["cue"] == cue
            and entry["current_goal"] == current_goal
        ):
            action = str(entry["action"])
            biases[action] += 0.65 * float(entry["strength"])
            refs[action].extend(
                str(value) for value in entry["source_command_hashes"]
            )
    return {
        action: (
            max(-0.5, min(0.5, biases[action])),
            sorted(set(refs[action])),
        )
        for action in ACTIONS
    }


def _transition_counts_for_observation(
    model: Mapping[str, Any], observation_key: str
) -> dict[str, Any]:
    counts = model.get(VISUAL_TRANSITION_MODEL_KEY, {})
    if not isinstance(counts, Mapping):
        return {}
    entry = counts.get(observation_key, {})
    return deepcopy(dict(entry)) if isinstance(entry, Mapping) else {}


def _explore_novelty_score(
    transition_counts: Mapping[str, Any], action: str, *, enabled: bool, novelty_mode: str
) -> dict[str, Any]:
    entry = transition_counts.get(action, {})
    if not isinstance(entry, Mapping):
        entry = {}
    next_counts = entry.get("next_counts", {})
    if not isinstance(next_counts, Mapping):
        next_counts = {}
    total = int(entry.get("total", 0)) if isinstance(entry.get("total", 0), int) else 0
    unique = len(next_counts)
    score = 0.0
    novelty = 0.0
    uncertainty = 0.0
    if enabled and novelty_mode == "canonical":
        novelty = _round(1.0 / (1.0 + total))
        if total == 0:
            uncertainty = 1.0
        else:
            uncertainty = _round(
                1.0 - (max(int(count) for count in next_counts.values()) / total)
            )
        score = _round(novelty + uncertainty)
    return {
        "score": score,
        "novelty": novelty,
        "uncertainty": uncertainty,
        "total": total,
        "unique": unique,
        "counter_hash": canonical_hash(
            {
                "action": action,
                "total": total,
                "next_counts": dict(sorted(next_counts.items())),
            }
        ),
    }


def _update_visual_transition_counts(
    model: dict[str, Any], *, observation_key: str, action: str, next_observation_hash: str
) -> dict[str, Any]:
    counts = model.setdefault(VISUAL_TRANSITION_MODEL_KEY, {})
    by_action = counts.setdefault(observation_key, {})
    entry = by_action.setdefault(action, {"total": 0, "next_counts": {}})
    before_hash = canonical_hash(entry)
    entry["total"] = int(entry["total"]) + 1
    entry["next_counts"][next_observation_hash] = int(entry["next_counts"].get(next_observation_hash, 0)) + 1
    after_hash = canonical_hash(entry)
    return {
        "applied": True,
        "observation_hash": observation_key,
        "next_observation_hash": next_observation_hash,
        "action": action,
        "count_before": entry["total"] - 1,
        "count_after": entry["total"],
        "entry_hash_before": before_hash,
        "entry_hash_after": after_hash,
    }


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
        or normalized["consolidation_mode"] not in CONSOLIDATION_MODES
        or normalized["vision_mode"] not in VISION_MODES
        or normalized["hysteresis_mode"] not in HYSTERESIS_MODES
        or normalized["novelty_mode"] not in NOVELTY_MODES
        or normalized["override_mode"] not in OVERRIDE_MODES
        or normalized["survival_learning_mode"] not in SURVIVAL_LEARNING_MODES
        or normalized["predictive_control_mode"] not in PREDICTIVE_CONTROL_MODES
        or normalized["predictive_horizon_mode"] not in PREDICTIVE_HORIZON_MODES
        or normalized["relative_map_mode"] not in RELATIVE_MAP_MODES
        or normalized["goal_value_mode"] not in GOAL_VALUE_MODES
    ):
        raise EngineInvariantError("intervention enum mismatch")
    if (
        normalized["predictive_control_mode"] == "factored_mpc"
        and normalized["survival_learning_mode"] != "off"
    ):
        raise EngineInvariantError(
            "predictive control and Expected SARSA cannot both select actions"
        )
    try:
        shuffle_seed = int(normalized["provenance_shuffle_seed"])
    except ValueError as exc:
        raise EngineInvariantError("provenance shuffle seed must be a canonical integer string") from exc
    if str(shuffle_seed) != normalized["provenance_shuffle_seed"] or shuffle_seed < 0:
        raise EngineInvariantError("provenance shuffle seed must be a canonical non-negative integer string")
    if (
        normalized["memory_mode"] == "off"
        and normalized["provenance_mode"] == "shuffle_projection"
    ):
        raise EngineInvariantError("invalid intervention combination: memory off with shuffle projection")
    if (
        normalized["memory_mode"] == "off"
        and normalized["consolidation_mode"] == "off_projection"
    ):
        raise EngineInvariantError(
            "invalid intervention combination: memory off with consolidation projection"
        )
    return normalized


def _deterministic_tie(seed: int | Mapping[str, Any], sequence: int | str, context_key: str | None = None, action: str | None = None) -> float:
    if action is None:
        action = str(sequence)
        payload = seed
    else:
        payload = seed
    digest = hashlib.sha256(
        canonical_json({"policy_projection": payload, "action": action}).encode("utf-8")
    ).digest()
    integer = int.from_bytes(digest[:8], "big")
    return _round((integer / float(2**64 - 1)) * 1e-6, digits=12)


def _deterministic_ties(policy_projection: Mapping[str, Any]) -> dict[str, float]:
    """Hash the large projection once while preserving the legacy tie bytes."""

    projection_json = canonical_json(policy_projection)
    result: dict[str, float] = {}
    for action in ACTIONS:
        action_json = json.dumps(
            action, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        )
        encoded = (
            f'{{"action":{action_json},"policy_projection":{projection_json}}}'
        ).encode("utf-8")
        digest = hashlib.sha256(encoded).digest()
        integer = int.from_bytes(digest[:8], "big")
        result[action] = _round(
            (integer / float(2**64 - 1)) * 1e-6, digits=12
        )
    return result


def _policy_memory_summary(
    memory: Mapping[str, Any], *, cue: str, current_goal: str
) -> dict[str, Any]:
    biases = _memory_biases(memory, cue=cue, current_goal=current_goal)
    legacy_bias_by_action = {
        action: _round(biases[action][0])
        for action in ACTIONS
    }
    return {
        "schema_version": "ego.life_playground.policy_memory_summary.v2",
        "episodic_count": len(memory.get("episodic", [])),
        "consolidated_count": len(memory.get("consolidated", [])),
        "claim_event_count": len(memory.get("claim_events", [])),
        "competing_claim_count": len(memory.get("competing_claims", [])),
        "legacy_bias_by_action": legacy_bias_by_action,
    }


def _sanitized_goal(goal: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "state_variable": goal.get("state_variable"),
        "target": goal.get("target"),
        "status": goal.get("status"),
        "entry_deficit": goal.get("entry_deficit"),
        "selection_reason": goal.get("selection_reason"),
        "completed_latches": deepcopy(goal.get("completed_latches", _empty_completed_latches())),
    }


def _current_goal_deficit_reduction(
    before: Mapping[str, float], after: Mapping[str, float], goal: Mapping[str, Any]
) -> float:
    if goal["status"] != "active":
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
