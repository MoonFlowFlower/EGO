"""Factored, replayable predictive control for the V2 product reducer.

The module has no controller, world transition, metabolism, persistence, or UI
entrypoint.  It consumes only policy-visible observations, organism state,
episode-relative belief, selected atomic actions, and observed receipts passed
by ``engine.compute_step``.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
import platform
from typing import Any, Mapping

import numpy as np

from .microworld import ACTIONS, FACING_DELTAS, FACING_ORDER, PUBLIC_OBSERVATION_SCHEMA_VERSION


STATE_SCHEMA_VERSION = "ego.life_playground.predictive_control.v3"
BELIEF_SCHEMA_VERSION = "ego.life_playground.relative_belief.v1"
MODEL_SCHEMA_VERSION = "ego.life_playground.factored_predictor.v3"
EXPLORATION_SCHEMA_VERSION = "ego.life_playground.predictive_exploration.v1"
PREDICTION_SCHEMA_VERSION = "ego.life_playground.outcome_prediction.v3"
PLAN_SCHEMA_VERSION = "ego.life_playground.factored_plan.v3"
UPDATE_SCHEMA_VERSION = "ego.life_playground.predictor_update.v3"
ALGORITHM = "online_linear_softmax_factored_mpc"
LEARNING_RATE = 0.08
HORIZON = 12
BEAM_WIDTH = 16
DISCOUNT = 0.97
TARGET_LEVEL = 0.72
ACTION_EXPOSURE_TARGET = 4
TOKEN_INTERACTION_TARGET = 2
OUTCOMES = ("moved", "blocked", "interacted", "no_object", "rested", "turned")
STATE_KEYS = ("energy", "safety", "connection", "stimulation")
RELATIVE_MAP_MODES = ("relative", "off")
GOAL_VALUE_MODES = ("contextual", "equal")
FEATURE_NAMES = (
    "bias",
    "energy",
    "safety",
    "connection",
    "stimulation",
    "front_empty",
    "front_wall",
    "front_occluded",
    "front_v0",
    "front_v1",
    "front_v2",
    "front_v3",
    "front_v4",
    "known_cell_fraction",
    "known_object_fraction",
)
_VISIBLE_TOKENS = frozenset({"self", "empty", "wall", "occluded", "v0", "v1", "v2", "v3", "v4"})
_FORBIDDEN_PREDICTOR_FIELDS = frozenset(
    {
        "cause",
        "future_observation",
        "global_coordinates",
        "global_position",
        "objects_by_cause",
        "run_seed",
        "seed",
        "seed_id",
        "token_mapping",
        "world_position",
    }
)
NUMERIC_BACKEND_ID = "numpy"
NUMERIC_BACKEND_VERSION = "2.2.6"
NUMERIC_DTYPE = np.dtype(np.float64)
ACTION_INDEX = {action: index for index, action in enumerate(ACTIONS)}
OUTCOME_INDEX = {outcome: index for index, outcome in enumerate(OUTCOMES)}
STATE_INDEX = {key: index for index, key in enumerate(STATE_KEYS)}
FEATURE_INDEX = {feature: index for index, feature in enumerate(FEATURE_NAMES)}


class PredictiveControlInvariantError(ValueError):
    """Raised when the predictor receives out-of-contract or invalid state."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _canonical_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _round(value: float) -> float:
    return round(float(value), 12)


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return _round(max(lower, min(upper, float(value))))


def _sigmoid(value: float) -> float:
    clipped = max(-30.0, min(30.0, float(value)))
    return 1.0 / (1.0 + math.exp(-clipped))


def numeric_runtime_contract() -> dict[str, str]:
    """Return and enforce the sole numeric runtime used by the predictor."""

    if np.__version__ != NUMERIC_BACKEND_VERSION:
        raise PredictiveControlInvariantError(
            f"predictive control requires numpy {NUMERIC_BACKEND_VERSION}"
        )
    return {
        "backend": NUMERIC_BACKEND_ID,
        "backend_version": NUMERIC_BACKEND_VERSION,
        "dtype": NUMERIC_DTYPE.str,
        "python_version": platform.python_version(),
    }


def hyperparameters() -> dict[str, Any]:
    runtime = numeric_runtime_contract()
    action_order = list(ACTIONS)
    outcome_order = list(OUTCOMES)
    state_order = list(STATE_KEYS)
    feature_order = list(FEATURE_NAMES)
    return {
        "algorithm": ALGORITHM,
        "learning_rate": LEARNING_RATE,
        "horizon": HORIZON,
        "beam_width": BEAM_WIDTH,
        "discount": DISCOUNT,
        "outcomes": list(OUTCOMES),
        "feature_names": list(FEATURE_NAMES),
        "predictor_inputs": ["policy_observation", "organism", "relative_belief"],
        "goal_is_predictor_input": False,
        "action_exposure_target": ACTION_EXPOSURE_TARGET,
        "token_interaction_target": TOKEN_INTERACTION_TARGET,
        "numeric_runtime": runtime,
        "action_order": action_order,
        "outcome_order": outcome_order,
        "state_order": state_order,
        "feature_order": feature_order,
        "action_order_hash": _canonical_hash(action_order),
        "outcome_order_hash": _canonical_hash(outcome_order),
        "state_order_hash": _canonical_hash(state_order),
        "feature_order_hash": _canonical_hash(feature_order),
    }


def _zero_vector(length: int) -> list[float]:
    return [0.0] * length


def _empty_outcome_weights() -> list[list[list[float]]]:
    return [[_zero_vector(len(FEATURE_NAMES)) for _ in OUTCOMES] for _ in ACTIONS]


def _empty_delta_weights() -> list[list[list[float]]]:
    return [[_zero_vector(len(FEATURE_NAMES)) for _ in STATE_KEYS] for _ in ACTIONS]


def _empty_action_feature_weights() -> list[list[float]]:
    return [_zero_vector(len(FEATURE_NAMES)) for _ in ACTIONS]


def _empty_belief(episode_index: int = 0) -> dict[str, Any]:
    return {
        "schema_version": BELIEF_SCHEMA_VERSION,
        "episode_index": episode_index,
        "relative_pose": [0, 0],
        "relative_facing": "N",
        "cells": {},
        "observation_count": 0,
    }


def _empty_exploration() -> dict[str, Any]:
    return {
        "schema_version": EXPLORATION_SCHEMA_VERSION,
        "action_exposure_counts": {action: 0 for action in ACTIONS},
        "token_interaction_counts": {f"v{index}": 0 for index in range(5)},
        "coverage_step": 0,
    }


def empty_state() -> dict[str, Any]:
    numeric_runtime_contract()
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "belief": _empty_belief(),
        "exploration": _empty_exploration(),
        "model": {
            "schema_version": MODEL_SCHEMA_VERSION,
            "algorithm": ALGORITHM,
            "outcome_weights": _empty_outcome_weights(),
            "delta_weights": _empty_delta_weights(),
            "resource_weights": _empty_action_feature_weights(),
            "terminal_weights": _empty_action_feature_weights(),
            "visit_counts": {},
            "update_count": 0,
        },
    }


def _validate_observation(observation: Any) -> None:
    if (
        not isinstance(observation, Mapping)
        or set(observation) != {"schema_version", "visual"}
        or observation.get("schema_version") != PUBLIC_OBSERVATION_SCHEMA_VERSION
    ):
        raise PredictiveControlInvariantError("predictor observation schema mismatch")
    visual = observation["visual"]
    if (
        not isinstance(visual, list)
        or len(visual) != 5
        or any(not isinstance(row, list) or len(row) != 5 for row in visual)
        or any(type(token) is not str or token not in _VISIBLE_TOKENS for row in visual for token in row)
        or visual[2][2] != "self"
    ):
        raise PredictiveControlInvariantError("predictor observation must be a valid 5x5 visual grid")


def _validate_organism(organism: Any) -> None:
    if not isinstance(organism, Mapping) or set(organism) != set(STATE_KEYS):
        raise PredictiveControlInvariantError("predictor organism schema mismatch")
    for key in STATE_KEYS:
        value = organism[key]
        if type(value) is not float or not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise PredictiveControlInvariantError(f"predictor organism {key} is invalid")


def _validate_belief_summary(summary: Any) -> None:
    required = {
        "relative_pose",
        "relative_facing",
        "known_cell_count",
        "known_object_count",
        "front_token",
        "token_counts",
    }
    if not isinstance(summary, Mapping) or set(summary) != required:
        raise PredictiveControlInvariantError("predictor belief summary schema mismatch")
    pose = summary["relative_pose"]
    if not isinstance(pose, list) or len(pose) != 2 or any(type(item) is not int for item in pose):
        raise PredictiveControlInvariantError("relative pose must be two integers")
    if summary["relative_facing"] not in FACING_ORDER:
        raise PredictiveControlInvariantError("relative facing is invalid")
    for key in ("known_cell_count", "known_object_count"):
        if type(summary[key]) is not int or summary[key] < 0:
            raise PredictiveControlInvariantError(f"{key} must be non-negative")
    if summary["front_token"] not in _VISIBLE_TOKENS - {"self"}:
        raise PredictiveControlInvariantError("front token is invalid")
    token_counts = summary["token_counts"]
    if (
        not isinstance(token_counts, Mapping)
        or set(token_counts) != {f"v{index}" for index in range(5)}
        or any(type(value) is not int or value < 0 for value in token_counts.values())
    ):
        raise PredictiveControlInvariantError("belief token counts are invalid")


def scan_predictor_input_leakage(payload: Any) -> dict[str, Any]:
    """Scan the predictor input boundary for explicitly forbidden private fields."""

    findings: list[dict[str, str]] = []

    def visit(value: Any, path: str) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                field = str(key)
                child_path = f"{path}.{field}" if path else field
                if field.lower() in _FORBIDDEN_PREDICTOR_FIELDS:
                    findings.append({"field": field, "path": child_path})
                visit(child, child_path)
        elif isinstance(value, (list, tuple)):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")

    visit(payload, "")
    findings.sort(key=lambda item: (item["field"], item["path"]))
    return {
        "schema_version": "ego.life_playground.predictor_leakage_scan.v1",
        "producer_function": (
            "ego_life_playground_v0.predictive_control.scan_predictor_input_leakage"
        ),
        "clean": not findings,
        "findings": findings,
        "input_hash": _canonical_hash(payload),
    }


def validate_predictor_input(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the complete goal/private-world-free predictor input surface."""

    leakage = scan_predictor_input_leakage(payload)
    if not leakage["clean"]:
        raise PredictiveControlInvariantError("predictor input contains forbidden private fields")
    if not isinstance(payload, Mapping) or set(payload) != {
        "observation",
        "organism",
        "belief_summary",
    }:
        raise PredictiveControlInvariantError("predictor input schema mismatch")
    _validate_observation(payload["observation"])
    _validate_organism(payload["organism"])
    _validate_belief_summary(payload["belief_summary"])
    return {
        "observation": deepcopy(dict(payload["observation"])),
        "organism": {key: float(payload["organism"][key]) for key in STATE_KEYS},
        "belief_summary": deepcopy(dict(payload["belief_summary"])),
    }


def predictor_input_snapshot(
    state: Mapping[str, Any],
    *,
    observation: Mapping[str, Any],
    organism: Mapping[str, float],
    relative_map_mode: str,
) -> dict[str, Any]:
    """Return the validated, auditable predictor input without planning or updating."""

    validate_state(state)
    _validate_observation(observation)
    _validate_organism(organism)
    if relative_map_mode not in RELATIVE_MAP_MODES:
        raise PredictiveControlInvariantError("relative map mode is invalid")
    return _predictor_input(
        state,
        observation=observation,
        organism=organism,
        relative_map_mode=relative_map_mode,
    )


def _validate_weight_array(name: str, value: Any, shape: tuple[int, ...]) -> None:
    try:
        array = np.asarray(value, dtype=object)
    except (TypeError, ValueError) as exc:
        raise PredictiveControlInvariantError(f"{name} shape mismatch") from exc
    if array.shape != shape:
        raise PredictiveControlInvariantError(f"{name} shape mismatch")
    if any(type(item) is not float for item in array.flat):
        raise PredictiveControlInvariantError(f"{name} must contain floats")
    if any(not math.isfinite(item) for item in array.flat):
        raise PredictiveControlInvariantError(f"{name} must be finite")


def validate_state(state: Mapping[str, Any]) -> None:
    numeric_runtime_contract()
    if not isinstance(state, Mapping) or set(state) != {
        "schema_version",
        "belief",
        "exploration",
        "model",
    }:
        raise PredictiveControlInvariantError("predictive control state schema mismatch")
    if state["schema_version"] != STATE_SCHEMA_VERSION:
        raise PredictiveControlInvariantError("predictive control state version mismatch")
    belief = state["belief"]
    if (
        not isinstance(belief, Mapping)
        or set(belief) != {
            "schema_version",
            "episode_index",
            "relative_pose",
            "relative_facing",
            "cells",
            "observation_count",
        }
        or belief.get("schema_version") != BELIEF_SCHEMA_VERSION
        or type(belief.get("episode_index")) is not int
        or belief["episode_index"] < 0
        or type(belief.get("observation_count")) is not int
        or belief["observation_count"] < 0
    ):
        raise PredictiveControlInvariantError("relative belief schema mismatch")
    pose = belief["relative_pose"]
    if not isinstance(pose, list) or len(pose) != 2 or any(type(value) is not int for value in pose):
        raise PredictiveControlInvariantError("relative belief pose is invalid")
    if belief["relative_facing"] not in FACING_ORDER or not isinstance(belief["cells"], Mapping):
        raise PredictiveControlInvariantError("relative belief facing/cells are invalid")
    for cell_key, token in belief["cells"].items():
        try:
            x_text, y_text = str(cell_key).split(",", 1)
            int(x_text)
            int(y_text)
        except (ValueError, TypeError) as exc:
            raise PredictiveControlInvariantError("relative belief cell key is invalid") from exc
        if token not in _VISIBLE_TOKENS - {"self", "occluded"}:
            raise PredictiveControlInvariantError("relative belief cell token is invalid")
    exploration = state["exploration"]
    if (
        not isinstance(exploration, Mapping)
        or set(exploration)
        != {
            "schema_version",
            "action_exposure_counts",
            "token_interaction_counts",
            "coverage_step",
        }
        or exploration.get("schema_version") != EXPLORATION_SCHEMA_VERSION
        or type(exploration.get("coverage_step")) is not int
        or exploration["coverage_step"] < 0
        or not isinstance(exploration.get("action_exposure_counts"), Mapping)
        or set(exploration["action_exposure_counts"]) != set(ACTIONS)
        or any(
            type(count) is not int or count < 0
            for count in exploration["action_exposure_counts"].values()
        )
        or not isinstance(exploration.get("token_interaction_counts"), Mapping)
        or set(exploration["token_interaction_counts"])
        != {f"v{index}" for index in range(5)}
        or any(
            type(count) is not int or count < 0
            for count in exploration["token_interaction_counts"].values()
        )
    ):
        raise PredictiveControlInvariantError("predictive exploration state mismatch")
    model = state["model"]
    if (
        not isinstance(model, Mapping)
        or set(model)
        != {
            "schema_version",
            "algorithm",
            "outcome_weights",
            "delta_weights",
            "resource_weights",
            "terminal_weights",
            "visit_counts",
            "update_count",
        }
        or model.get("schema_version") != MODEL_SCHEMA_VERSION
        or model.get("algorithm") != ALGORITHM
        or type(model.get("update_count")) is not int
        or model["update_count"] < 0
        or not isinstance(model.get("visit_counts"), Mapping)
    ):
        raise PredictiveControlInvariantError("predictor model schema mismatch")
    _validate_weight_array(
        "outcome_weights",
        model["outcome_weights"],
        (len(ACTIONS), len(OUTCOMES), len(FEATURE_NAMES)),
    )
    _validate_weight_array(
        "delta_weights",
        model["delta_weights"],
        (len(ACTIONS), len(STATE_KEYS), len(FEATURE_NAMES)),
    )
    _validate_weight_array(
        "resource_weights",
        model["resource_weights"],
        (len(ACTIONS), len(FEATURE_NAMES)),
    )
    _validate_weight_array(
        "terminal_weights",
        model["terminal_weights"],
        (len(ACTIONS), len(FEATURE_NAMES)),
    )
    for key, count in model["visit_counts"].items():
        if type(key) is not str or len(key) != 64 or type(count) is not int or count < 1:
            raise PredictiveControlInvariantError("predictor visit count is invalid")


def _compiled_model_arrays(model: Mapping[str, Any]) -> dict[str, np.ndarray]:
    """Compile the serialized fixed arrays exactly once per public operation."""

    numeric_runtime_contract()
    return {
        "outcome_weights": np.asarray(model["outcome_weights"], dtype=NUMERIC_DTYPE),
        "delta_weights": np.asarray(model["delta_weights"], dtype=NUMERIC_DTYPE),
        "resource_weights": np.asarray(model["resource_weights"], dtype=NUMERIC_DTYPE),
        "terminal_weights": np.asarray(model["terminal_weights"], dtype=NUMERIC_DTYPE),
    }


def model_hash(state: Mapping[str, Any]) -> str:
    validate_state(state)
    return _canonical_hash(state["model"])


def belief_hash(state: Mapping[str, Any]) -> str:
    validate_state(state)
    return _canonical_hash(state["belief"])


def exploration_hash(state: Mapping[str, Any]) -> str:
    validate_state(state)
    return _canonical_hash(state["exploration"])


def reset_for_respawn(state: Mapping[str, Any], *, episode_index: int) -> dict[str, Any]:
    validate_state(state)
    if type(episode_index) is not int or episode_index < 0:
        raise PredictiveControlInvariantError("episode_index must be non-negative")
    updated = dict(state)
    updated["belief"] = _empty_belief(episode_index)
    return updated


def _rotate_local(dx: int, dy: int, facing: str) -> tuple[int, int]:
    if facing == "N":
        return dx, dy
    if facing == "E":
        return -dy, dx
    if facing == "S":
        return -dx, -dy
    return dy, -dx


def _integrate_observation(belief: Mapping[str, Any], observation: Mapping[str, Any]) -> dict[str, Any]:
    next_belief = dict(belief)
    cells = dict(belief["cells"])
    pose_x, pose_y = belief["relative_pose"]
    facing = str(belief["relative_facing"])
    for row_index, row in enumerate(observation["visual"]):
        for column_index, token in enumerate(row):
            if token in {"self", "occluded"}:
                continue
            dx, dy = _rotate_local(column_index - 2, row_index - 2, facing)
            cells[f"{pose_x + dx},{pose_y + dy}"] = token
    next_belief["cells"] = cells
    next_belief["observation_count"] = int(belief["observation_count"]) + 1
    return next_belief


def observe_belief(
    state: Mapping[str, Any],
    *,
    observation: Mapping[str, Any],
    episode_index: int,
    mode: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_state(state)
    _validate_observation(observation)
    if mode not in RELATIVE_MAP_MODES:
        raise PredictiveControlInvariantError("relative map mode is invalid")
    if type(episode_index) is not int or episode_index < 0:
        raise PredictiveControlInvariantError("episode_index must be non-negative")
    base = state
    reset_applied = int(state["belief"]["episode_index"]) != episode_index
    if reset_applied:
        base = reset_for_respawn(state, episode_index=episode_index)
    before_hash = _canonical_hash(base["belief"])
    if mode == "off":
        return dict(base), {
            "applied": False,
            "reason": "relative_map_off",
            "reset_applied": reset_applied,
            "belief_hash_before": before_hash,
            "belief_hash_after": before_hash,
        }
    updated = dict(base)
    updated["belief"] = _integrate_observation(base["belief"], observation)
    return updated, {
        "applied": True,
        "reason": "visible_observation_integrated",
        "reset_applied": reset_applied,
        "belief_hash_before": before_hash,
        "belief_hash_after": _canonical_hash(updated["belief"]),
        "known_cell_count": len(updated["belief"]["cells"]),
    }


def _front_position(belief: Mapping[str, Any]) -> tuple[int, int]:
    x, y = belief["relative_pose"]
    dx, dy = FACING_DELTAS[str(belief["relative_facing"])]
    return int(x) + dx, int(y) + dy


def _belief_summary_at(
    belief: Mapping[str, Any],
    *,
    pose: tuple[int, int],
    facing: str,
    observation: Mapping[str, Any] | None,
) -> dict[str, Any]:
    cells = belief["cells"]
    token_counts = {f"v{index}": 0 for index in range(5)}
    for token in cells.values():
        if token in token_counts:
            token_counts[token] += 1
    if observation is not None:
        front_token = observation["visual"][1][2]
    else:
        dx, dy = FACING_DELTAS[facing]
        front_token = cells.get(f"{pose[0] + dx},{pose[1] + dy}", "occluded")
    return {
        "relative_pose": [pose[0], pose[1]],
        "relative_facing": facing,
        "known_cell_count": len(cells),
        "known_object_count": sum(1 for token in cells.values() if token.startswith("v")),
        "front_token": front_token,
        "token_counts": token_counts,
    }


def _belief_summary(
    belief: Mapping[str, Any], observation: Mapping[str, Any] | None
) -> dict[str, Any]:
    return _belief_summary_at(
        belief,
        pose=(int(belief["relative_pose"][0]), int(belief["relative_pose"][1])),
        facing=str(belief["relative_facing"]),
        observation=observation,
    )


def _predictor_input(
    state: Mapping[str, Any],
    *,
    observation: Mapping[str, Any],
    organism: Mapping[str, float],
    relative_map_mode: str,
) -> dict[str, Any]:
    belief = state["belief"] if relative_map_mode == "relative" else _empty_belief(
        int(state["belief"]["episode_index"])
    )
    summary = _belief_summary(belief, observation)
    return validate_predictor_input(
        {
            "observation": observation,
            "organism": organism,
            "belief_summary": summary,
        }
    )


def _feature_vector_from_summary(
    *, organism: Mapping[str, float], summary: Mapping[str, Any]
) -> np.ndarray:
    front = str(summary["front_token"])
    known = int(summary["known_cell_count"])
    objects = int(summary["known_object_count"])
    vector = np.zeros(len(FEATURE_NAMES), dtype=NUMERIC_DTYPE)
    vector[FEATURE_INDEX["bias"]] = 1.0
    vector[FEATURE_INDEX["energy"]] = float(organism["energy"])
    vector[FEATURE_INDEX["safety"]] = float(organism["safety"])
    vector[FEATURE_INDEX["connection"]] = float(organism["connection"])
    vector[FEATURE_INDEX["stimulation"]] = float(organism["stimulation"])
    if front in {"empty", "wall", "occluded"}:
        vector[FEATURE_INDEX[f"front_{front}"]] = 1.0
    elif front.startswith("v") and f"front_{front}" in FEATURE_INDEX:
        vector[FEATURE_INDEX[f"front_{front}"]] = 1.0
    vector[FEATURE_INDEX["known_cell_fraction"]] = min(1.0, known / 81.0)
    vector[FEATURE_INDEX["known_object_fraction"]] = min(1.0, objects / 5.0)
    return vector


def _feature_mapping_from_vector(vector: np.ndarray) -> dict[str, float]:
    return {
        feature: float(vector[FEATURE_INDEX[feature]])
        for feature in FEATURE_NAMES
    }


def _features(payload: Mapping[str, Any]) -> dict[str, float]:
    return _feature_mapping_from_vector(
        _feature_vector_from_summary(
            organism=payload["organism"],
            summary=payload["belief_summary"],
        )
    )


def _softmax_array(logits: np.ndarray, *, round_values: bool = True) -> dict[str, float]:
    maximum = max(float(value) for value in logits)
    exponentials = [math.exp(float(value) - maximum) for value in logits]
    total = sum(exponentials)
    values = [value / total for value in exponentials]
    if round_values:
        return {
            outcome: _round(float(values[OUTCOME_INDEX[outcome]]))
            for outcome in OUTCOMES
        }
    return {
        outcome: float(values[OUTCOME_INDEX[outcome]])
        for outcome in OUTCOMES
    }


def _ordered_dot(weights: np.ndarray, features: np.ndarray) -> float:
    products = np.multiply(weights, features, dtype=NUMERIC_DTYPE)
    return (
        float(products[0])
        + float(products[1])
        + float(products[2])
        + float(products[3])
        + float(products[4])
        + float(products[5])
        + float(products[6])
        + float(products[7])
        + float(products[8])
        + float(products[9])
        + float(products[10])
        + float(products[11])
        + float(products[12])
        + float(products[13])
        + float(products[14])
    )


def _visit_key(action: str, payload: Mapping[str, Any]) -> str:
    summary = payload["belief_summary"]
    return _canonical_hash(
        {
            "action": action,
            "front_token": summary["front_token"],
            "energy_decile": int(float(payload["organism"]["energy"]) * 10),
            "known_object_count": summary["known_object_count"],
        }
    )


def _predict_from_payload(
    state: Mapping[str, Any],
    payload: Mapping[str, Any],
    action: str,
    *,
    include_hashes: bool = True,
    precomputed_features: np.ndarray | None = None,
    compiled_model: dict[str, np.ndarray] | None = None,
    visit_key_cache: dict[tuple[Any, ...], str] | None = None,
) -> dict[str, Any]:
    if action not in ACTIONS:
        raise PredictiveControlInvariantError("predictor action is invalid")
    feature_vector = (
        _feature_vector_from_summary(
            organism=payload["organism"],
            summary=payload["belief_summary"],
        )
        if precomputed_features is None
        else precomputed_features
    )
    compiled = (
        _compiled_model_arrays(state["model"])
        if compiled_model is None
        else compiled_model
    )
    action_index = ACTION_INDEX[action]
    outcome_logits = np.asarray(
        [
            _ordered_dot(compiled["outcome_weights"][action_index, outcome_index], feature_vector)
            for outcome_index in range(len(OUTCOMES))
        ],
        dtype=NUMERIC_DTYPE,
    )
    probabilities = _softmax_array(outcome_logits, round_values=include_hashes)
    visit_descriptor = (
        action,
        payload["belief_summary"]["front_token"],
        int(float(payload["organism"]["energy"]) * 10),
        payload["belief_summary"]["known_object_count"],
    )
    visit_key = None if visit_key_cache is None else visit_key_cache.get(visit_descriptor)
    if visit_key is None:
        visit_key = _visit_key(action, payload)
        if visit_key_cache is not None:
            visit_key_cache[visit_descriptor] = visit_key
    visit_count = int(state["model"]["visit_counts"].get(visit_key, 0))
    round_prediction = _round if include_hashes else float
    prediction = {
        "schema_version": PREDICTION_SCHEMA_VERSION,
        "producer_function": "ego_life_playground_v0.predictive_control.predict_action",
        "input_hash": _canonical_hash(payload) if include_hashes else None,
        "feature_hash": (
            _canonical_hash(_feature_mapping_from_vector(feature_vector))
            if include_hashes
            else None
        ),
        "action": action,
        "outcome_probabilities": probabilities,
        "predicted_delta": {
            key: round_prediction(
                max(
                    -0.35,
                    min(
                        0.35,
                        _ordered_dot(
                            compiled["delta_weights"][action_index, STATE_INDEX[key]],
                            feature_vector,
                        ),
                    ),
                )
            )
            for key in STATE_KEYS
        },
        "resource_interaction_probability": round_prediction(
            _sigmoid(
                _ordered_dot(compiled["resource_weights"][action_index], feature_vector)
            )
        ),
        "terminal_risk": round_prediction(
            _sigmoid(
                _ordered_dot(compiled["terminal_weights"][action_index], feature_vector)
            )
        ),
        "uncertainty": round_prediction(1.0 / math.sqrt(1.0 + visit_count)),
        "visit_count": visit_count,
    }
    return prediction


def predict_action(
    state: Mapping[str, Any],
    *,
    observation: Mapping[str, Any],
    organism: Mapping[str, float],
    action: str,
    relative_map_mode: str,
) -> dict[str, Any]:
    validate_state(state)
    if relative_map_mode not in RELATIVE_MAP_MODES:
        raise PredictiveControlInvariantError("relative map mode is invalid")
    payload = _predictor_input(
        state,
        observation=observation,
        organism=organism,
        relative_map_mode=relative_map_mode,
    )
    return _predict_from_payload(state, payload, action)


def _turn(facing: str, direction: int) -> str:
    index = FACING_ORDER.index(facing)
    return FACING_ORDER[(index + direction) % len(FACING_ORDER)]


def _advance_belief_pose(
    belief: Mapping[str, Any], *, action: str, outcome_type: str
) -> dict[str, Any]:
    updated = dict(belief)
    if action == "turn_left":
        updated["relative_facing"] = _turn(str(belief["relative_facing"]), -1)
    elif action == "turn_right":
        updated["relative_facing"] = _turn(str(belief["relative_facing"]), 1)
    elif action == "move_forward" and outcome_type == "moved":
        dx, dy = FACING_DELTAS[str(belief["relative_facing"])]
        updated["relative_pose"] = [
            int(belief["relative_pose"][0]) + dx,
            int(belief["relative_pose"][1]) + dy,
        ]
    return updated


def _pose_after(
    pose: tuple[int, int], facing: str, *, action: str, outcome_type: str
) -> tuple[int, int, str]:
    if action == "turn_left" and outcome_type == "turned":
        return pose[0], pose[1], _turn(facing, -1)
    if action == "turn_right" and outcome_type == "turned":
        return pose[0], pose[1], _turn(facing, 1)
    if action == "move_forward" and outcome_type == "moved":
        dx, dy = FACING_DELTAS[facing]
        return pose[0] + dx, pose[1] + dy, facing
    return pose[0], pose[1], facing


def _unknown_fraction(belief: Mapping[str, Any], pose: tuple[int, int]) -> float:
    cells = belief["cells"]
    unknown = sum(
        1
        for dy in range(-2, 3)
        for dx in range(-2, 3)
        if f"{pose[0] + dx},{pose[1] + dy}" not in cells
    )
    return _round(unknown / 25.0)


def _expected_pose_distribution(
    *,
    pose: tuple[int, int],
    facing: str,
    action: str,
    outcome_probabilities: Mapping[str, float],
) -> dict[tuple[int, int, str], float]:
    stay = (pose[0], pose[1], facing)
    if action == "move_forward":
        changed_outcome = "moved"
    elif action in {"turn_left", "turn_right"}:
        changed_outcome = "turned"
    else:
        changed_outcome = None
    if changed_outcome is None:
        return {stay: 1.0}
    changed = _pose_after(
        pose, facing, action=action, outcome_type=changed_outcome
    )
    changed_probability = float(outcome_probabilities[changed_outcome])
    successor_mass = {stay: 1.0 - changed_probability}
    successor_mass[changed] = successor_mass.get(changed, 0.0) + changed_probability
    successor_mass = {key: value for key, value in successor_mass.items() if value > 0.0}
    total_mass = sum(successor_mass.values())
    if total_mass <= 0.0:
        raise PredictiveControlInvariantError("outcome probability mass vanished")
    return {key: value / total_mass for key, value in successor_mass.items()}


def expected_pose_receipt(
    *,
    belief: Mapping[str, Any],
    pose: tuple[int, int],
    facing: str,
    action: str,
    outcome_probabilities: Mapping[str, float],
) -> dict[str, Any]:
    """Compute the planner's probability-weighted relative-pose information value."""

    if (
        not isinstance(belief, Mapping)
        or belief.get("schema_version") != BELIEF_SCHEMA_VERSION
        or not isinstance(belief.get("cells"), Mapping)
    ):
        raise PredictiveControlInvariantError("expected pose belief is invalid")
    if (
        not isinstance(pose, tuple)
        or len(pose) != 2
        or any(type(item) is not int for item in pose)
        or facing not in FACING_ORDER
        or action not in ACTIONS
    ):
        raise PredictiveControlInvariantError("expected pose request is invalid")
    if (
        not isinstance(outcome_probabilities, Mapping)
        or set(outcome_probabilities) != set(OUTCOMES)
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) < 0.0
            for value in outcome_probabilities.values()
        )
        or abs(sum(float(value) for value in outcome_probabilities.values()) - 1.0)
        > 1e-9
    ):
        raise PredictiveControlInvariantError("outcome probabilities are invalid")
    distribution = _expected_pose_distribution(
        pose=pose,
        facing=facing,
        action=action,
        outcome_probabilities=outcome_probabilities,
    )
    expected_unknown = sum(
        probability * _unknown_fraction(belief, (pose_x, pose_y))
        for (pose_x, pose_y, _next_facing), probability in distribution.items()
    )
    return {
        "schema_version": "ego.life_playground.expected_pose_receipt.v1",
        "producer_function": (
            "ego_life_playground_v0.predictive_control.expected_pose_receipt"
        ),
        "successor_distribution": [
            [pose_x, pose_y, next_facing, _round(probability)]
            for (pose_x, pose_y, next_facing), probability in sorted(
                distribution.items()
            )
        ],
        "expected_newly_observable_unknown_fraction": _round(expected_unknown),
        "map_information_value": _round(0.20 * expected_unknown),
    }


def _value_breakdown(
    organism: Mapping[str, float],
    *,
    expected_delta: Mapping[str, float],
    predicted_terminal_risk: float,
    expected_newly_observable_unknown_fraction: float,
    active_goal: str,
    goal_value_mode: str,
) -> dict[str, float]:
    predicted_after = {
        key: _clamp(float(organism[key]) + float(expected_delta[key]))
        for key in STATE_KEYS
    }
    changes = {
        key: _round(
            max(0.0, TARGET_LEVEL - float(organism[key]))
            - max(0.0, TARGET_LEVEL - predicted_after[key])
        )
        for key in STATE_KEYS
    }
    weights = {
        key: (
            2.0
            if goal_value_mode == "contextual" and active_goal == key
            else 1.0
        )
        for key in STATE_KEYS
    }
    survival_value = _round(1.0 - predicted_terminal_risk)
    homeostatic_value = _round(
        sum(weights[key] * changes[key] for key in STATE_KEYS)
    )
    map_information_value = _round(
        0.20 * expected_newly_observable_unknown_fraction
    )
    return {
        "total_deficit_change": _round(sum(changes.values())),
        "intent_deficit_change": (
            0.0 if active_goal == "explore" else _round(changes[active_goal])
        ),
        "predicted_terminal_risk": _round(predicted_terminal_risk),
        "expected_newly_observable_unknown_fraction": _round(
            expected_newly_observable_unknown_fraction
        ),
        "survival_value": survival_value,
        "homeostatic_value": homeostatic_value,
        "map_information_value": map_information_value,
        "total": _round(survival_value + homeostatic_value + map_information_value),
    }


def _serialized_pose_distribution(
    pose_distribution: Mapping[tuple[int, int, str], float]
) -> list[list[Any]]:
    return [
        [pose_x, pose_y, facing, _round(probability)]
        for (pose_x, pose_y, facing), probability in sorted(pose_distribution.items())
    ]


def _node_sort_key(node: Mapping[str, Any]) -> tuple[Any, ...]:
    return (
        -float(node["score"]),
        tuple(ACTIONS.index(action) for action in node["actions"]),
        tuple(
            (pose_x, pose_y, facing, _round(probability))
            for (pose_x, pose_y, facing), probability in sorted(
                node["pose_distribution"].items()
            )
        ),
    )


def _prediction_for_pose(
    state: Mapping[str, Any],
    *,
    belief: Mapping[str, Any],
    pose: tuple[int, int],
    facing: str,
    observation: Mapping[str, Any] | None,
    organism: Mapping[str, float],
    action: str,
    compiled_model: dict[str, np.ndarray],
    prediction_cache: dict[tuple[Any, ...], dict[str, Any]],
    summary_cache: dict[tuple[int, int, str, bool], dict[str, Any]],
    visit_key_cache: dict[tuple[Any, ...], str],
) -> dict[str, Any]:
    summary_key = (pose[0], pose[1], facing, observation is not None)
    summary = summary_cache.get(summary_key)
    if summary is None:
        summary = _belief_summary_at(
            belief,
            pose=pose,
            facing=facing,
            observation=observation,
        )
        summary_cache[summary_key] = summary
    organism_tuple = tuple(float(organism[key]) for key in STATE_KEYS)
    cache_key = (
        ACTION_INDEX[action],
        organism_tuple,
        str(summary["front_token"]),
        int(summary["known_cell_count"]),
        int(summary["known_object_count"]),
    )
    prediction = prediction_cache.get(cache_key)
    if prediction is None:
        feature_vector = _feature_vector_from_summary(
            organism=organism,
            summary=summary,
        )
        payload = {
            "observation": observation,
            "organism": organism,
            "belief_summary": summary,
        }
        prediction = _predict_from_payload(
            state,
            payload,
            action,
            include_hashes=False,
            precomputed_features=feature_vector,
            compiled_model=compiled_model,
            visit_key_cache=visit_key_cache,
        )
        prediction_cache[cache_key] = prediction
    return prediction


def _expand_node(
    state: Mapping[str, Any],
    node: Mapping[str, Any],
    *,
    action: str,
    belief: Mapping[str, Any],
    observation: Mapping[str, Any] | None,
    active_goal: str,
    goal_value_mode: str,
    depth: int,
    discount: float,
    compiled_model: dict[str, np.ndarray],
    prediction_cache: dict[tuple[Any, ...], dict[str, Any]],
    summary_cache: dict[tuple[int, int, str, bool], dict[str, Any]],
    unknown_cache: dict[tuple[int, int], float],
    visit_key_cache: dict[tuple[Any, ...], str],
) -> dict[str, Any]:
    successor_mass: dict[tuple[int, int, str], float] = {}
    expected_delta = {key: 0.0 for key in STATE_KEYS}
    expected_terminal_risk = 0.0
    expected_resource_probability = 0.0
    expected_uncertainty = 0.0
    for pose_key, pose_probability in node["pose_distribution"].items():
        pose_x, pose_y, facing = pose_key
        prediction = _prediction_for_pose(
            state,
            belief=belief,
            pose=(pose_x, pose_y),
            facing=facing,
            observation=observation,
            organism=node["organism"],
            action=action,
            compiled_model=compiled_model,
            prediction_cache=prediction_cache,
            summary_cache=summary_cache,
            visit_key_cache=visit_key_cache,
        )
        for key in STATE_KEYS:
            expected_delta[key] += pose_probability * float(
                prediction["predicted_delta"][key]
            )
        expected_terminal_risk += pose_probability * float(prediction["terminal_risk"])
        expected_resource_probability += pose_probability * float(
            prediction["resource_interaction_probability"]
        )
        expected_uncertainty += pose_probability * float(prediction["uncertainty"])
        local_successors = _expected_pose_distribution(
            pose=(pose_x, pose_y),
            facing=facing,
            action=action,
            outcome_probabilities=prediction["outcome_probabilities"],
        )
        for successor, successor_probability in local_successors.items():
            successor_mass[successor] = successor_mass.get(successor, 0.0) + (
                pose_probability * successor_probability
            )
    total_mass = sum(successor_mass.values())
    if total_mass <= 0.0:
        raise PredictiveControlInvariantError("beam successor probability mass vanished")
    successor_distribution = {
        key: value / total_mass for key, value in successor_mass.items()
    }
    expected_unknown = 0.0
    for (pose_x, pose_y, _facing), probability in successor_distribution.items():
        pose = (pose_x, pose_y)
        unknown = unknown_cache.get(pose)
        if unknown is None:
            unknown = _unknown_fraction(belief, pose)
            unknown_cache[pose] = unknown
        expected_unknown += probability * unknown
    rounded_delta = {key: _round(value) for key, value in expected_delta.items()}
    breakdown = _value_breakdown(
        node["organism"],
        expected_delta=rounded_delta,
        predicted_terminal_risk=expected_terminal_risk,
        expected_newly_observable_unknown_fraction=expected_unknown,
        active_goal=active_goal,
        goal_value_mode=goal_value_mode,
    )
    next_organism = {
        key: _clamp(float(node["organism"][key]) + rounded_delta[key])
        for key in STATE_KEYS
    }
    actions = [*node["actions"], action]
    return {
        "root_action": actions[0],
        "actions": actions,
        "pose_distribution": successor_distribution,
        "organism": next_organism,
        "score": _round(
            float(node["score"]) + (discount**depth) * float(breakdown["total"])
        ),
        "first_breakdown": node["first_breakdown"] or breakdown,
        "last_prediction_summary": {
            "terminal_risk": _round(expected_terminal_risk),
            "resource_interaction_probability": _round(expected_resource_probability),
            "uncertainty": _round(expected_uncertainty),
            "predicted_delta": rounded_delta,
        },
    }


def _retain_global_beam(nodes: list[dict[str, Any]], beam_width: int) -> list[dict[str, Any]]:
    ordered = sorted(nodes, key=_node_sort_key)
    retained: list[dict[str, Any]] = []
    used_ids: set[int] = set()
    for action in ACTIONS:
        best = next(node for node in ordered if node["root_action"] == action)
        retained.append(best)
        used_ids.add(id(best))
    for node in ordered:
        if len(retained) >= beam_width:
            break
        if id(node) not in used_ids:
            retained.append(node)
            used_ids.add(id(node))
    return sorted(retained, key=_node_sort_key)


def _deterministic_action_order(
    actions: tuple[str, ...] | list[str],
    *,
    run_seed: int = 0,
    episode_index: int = 0,
    sequence: int = 1,
    current_belief_hash: str,
) -> list[str]:
    return sorted(
        actions,
        key=lambda action: _canonical_hash(
            {
                "producer": "ego_life_playground_v0.predictive_control.deterministic_order",
                "run_seed": run_seed,
                "episode_index": episode_index,
                "sequence": sequence,
                "belief_hash": current_belief_hash,
                "action": action,
            }
        ),
    )


def plan_action(
    *,
    state: Mapping[str, Any],
    observation: Mapping[str, Any],
    organism: Mapping[str, float],
    active_goal: str,
    heuristic_scores: Mapping[str, float],
    horizon: int = HORIZON,
    beam_width: int = BEAM_WIDTH,
    discount: float = DISCOUNT,
    relative_map_mode: str = "relative",
    goal_value_mode: str = "contextual",
    action_costs: Mapping[str, float],
    run_seed: int = 0,
    episode_index: int = 0,
    sequence: int = 1,
) -> dict[str, Any]:
    validate_state(state)
    _validate_observation(observation)
    _validate_organism(organism)
    if active_goal not in {*STATE_KEYS, "explore"}:
        raise PredictiveControlInvariantError("active goal is invalid")
    if (
        not isinstance(heuristic_scores, Mapping)
        or set(heuristic_scores) != set(ACTIONS)
        or any(not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)) for value in heuristic_scores.values())
    ):
        raise PredictiveControlInvariantError("heuristic tie scores are invalid")
    if type(horizon) is not int or not 1 <= horizon <= HORIZON:
        raise PredictiveControlInvariantError("planning horizon is invalid")
    if type(beam_width) is not int or beam_width != BEAM_WIDTH:
        raise PredictiveControlInvariantError("beam width is invalid")
    if type(discount) is not float or discount != DISCOUNT:
        raise PredictiveControlInvariantError("planning discount is invalid")
    if relative_map_mode not in RELATIVE_MAP_MODES or goal_value_mode not in GOAL_VALUE_MODES:
        raise PredictiveControlInvariantError("planning ablation mode is invalid")
    if not isinstance(action_costs, Mapping) or set(action_costs) != set(ACTIONS):
        raise PredictiveControlInvariantError("planning action costs are invalid")
    if type(run_seed) is not int:
        raise PredictiveControlInvariantError("planning run_seed must be an integer")
    if type(episode_index) is not int or episode_index < 0:
        raise PredictiveControlInvariantError("planning episode_index is invalid")
    if type(sequence) is not int or sequence < 1:
        raise PredictiveControlInvariantError("planning sequence is invalid")
    current_payload = _predictor_input(
        state,
        observation=observation,
        organism=organism,
        relative_map_mode=relative_map_mode,
    )
    compiled_model = _compiled_model_arrays(state["model"])
    current_features = _feature_vector_from_summary(
        organism=current_payload["organism"],
        summary=current_payload["belief_summary"],
    )
    predictions = {
        action: _predict_from_payload(
            state,
            current_payload,
            action,
            precomputed_features=current_features,
            compiled_model=compiled_model,
        )
        for action in ACTIONS
    }
    base_belief = (
        state["belief"]
        if relative_map_mode == "relative"
        else _empty_belief(int(state["belief"]["episode_index"]))
    )
    pose = (
        int(base_belief["relative_pose"][0]),
        int(base_belief["relative_pose"][1]),
        str(base_belief["relative_facing"]),
    )
    beam: list[dict[str, Any]] = [
        {
            "root_action": None,
            "actions": [],
            "pose_distribution": {pose: 1.0},
            "organism": {key: float(organism[key]) for key in STATE_KEYS},
            "score": 0.0,
            "first_breakdown": None,
            "last_prediction_summary": None,
        }
    ]
    prediction_cache: dict[tuple[Any, ...], dict[str, Any]] = {}
    summary_cache: dict[tuple[int, int, str, bool], dict[str, Any]] = {}
    unknown_cache: dict[tuple[int, int], float] = {}
    visit_key_cache: dict[tuple[Any, ...], str] = {}
    expanded_by_depth: list[int] = []
    retained_by_depth: list[int] = []
    root_actions_by_depth: list[list[str]] = []
    probability_mass_normalized = True
    for depth in range(horizon):
        expanded = [
            _expand_node(
                state,
                node,
                action=action,
                belief=base_belief,
                observation=observation if depth == 0 else None,
                active_goal=active_goal,
                goal_value_mode=goal_value_mode,
                depth=depth,
                discount=discount,
                compiled_model=compiled_model,
                prediction_cache=prediction_cache,
                summary_cache=summary_cache,
                unknown_cache=unknown_cache,
                visit_key_cache=visit_key_cache,
            )
            for node in beam
            for action in ACTIONS
        ]
        expanded_by_depth.append(len(expanded))
        beam = (
            sorted(expanded, key=_node_sort_key)
            if len(expanded) <= beam_width
            else _retain_global_beam(expanded, beam_width)
        )
        retained_by_depth.append(len(beam))
        roots = [action for action in ACTIONS if any(node["root_action"] == action for node in beam)]
        root_actions_by_depth.append(roots)
        probability_mass_normalized = probability_mass_normalized and all(
            abs(sum(node["pose_distribution"].values()) - 1.0) <= 1e-9
            for node in beam
        )
    values: dict[str, Any] = {}
    for action in ACTIONS:
        best = min(
            (node for node in beam if node["root_action"] == action),
            key=_node_sort_key,
        )
        values[action] = {
            **{key: _round(value) for key, value in best["first_breakdown"].items()},
            "total": _round(float(best["score"])),
            "plan_actions": list(best["actions"][:3]),
            "resource_interaction_probability": _round(
                float(predictions[action]["resource_interaction_probability"])
            ),
            "trajectory_hash": _canonical_hash(
                {
                    "actions": best["actions"],
                    "score": best["score"],
                    "organism": best["organism"],
                    "pose_distribution": _serialized_pose_distribution(
                        best["pose_distribution"]
                    ),
                }
            ),
        }
    maximum_value = max(float(values[action]["total"]) for action in ACTIONS)
    value_ties = [
        action for action in ACTIONS if float(values[action]["total"]) == maximum_value
    ]
    tie_break_used = len(value_ties) > 1
    if tie_break_used:
        maximum_heuristic = max(float(heuristic_scores[action]) for action in value_ties)
        heuristic_ties = [
            action
            for action in value_ties
            if float(heuristic_scores[action]) == maximum_heuristic
        ]
        mpc_selected = _deterministic_action_order(
            heuristic_ties,
            run_seed=run_seed,
            episode_index=episode_index,
            sequence=sequence,
            current_belief_hash=_canonical_hash(state["belief"]),
        )[0]
        tie_break_source = "heuristic_score" if len(heuristic_ties) == 1 else "deterministic_hash"
    else:
        mpc_selected = value_ties[0]
        tie_break_source = "none"
    exploration = state["exploration"]
    exposure_counts = exploration["action_exposure_counts"]
    minimum_exposure = min(int(exposure_counts[action]) for action in ACTIONS)
    underexposed = [
        action
        for action in ACTIONS
        if int(exposure_counts[action]) == minimum_exposure
        and int(exposure_counts[action]) < ACTION_EXPOSURE_TARGET
    ]
    front_token = str(current_payload["belief_summary"]["front_token"])
    if underexposed:
        selected = _deterministic_action_order(
            underexposed,
            run_seed=run_seed,
            episode_index=episode_index,
            sequence=sequence,
            current_belief_hash=_canonical_hash(state["belief"]),
        )[0]
        selection_mode = "bounded_explore"
        exploration_reason = "action_coverage"
    elif (
        front_token in exploration["token_interaction_counts"]
        and int(exploration["token_interaction_counts"][front_token])
        < TOKEN_INTERACTION_TARGET
    ):
        selected = "interact"
        selection_mode = "bounded_explore"
        exploration_reason = "front_token_identification"
    else:
        selected = mpc_selected
        selection_mode = "mpc_exploit"
        exploration_reason = "none"
    return {
        "schema_version": PLAN_SCHEMA_VERSION,
        "producer_function": "ego_life_playground_v0.predictive_control.plan_action",
        "algorithm": ALGORITHM,
        "horizon": horizon,
        "beam_width": beam_width,
        "discount": discount,
        "relative_map_mode": relative_map_mode,
        "goal_value_mode": goal_value_mode,
        "active_goal": active_goal,
        "predictor_input_goal_independent": True,
        "predictions_by_action": predictions,
        "candidate_values": values,
        "selected_action": selected,
        "planned_actions": values[selected]["plan_actions"],
        "mpc_selected_action": mpc_selected,
        "selection_mode": selection_mode,
        "exploration_reason": exploration_reason,
        "action_exposure_counts": dict(exposure_counts),
        "token_interaction_counts": dict(exploration["token_interaction_counts"]),
        "coverage_step": int(exploration["coverage_step"]),
        "exploration_hash": _canonical_hash(exploration),
        "tie_break_used": tie_break_used,
        "tie_break_source": tie_break_source,
        "beam_receipt": {
            "expanded_by_depth": expanded_by_depth,
            "retained_by_depth": retained_by_depth,
            "root_actions_by_depth": root_actions_by_depth,
            "all_probability_mass_normalized": probability_mass_normalized,
        },
        "model_hash": _canonical_hash(state["model"]),
        "belief_hash": _canonical_hash(state["belief"]),
    }


def _updated_vector(
    row: np.ndarray,
    features: np.ndarray,
    multiplier: float,
) -> np.ndarray:
    return np.asarray(
        [
            _round(
                max(
                    -4.0,
                    min(
                        4.0,
                        float(row[index])
                        + LEARNING_RATE
                        * float(multiplier)
                        * float(features[index]),
                    ),
                )
            )
            for index in range(len(FEATURE_NAMES))
        ],
        dtype=NUMERIC_DTYPE,
    )


def update_after_transition(
    state: Mapping[str, Any],
    *,
    observation: Mapping[str, Any],
    organism_before: Mapping[str, float],
    action: str,
    actual_outcome_type: str,
    actual_delta: Mapping[str, float],
    terminal: bool,
    resource_interaction: bool,
    next_observation: Mapping[str, Any],
    episode_index: int,
    relative_map_mode: str,
    updates_enabled: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_state(state)
    if action not in ACTIONS or actual_outcome_type not in OUTCOMES:
        raise PredictiveControlInvariantError("predictor update action/outcome is invalid")
    _validate_observation(next_observation)
    if not isinstance(actual_delta, Mapping) or set(actual_delta) != set(STATE_KEYS):
        raise PredictiveControlInvariantError("predictor actual delta schema mismatch")
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) for value in actual_delta.values()):
        raise PredictiveControlInvariantError("predictor actual delta must be finite")
    if type(terminal) is not bool or type(resource_interaction) is not bool or type(updates_enabled) is not bool:
        raise PredictiveControlInvariantError("predictor update flags must be boolean")
    payload = _predictor_input(
        state,
        observation=observation,
        organism=organism_before,
        relative_map_mode=relative_map_mode,
    )
    compiled_model = _compiled_model_arrays(state["model"])
    feature_vector = _feature_vector_from_summary(
        organism=payload["organism"],
        summary=payload["belief_summary"],
    )
    prediction_before = _predict_from_payload(
        state,
        payload,
        action,
        precomputed_features=feature_vector,
        compiled_model=compiled_model,
    )
    before_hash = _canonical_hash(state["model"])
    updated = dict(state)
    exploration_before_hash = _canonical_hash(state["exploration"])
    exploration = deepcopy(dict(state["exploration"]))
    action_exposure_counts = dict(exploration["action_exposure_counts"])
    action_exposure_counts[action] = int(action_exposure_counts[action]) + 1
    exploration["action_exposure_counts"] = action_exposure_counts
    token_interaction_counts = dict(exploration["token_interaction_counts"])
    front_token = str(payload["belief_summary"]["front_token"])
    if action == "interact" and front_token in token_interaction_counts:
        token_interaction_counts[front_token] = int(token_interaction_counts[front_token]) + 1
    exploration["token_interaction_counts"] = token_interaction_counts
    exploration["coverage_step"] = int(exploration["coverage_step"]) + 1
    updated["exploration"] = exploration
    model = dict(state["model"])
    if updates_enabled:
        action_index = ACTION_INDEX[action]
        probabilities = prediction_before["outcome_probabilities"]
        for outcome in OUTCOMES:
            target = 1.0 if outcome == actual_outcome_type else 0.0
            outcome_index = OUTCOME_INDEX[outcome]
            compiled_model["outcome_weights"][action_index, outcome_index] = _updated_vector(
                compiled_model["outcome_weights"][action_index, outcome_index],
                feature_vector,
                target - float(probabilities[outcome]),
            )
        for key in STATE_KEYS:
            error = float(actual_delta[key]) - float(prediction_before["predicted_delta"][key])
            state_index = STATE_INDEX[key]
            compiled_model["delta_weights"][action_index, state_index] = _updated_vector(
                compiled_model["delta_weights"][action_index, state_index],
                feature_vector,
                error,
            )
        compiled_model["resource_weights"][action_index] = _updated_vector(
            compiled_model["resource_weights"][action_index],
            feature_vector,
            (1.0 if resource_interaction else 0.0)
            - float(prediction_before["resource_interaction_probability"]),
        )
        compiled_model["terminal_weights"][action_index] = _updated_vector(
            compiled_model["terminal_weights"][action_index],
            feature_vector,
            (1.0 if terminal else 0.0) - float(prediction_before["terminal_risk"]),
        )
        for field, array in compiled_model.items():
            model[field] = array.tolist()
        visit_counts = dict(model["visit_counts"])
        visit_key = _visit_key(action, payload)
        visit_counts[visit_key] = int(visit_counts.get(visit_key, 0)) + 1
        model["visit_counts"] = visit_counts
        model["update_count"] = int(model["update_count"]) + 1
        updated["model"] = model
    if relative_map_mode == "relative":
        belief = _advance_belief_pose(
            state["belief"], action=action, outcome_type=actual_outcome_type
        )
        updated["belief"] = _integrate_observation(belief, next_observation)
    elif relative_map_mode != "off":
        raise PredictiveControlInvariantError("relative map mode is invalid")
    prediction_after = _predict_from_payload(
        updated,
        payload,
        action,
        precomputed_features=feature_vector,
        compiled_model=compiled_model,
    )
    probability = max(1e-12, float(prediction_before["outcome_probabilities"][actual_outcome_type]))
    brier = sum(
        (
            float(prediction_before["outcome_probabilities"][outcome])
            - (1.0 if outcome == actual_outcome_type else 0.0)
        )
        ** 2
        for outcome in OUTCOMES
    )
    receipt = {
        "schema_version": UPDATE_SCHEMA_VERSION,
        "producer_function": "ego_life_playground_v0.predictive_control.update_after_transition",
        "applied": updates_enabled,
        "reason": "online_update" if updates_enabled else "predictor_updates_frozen",
        "action": action,
        "actual_outcome_type": actual_outcome_type,
        "resource_interaction": resource_interaction,
        "terminal": terminal,
        "prediction_before": prediction_before,
        "prediction_after": prediction_after,
        "outcome_brier": _round(brier),
        "outcome_nll": _round(-math.log(probability)),
        "delta_error": {
            key: _round(float(actual_delta[key]) - float(prediction_before["predicted_delta"][key]))
            for key in STATE_KEYS
        },
        "model_hash_before": before_hash,
        "model_hash_after": _canonical_hash(updated["model"]),
        "belief_hash_after": _canonical_hash(updated["belief"]),
        "exploration_hash_before": exploration_before_hash,
        "exploration_hash_after": _canonical_hash(updated["exploration"]),
        "action_exposure_counts_after": dict(action_exposure_counts),
        "token_interaction_counts_after": dict(token_interaction_counts),
        "coverage_step_after": int(exploration["coverage_step"]),
        "update_count_after": int(updated["model"]["update_count"]),
    }
    validate_state(updated)
    return updated, receipt


__all__ = [
    "ACTIONS",
    "ALGORITHM",
    "BEAM_WIDTH",
    "DISCOUNT",
    "GOAL_VALUE_MODES",
    "HORIZON",
    "OUTCOMES",
    "PredictiveControlInvariantError",
    "RELATIVE_MAP_MODES",
    "belief_hash",
    "empty_state",
    "expected_pose_receipt",
    "exploration_hash",
    "hyperparameters",
    "model_hash",
    "numeric_runtime_contract",
    "observe_belief",
    "plan_action",
    "predict_action",
    "predictor_input_snapshot",
    "reset_for_respawn",
    "scan_predictor_input_leakage",
    "update_after_transition",
    "validate_predictor_input",
    "validate_state",
]
