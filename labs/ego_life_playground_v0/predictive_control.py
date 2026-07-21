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
from typing import Any, Mapping

from .microworld import ACTIONS, FACING_DELTAS, FACING_ORDER, PUBLIC_OBSERVATION_SCHEMA_VERSION


STATE_SCHEMA_VERSION = "ego.life_playground.predictive_control.v1"
BELIEF_SCHEMA_VERSION = "ego.life_playground.relative_belief.v1"
MODEL_SCHEMA_VERSION = "ego.life_playground.factored_predictor.v1"
PREDICTION_SCHEMA_VERSION = "ego.life_playground.outcome_prediction.v1"
PLAN_SCHEMA_VERSION = "ego.life_playground.factored_plan.v1"
UPDATE_SCHEMA_VERSION = "ego.life_playground.predictor_update.v1"
ALGORITHM = "online_linear_softmax_factored_mpc"
LEARNING_RATE = 0.08
HORIZON = 12
BEAM_WIDTH = 16
DISCOUNT = 0.97
TARGET_LEVEL = 0.72
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


def hyperparameters() -> dict[str, Any]:
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
    }


def _zero_row() -> dict[str, float]:
    return {feature: 0.0 for feature in FEATURE_NAMES}


def _empty_action_model() -> dict[str, Any]:
    return {
        "outcome_weights": {outcome: _zero_row() for outcome in OUTCOMES},
        "delta_weights": {key: _zero_row() for key in STATE_KEYS},
        "resource_weights": _zero_row(),
        "terminal_weights": _zero_row(),
    }


def _empty_belief(episode_index: int = 0) -> dict[str, Any]:
    return {
        "schema_version": BELIEF_SCHEMA_VERSION,
        "episode_index": episode_index,
        "relative_pose": [0, 0],
        "relative_facing": "N",
        "cells": {},
        "observation_count": 0,
    }


def empty_state() -> dict[str, Any]:
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "belief": _empty_belief(),
        "model": {
            "schema_version": MODEL_SCHEMA_VERSION,
            "algorithm": ALGORITHM,
            "actions": {action: _empty_action_model() for action in ACTIONS},
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


def validate_predictor_input(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the complete goal/private-world-free predictor input surface."""

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


def _validate_weight_row(row: Any) -> None:
    if not isinstance(row, Mapping) or set(row) != set(FEATURE_NAMES):
        raise PredictiveControlInvariantError("predictor weight row schema mismatch")
    for value in row.values():
        if type(value) is not float or not math.isfinite(value):
            raise PredictiveControlInvariantError("predictor weight must be finite float")


def validate_state(state: Mapping[str, Any]) -> None:
    if not isinstance(state, Mapping) or set(state) != {"schema_version", "belief", "model"}:
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
    model = state["model"]
    if (
        not isinstance(model, Mapping)
        or set(model) != {"schema_version", "algorithm", "actions", "visit_counts", "update_count"}
        or model.get("schema_version") != MODEL_SCHEMA_VERSION
        or model.get("algorithm") != ALGORITHM
        or type(model.get("update_count")) is not int
        or model["update_count"] < 0
        or not isinstance(model.get("actions"), Mapping)
        or set(model["actions"]) != set(ACTIONS)
        or not isinstance(model.get("visit_counts"), Mapping)
    ):
        raise PredictiveControlInvariantError("predictor model schema mismatch")
    for action_model in model["actions"].values():
        if not isinstance(action_model, Mapping) or set(action_model) != {
            "outcome_weights",
            "delta_weights",
            "resource_weights",
            "terminal_weights",
        }:
            raise PredictiveControlInvariantError("predictor action model schema mismatch")
        if set(action_model["outcome_weights"]) != set(OUTCOMES):
            raise PredictiveControlInvariantError("predictor outcome weights mismatch")
        if set(action_model["delta_weights"]) != set(STATE_KEYS):
            raise PredictiveControlInvariantError("predictor delta weights mismatch")
        for row in action_model["outcome_weights"].values():
            _validate_weight_row(row)
        for row in action_model["delta_weights"].values():
            _validate_weight_row(row)
        _validate_weight_row(action_model["resource_weights"])
        _validate_weight_row(action_model["terminal_weights"])
    for key, count in model["visit_counts"].items():
        if type(key) is not str or len(key) != 64 or type(count) is not int or count < 1:
            raise PredictiveControlInvariantError("predictor visit count is invalid")


def model_hash(state: Mapping[str, Any]) -> str:
    validate_state(state)
    return _canonical_hash(state["model"])


def belief_hash(state: Mapping[str, Any]) -> str:
    validate_state(state)
    return _canonical_hash(state["belief"])


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


def _belief_summary(
    belief: Mapping[str, Any], observation: Mapping[str, Any] | None
) -> dict[str, Any]:
    cells = belief["cells"]
    token_counts = {f"v{index}": 0 for index in range(5)}
    for token in cells.values():
        if token in token_counts:
            token_counts[token] += 1
    if observation is not None:
        front_token = observation["visual"][1][2]
    else:
        front_x, front_y = _front_position(belief)
        front_token = cells.get(f"{front_x},{front_y}", "occluded")
    return {
        "relative_pose": list(belief["relative_pose"]),
        "relative_facing": str(belief["relative_facing"]),
        "known_cell_count": len(cells),
        "known_object_count": sum(1 for token in cells.values() if token.startswith("v")),
        "front_token": front_token,
        "token_counts": token_counts,
    }


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


def _features(payload: Mapping[str, Any]) -> dict[str, float]:
    organism = payload["organism"]
    summary = payload["belief_summary"]
    front = str(summary["front_token"])
    known = int(summary["known_cell_count"])
    objects = int(summary["known_object_count"])
    values = {
        "bias": 1.0,
        **{key: float(organism[key]) for key in STATE_KEYS},
        "front_empty": 1.0 if front == "empty" else 0.0,
        "front_wall": 1.0 if front == "wall" else 0.0,
        "front_occluded": 1.0 if front == "occluded" else 0.0,
        **{f"front_v{index}": 1.0 if front == f"v{index}" else 0.0 for index in range(5)},
        "known_cell_fraction": min(1.0, known / 81.0),
        "known_object_fraction": min(1.0, objects / 5.0),
    }
    return {name: float(values[name]) for name in FEATURE_NAMES}


def _dot(weights: Mapping[str, float], features: Mapping[str, float]) -> float:
    return (
        weights["bias"] * features["bias"]
        + weights["energy"] * features["energy"]
        + weights["safety"] * features["safety"]
        + weights["connection"] * features["connection"]
        + weights["stimulation"] * features["stimulation"]
        + weights["front_empty"] * features["front_empty"]
        + weights["front_wall"] * features["front_wall"]
        + weights["front_occluded"] * features["front_occluded"]
        + weights["front_v0"] * features["front_v0"]
        + weights["front_v1"] * features["front_v1"]
        + weights["front_v2"] * features["front_v2"]
        + weights["front_v3"] * features["front_v3"]
        + weights["front_v4"] * features["front_v4"]
        + weights["known_cell_fraction"] * features["known_cell_fraction"]
        + weights["known_object_fraction"] * features["known_object_fraction"]
    )


def _softmax(logits: Mapping[str, float]) -> dict[str, float]:
    maximum = max(logits.values())
    exponentials = {key: math.exp(float(value) - maximum) for key, value in logits.items()}
    total = sum(exponentials.values())
    return {key: _round(exponentials[key] / total) for key in OUTCOMES}


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
) -> dict[str, Any]:
    if action not in ACTIONS:
        raise PredictiveControlInvariantError("predictor action is invalid")
    features = _features(payload)
    action_model = state["model"]["actions"][action]
    probabilities = _softmax(
        {
            outcome: _dot(action_model["outcome_weights"][outcome], features)
            for outcome in OUTCOMES
        }
    )
    visit_key = _visit_key(action, payload)
    visit_count = int(state["model"]["visit_counts"].get(visit_key, 0))
    prediction = {
        "schema_version": PREDICTION_SCHEMA_VERSION,
        "producer_function": "ego_life_playground_v0.predictive_control.predict_action",
        "input_hash": _canonical_hash(payload) if include_hashes else None,
        "feature_hash": _canonical_hash(features) if include_hashes else None,
        "action": action,
        "outcome_probabilities": probabilities,
        "predicted_delta": {
            key: _round(max(-0.35, min(0.35, _dot(action_model["delta_weights"][key], features))))
            for key in STATE_KEYS
        },
        "resource_interaction_probability": _round(
            _sigmoid(_dot(action_model["resource_weights"], features))
        ),
        "terminal_risk": _round(
            _sigmoid(_dot(action_model["terminal_weights"], features))
        ),
        "uncertainty": _round(1.0 / math.sqrt(1.0 + visit_count)),
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


def _most_likely_outcome(prediction: Mapping[str, Any], action: str, front_token: str) -> str:
    probabilities = prediction["outcome_probabilities"]
    maximum = max(probabilities.values())
    tied = [outcome for outcome in OUTCOMES if probabilities[outcome] == maximum]
    if action == "move_forward" and front_token == "wall":
        return "blocked"
    preferred = {
        "turn_left": "turned",
        "turn_right": "turned",
        "rest": "rested",
        "interact": "interacted" if front_token.startswith("v") else "no_object",
        "move_forward": "moved",
    }[action]
    return preferred if preferred in tied else tied[0]


def _value_breakdown(
    organism: Mapping[str, float],
    prediction: Mapping[str, Any],
    *,
    active_goal: str,
    goal_value_mode: str,
    action_cost: float,
) -> dict[str, float]:
    predicted_after = {
        key: _clamp(float(organism[key]) + float(prediction["predicted_delta"][key]))
        for key in STATE_KEYS
    }
    changes = {
        key: _round(
            max(0.0, TARGET_LEVEL - float(organism[key]))
            - max(0.0, TARGET_LEVEL - predicted_after[key])
        )
        for key in STATE_KEYS
    }
    if goal_value_mode == "equal" or active_goal == "explore":
        weighted = sum(changes.values())
        intent = 0.0
    else:
        weighted = sum(
            value * (2.0 if key == active_goal else 1.0)
            for key, value in changes.items()
        )
        intent = changes[active_goal]
    terminal = -1.25 * float(prediction["terminal_risk"])
    cost = -0.25 * float(action_cost)
    exploration = 0.12 * float(prediction["uncertainty"])
    resource = (
        (0.16 if active_goal == "energy" else 0.03)
        * float(prediction["resource_interaction_probability"])
    )
    return {
        "total_deficit_change": sum(changes.values()),
        "weighted_deficit_change": weighted,
        "intent_deficit_change": intent,
        "terminal_risk_value": terminal,
        "action_cost_value": cost,
        "exploration_uncertainty_value": exploration,
        "resource_value": resource,
        "total": weighted + 0.5 * intent + terminal + cost + exploration + resource,
    }


def _rollout_for_first_action(
    state: Mapping[str, Any],
    *,
    observation: Mapping[str, Any],
    organism: Mapping[str, float],
    first_action: str,
    active_goal: str,
    horizon: int,
    beam_width: int,
    discount: float,
    relative_map_mode: str,
    goal_value_mode: str,
    action_costs: Mapping[str, float],
    prediction_cache: dict[tuple[Any, ...], dict[str, Any]],
) -> dict[str, Any]:
    base_belief = deepcopy(
        state["belief"] if relative_map_mode == "relative" else _empty_belief(
            int(state["belief"]["episode_index"])
        )
    )
    template_bank = [
        ("rest",),
        ("move_forward",),
        ("interact",),
        ("turn_left",),
        ("turn_right",),
        ("move_forward", "interact"),
        ("turn_left", "move_forward"),
        ("turn_right", "move_forward"),
        ("move_forward", "turn_left"),
        ("move_forward", "turn_right"),
        ("turn_left", "move_forward", "interact"),
        ("turn_right", "move_forward", "interact"),
        ("move_forward", "move_forward", "interact"),
        ("interact", "turn_left", "move_forward"),
        ("interact", "turn_right", "move_forward"),
        ACTIONS,
    ]
    if len(template_bank) != beam_width:
        raise PredictiveControlInvariantError("beam template count differs from beam width")
    # The beam-width contract applies to the whole first-action frontier, not
    # independently to each of its five action groups.  Allocate 4+3+3+3+3
    # deterministic trajectories so all five first actions are represented by
    # exactly 16 total beams without multiplying the width by five.
    allocation = 4 if first_action == ACTIONS[0] else 3
    start = ACTIONS.index(first_action) * 3
    continuation_templates = [
        template_bank[(start + offset) % len(template_bank)]
        for offset in range(allocation)
    ]
    beams: list[dict[str, Any]] = []
    for template in continuation_templates:
        actions = [first_action]
        while len(actions) < horizon:
            actions.append(template[(len(actions) - 1) % len(template)])
        node_organism = {key: float(organism[key]) for key in STATE_KEYS}
        node_belief = deepcopy(base_belief)
        node_observation: Mapping[str, Any] | None = observation
        score = 0.0
        first_breakdown = None
        for depth, action in enumerate(actions):
            summary = _belief_summary(node_belief, node_observation)
            payload = {
                # Internal trajectory prediction uses only the already-derived
                # belief summary and organism vector.  The observation is not
                # a model feature after the visible tokens have entered belief.
                "observation": observation,
                "organism": node_organism,
                "belief_summary": summary,
            }
            feature_values = _features(payload)
            cache_key = (
                action,
                *(feature_values[name] for name in FEATURE_NAMES),
            )
            prediction = prediction_cache.get(cache_key)
            if prediction is None:
                prediction = _predict_from_payload(
                    state, payload, action, include_hashes=False
                )
                prediction_cache[cache_key] = prediction
            breakdown = _value_breakdown(
                node_organism,
                prediction,
                active_goal=active_goal,
                goal_value_mode=goal_value_mode,
                action_cost=float(action_costs[action]),
            )
            if first_breakdown is None:
                first_breakdown = breakdown
            score = score + (discount**depth) * float(breakdown["total"])
            node_organism = {
                key: max(
                    0.0,
                    min(
                        1.0,
                        float(node_organism[key])
                        + float(prediction["predicted_delta"][key]),
                    ),
                )
                for key in STATE_KEYS
            }
            outcome = _most_likely_outcome(
                prediction, action, str(summary["front_token"])
            )
            node_belief = _advance_belief_pose(
                node_belief, action=action, outcome_type=outcome
            )
            node_observation = None
        beams.append(
            {
                "score": score,
                "organism": node_organism,
                "belief": node_belief,
                "actions": actions,
                "first_breakdown": first_breakdown,
            }
        )
    beams.sort(
        key=lambda node: (
            -float(node["score"]),
            tuple(ACTIONS.index(action) for action in node["actions"]),
        )
    )
    best = beams[0]
    return {
        **{
            key: _round(value)
            for key, value in best["first_breakdown"].items()
        },
        "total": _round(float(best["score"])),
        "plan_actions": list(best["actions"][:3]),
        "trajectory_hash": _canonical_hash(
            {
                "actions": best["actions"],
                "score": best["score"],
                "organism": best["organism"],
                "belief": best["belief"],
            }
        ),
    }


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
    current_payload = _predictor_input(
        state,
        observation=observation,
        organism=organism,
        relative_map_mode=relative_map_mode,
    )
    predictions = {
        action: _predict_from_payload(state, current_payload, action)
        for action in ACTIONS
    }
    prediction_cache: dict[tuple[Any, ...], dict[str, Any]] = {}
    values = {
        action: _rollout_for_first_action(
            state,
            observation=observation,
            organism=organism,
            first_action=action,
            active_goal=active_goal,
            horizon=horizon,
            beam_width=beam_width,
            discount=discount,
            relative_map_mode=relative_map_mode,
            goal_value_mode=goal_value_mode,
            action_costs=action_costs,
            prediction_cache=prediction_cache,
        )
        for action in ACTIONS
    }
    selected = max(
        ACTIONS,
        key=lambda action: (
            float(values[action]["total"]),
            -ACTIONS.index(action),
        ),
    )
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
        "model_hash": _canonical_hash(state["model"]),
        "belief_hash": _canonical_hash(state["belief"]),
    }


def _updated_row(
    row: Mapping[str, float],
    features: Mapping[str, float],
    multiplier: float,
) -> dict[str, float]:
    return {
        feature: _round(
            max(-4.0, min(4.0, float(row[feature]) + LEARNING_RATE * multiplier * float(features[feature])))
        )
        for feature in FEATURE_NAMES
    }


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
    prediction_before = _predict_from_payload(state, payload, action)
    before_hash = _canonical_hash(state["model"])
    updated = dict(state)
    model = dict(state["model"])
    if updates_enabled:
        actions = dict(model["actions"])
        action_model = deepcopy(actions[action])
        features = _features(payload)
        probabilities = prediction_before["outcome_probabilities"]
        for outcome in OUTCOMES:
            target = 1.0 if outcome == actual_outcome_type else 0.0
            action_model["outcome_weights"][outcome] = _updated_row(
                action_model["outcome_weights"][outcome],
                features,
                target - float(probabilities[outcome]),
            )
        for key in STATE_KEYS:
            error = float(actual_delta[key]) - float(prediction_before["predicted_delta"][key])
            action_model["delta_weights"][key] = _updated_row(
                action_model["delta_weights"][key], features, error
            )
        action_model["resource_weights"] = _updated_row(
            action_model["resource_weights"],
            features,
            (1.0 if resource_interaction else 0.0)
            - float(prediction_before["resource_interaction_probability"]),
        )
        action_model["terminal_weights"] = _updated_row(
            action_model["terminal_weights"],
            features,
            (1.0 if terminal else 0.0) - float(prediction_before["terminal_risk"]),
        )
        actions[action] = action_model
        model["actions"] = actions
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
    prediction_after = _predict_from_payload(updated, payload, action)
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
    "hyperparameters",
    "model_hash",
    "observe_belief",
    "plan_action",
    "predict_action",
    "reset_for_respawn",
    "update_after_transition",
    "validate_predictor_input",
    "validate_state",
]
