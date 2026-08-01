"""Legal-public homeostatic consequence learner and fixed planner.

This module is deliberately small and JSON-only.  It is an interpretable
Bayesian/empirical reference extracted from the bounded 001K evidence, not a
neural learner and not a second runtime.  Product live execution and replay
both call it only through ``engine.compute_step``.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from typing import Any, Mapping

from . import microworld


STATE_SCHEMA_VERSION = "ego.life_playground.homeostatic_transfer.state.v2"
PLAN_SCHEMA_VERSION = "ego.life_playground.homeostatic_transfer.plan.v2"
UPDATE_SCHEMA_VERSION = "ego.life_playground.homeostatic_transfer.update.v2"
MODES = ("off", "public_bayes")
DRIVE_MODES = ("canonical", "off")
POSTERIOR_MODES = ("canonical", "two_timescale", "ablated")
FEEDBACK_MODES = ("canonical", "shuffle")
PUBLIC_INPUT_FIELDS = ("observation", "organism", "last_action", "last_delta")
PUBLIC_ORGANISM_FIELDS = ("energy", "safety")
SHORT_HISTORY_LIMIT = 16
HOMEOSTATIC_TARGET_LEVEL = 0.72


class HomeostaticTransferInvariantError(ValueError):
    """Raised when public input or serialized learner state is invalid."""


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _round(value: float, digits: int = 12) -> float:
    return round(float(value), digits)


def hyperparameters() -> dict[str, Any]:
    return {
        "schema_version": "ego.life_playground.homeostatic_transfer.hyperparameters.v1",
        "algorithm": "legal_public_empirical_bayes_reference",
        "short_history_limit": SHORT_HISTORY_LIMIT,
        "unknown_information_floor": 0.04,
        "known_uncertainty_scale": 0.05,
        "terminal_risk_scale": 0.50,
        "default_mode": "off",
        "default_posterior_mode": "canonical",
        "two_timescale_qualification_consumed": False,
        "two_timescale_transfer_gate_passed": False,
        "neural": False,
    }


def _empty_fast_state(*, world_epoch: int = 0, respawn_count: int = 0) -> dict[str, Any]:
    return {
        "schema_version": "ego.life_playground.homeostatic_transfer.fast.v2",
        "world_epoch": int(world_epoch),
        "respawn_count": int(respawn_count),
        "token_stats": {},
        "active_target": None,
        "short_history": [],
        "interaction_count": 0,
        "escape_steps_remaining": 0,
        "escape_trigger_count": 0,
    }


def _empty_slow_state() -> dict[str, Any]:
    return {
        "schema_version": "ego.life_playground.homeostatic_transfer.slow.v2",
        "action_stats": {},
        "effect_family_stats": {},
        "effect_prototypes": {},
        "update_count": 0,
        "world_reset_count": 0,
    }


def empty_state() -> dict[str, Any]:
    state = {
        "schema_version": STATE_SCHEMA_VERSION,
        "slow_state": _empty_slow_state(),
        "fast_state": _empty_fast_state(),
        "rng_state": {
            "schema_version": "ego.life_playground.homeostatic_transfer.rng.v1",
            "algorithm": "sha256_deterministic_tie",
            "counter": 0,
        },
    }
    validate_state(state)
    return state


def state_hash(state: Mapping[str, Any]) -> str:
    validate_state(state)
    return canonical_hash(state)


def slow_state_hash(state: Mapping[str, Any]) -> str:
    validate_state(state)
    return canonical_hash(state["slow_state"])


def fast_state_hash(state: Mapping[str, Any]) -> str:
    validate_state(state)
    return canonical_hash(state["fast_state"])


def posterior_hash(state: Mapping[str, Any]) -> str:
    validate_state(state)
    return canonical_hash(state["fast_state"]["token_stats"])


def _validate_stat_row(value: Any, label: str) -> None:
    required = {
        "count",
        "energy_mean",
        "safety_mean",
        "terminal_count",
        "outcome_counts",
    }
    if not isinstance(value, Mapping) or set(value) != required:
        raise HomeostaticTransferInvariantError(f"{label} stat schema mismatch")
    if type(value["count"]) is not int or value["count"] <= 0:
        raise HomeostaticTransferInvariantError(f"{label} count must be positive")
    if type(value["terminal_count"]) is not int or not 0 <= value["terminal_count"] <= value["count"]:
        raise HomeostaticTransferInvariantError(f"{label} terminal_count is invalid")
    for field in ("energy_mean", "safety_mean"):
        number = value[field]
        if type(number) is not float or not math.isfinite(number):
            raise HomeostaticTransferInvariantError(f"{label} {field} must be finite float")
    counts = value["outcome_counts"]
    if not isinstance(counts, Mapping) or any(
        type(key) is not str or type(count) is not int or count <= 0
        for key, count in counts.items()
    ):
        raise HomeostaticTransferInvariantError(f"{label} outcome_counts are invalid")
    if sum(counts.values()) != value["count"]:
        raise HomeostaticTransferInvariantError(f"{label} outcome counts do not sum to count")


def validate_state(state: Mapping[str, Any]) -> None:
    if not isinstance(state, Mapping) or set(state) != {
        "schema_version",
        "slow_state",
        "fast_state",
        "rng_state",
    }:
        raise HomeostaticTransferInvariantError("homeostatic state schema mismatch")
    if state["schema_version"] != STATE_SCHEMA_VERSION:
        raise HomeostaticTransferInvariantError("homeostatic state version mismatch")
    slow = state["slow_state"]
    if not isinstance(slow, Mapping) or set(slow) != {
        "schema_version",
        "action_stats",
        "effect_family_stats",
        "effect_prototypes",
        "update_count",
        "world_reset_count",
    }:
        raise HomeostaticTransferInvariantError("slow state schema mismatch")
    if slow["schema_version"] != "ego.life_playground.homeostatic_transfer.slow.v2":
        raise HomeostaticTransferInvariantError("slow state version mismatch")
    if type(slow["update_count"]) is not int or slow["update_count"] < 0:
        raise HomeostaticTransferInvariantError("slow update_count is invalid")
    if type(slow["world_reset_count"]) is not int or slow["world_reset_count"] < 0:
        raise HomeostaticTransferInvariantError("slow world_reset_count is invalid")
    if not isinstance(slow["action_stats"], Mapping):
        raise HomeostaticTransferInvariantError("slow action_stats must be an object")
    for action, row in slow["action_stats"].items():
        if action not in microworld.ACTIONS:
            raise HomeostaticTransferInvariantError("slow action_stats action is invalid")
        _validate_stat_row(row, "slow action")
    if not isinstance(slow["effect_family_stats"], Mapping):
        raise HomeostaticTransferInvariantError("effect_family_stats must be an object")
    for signature, count in slow["effect_family_stats"].items():
        if type(signature) is not str or type(count) is not int or count <= 0:
            raise HomeostaticTransferInvariantError("effect family row is invalid")
    if not isinstance(slow["effect_prototypes"], Mapping):
        raise HomeostaticTransferInvariantError("effect_prototypes must be an object")
    for signature, row in slow["effect_prototypes"].items():
        if type(signature) is not str:
            raise HomeostaticTransferInvariantError("effect prototype key is invalid")
        _validate_stat_row(row, "slow effect prototype")

    fast = state["fast_state"]
    if not isinstance(fast, Mapping) or set(fast) != {
        "schema_version",
        "world_epoch",
        "respawn_count",
        "token_stats",
        "active_target",
        "short_history",
        "interaction_count",
        "escape_steps_remaining",
        "escape_trigger_count",
    }:
        raise HomeostaticTransferInvariantError("fast state schema mismatch")
    if fast["schema_version"] != "ego.life_playground.homeostatic_transfer.fast.v2":
        raise HomeostaticTransferInvariantError("fast state version mismatch")
    for field in (
        "world_epoch",
        "respawn_count",
        "interaction_count",
        "escape_steps_remaining",
        "escape_trigger_count",
    ):
        if type(fast[field]) is not int or fast[field] < 0:
            raise HomeostaticTransferInvariantError(f"fast {field} is invalid")
    if fast["escape_steps_remaining"] > 3:
        raise HomeostaticTransferInvariantError("escape_steps_remaining exceeds bound")
    if not isinstance(fast["token_stats"], Mapping):
        raise HomeostaticTransferInvariantError("fast token_stats must be an object")
    for token, row in fast["token_stats"].items():
        if token not in microworld.TOKENS:
            raise HomeostaticTransferInvariantError("fast token is invalid")
        _validate_stat_row(row, "fast token")
    if fast["active_target"] is not None and fast["active_target"] not in microworld.TOKENS:
        raise HomeostaticTransferInvariantError("active_target is invalid")
    history = fast["short_history"]
    if not isinstance(history, list) or len(history) > SHORT_HISTORY_LIMIT:
        raise HomeostaticTransferInvariantError("short_history is invalid")
    if any(not isinstance(item, Mapping) for item in history):
        raise HomeostaticTransferInvariantError("short_history row is invalid")

    rng = state["rng_state"]
    if not isinstance(rng, Mapping) or set(rng) != {
        "schema_version",
        "algorithm",
        "counter",
    }:
        raise HomeostaticTransferInvariantError("rng state schema mismatch")
    if (
        rng["schema_version"] != "ego.life_playground.homeostatic_transfer.rng.v1"
        or rng["algorithm"] != "sha256_deterministic_tie"
        or type(rng["counter"]) is not int
        or rng["counter"] < 0
    ):
        raise HomeostaticTransferInvariantError("rng state is invalid")


def scan_public_input(payload: Any) -> dict[str, Any]:
    forbidden = {
        "seed",
        "world_id",
        "context_id",
        "opaque_context_id",
        "layout_id",
        "layout",
        "mapping_index",
        "mapping_commitment",
        "token_mapping",
        "private_pose",
        "position",
        "objects_by_cause",
        "cause",
        "oracle",
        "oracle_action",
        "split",
        "packet",
        "packet_name",
        "future",
        "future_observation",
        "verdict",
    }
    findings: list[dict[str, str]] = []

    def visit(value: Any, path: str) -> None:
        if isinstance(value, Mapping):
            for raw_key, child in value.items():
                key = str(raw_key)
                child_path = f"{path}.{key}" if path else key
                if key.lower() in forbidden:
                    findings.append({"field": key, "path": child_path})
                visit(child, child_path)
        elif isinstance(value, (list, tuple)):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")

    if not isinstance(payload, Mapping):
        findings.append({"field": "<root>", "path": ""})
    else:
        for key in sorted(set(payload) - set(PUBLIC_INPUT_FIELDS)):
            findings.append({"field": str(key), "path": str(key)})
    visit(payload, "")
    unique = {_canonical_json(item): item for item in findings}
    ordered = sorted(unique.values(), key=lambda item: (item["field"], item["path"]))
    clean = bool(
        not ordered
        and isinstance(payload, Mapping)
        and set(payload) == set(PUBLIC_INPUT_FIELDS)
    )
    if clean:
        organism = payload["organism"]
        observation = payload["observation"]
        clean = bool(
            isinstance(organism, Mapping)
            and set(organism) == set(PUBLIC_ORGANISM_FIELDS)
            and all(
                type(organism[key]) is float
                and math.isfinite(organism[key])
                and 0.0 <= organism[key] <= 1.0
                for key in PUBLIC_ORGANISM_FIELDS
            )
            and isinstance(observation, Mapping)
            and set(observation) == {"schema_version", "visual"}
            and observation.get("schema_version")
            == microworld.PUBLIC_OBSERVATION_SCHEMA_VERSION
        )
        if not clean:
            ordered.append({"field": "<public_schema>", "path": ""})
    return {
        "schema_version": "ego.life_playground.homeostatic_transfer.input_scan.v1",
        "clean": clean,
        "findings": ordered,
        "input_hash": canonical_hash(payload),
    }


def _front_token(observation: Mapping[str, Any]) -> str:
    return str(observation["visual"][1][2])


def _visible_tokens(observation: Mapping[str, Any]) -> list[tuple[str, int, int]]:
    visible: list[tuple[str, int, int]] = []
    visual = observation["visual"]
    if not isinstance(visual, list) or len(visual) != 5:
        raise HomeostaticTransferInvariantError("public visual must be 5x5")
    for row_index, row in enumerate(visual):
        if not isinstance(row, list) or len(row) != 5:
            raise HomeostaticTransferInvariantError("public visual must be 5x5")
        for column_index, token in enumerate(row):
            if token not in microworld.VISUAL_TOKENS:
                raise HomeostaticTransferInvariantError("public visual token is invalid")
            if token in microworld.TOKENS:
                visible.append((str(token), column_index - 2, row_index - 2))
    return visible


def _empty_prediction() -> dict[str, Any]:
    return {
        "count": 0,
        "predicted_delta": {"energy": 0.0, "safety": 0.0},
        "terminal_risk": 0.0,
        "uncertainty": 1.0,
        "outcome_probabilities": {},
        "source": "unobserved_public_prior",
    }


def _prediction_from_row(row: Mapping[str, Any], source: str) -> dict[str, Any]:
    count = int(row["count"])
    return {
        "count": count,
        "predicted_delta": {
            "energy": _round(row["energy_mean"]),
            "safety": _round(row["safety_mean"]),
        },
        "terminal_risk": _round(float(row["terminal_count"]) / count),
        "uncertainty": _round(1.0 / math.sqrt(count + 1.0)),
        "outcome_probabilities": {
            str(outcome): _round(float(value) / count)
            for outcome, value in sorted(row["outcome_counts"].items())
        },
        "source": source,
    }


def _slow_effect_prior(state: Mapping[str, Any]) -> dict[str, Any]:
    """Return a public-history mixture over reusable effect families.

    Anonymous token identity never crosses worlds.  Only effect prototypes are
    slow: their public delta/outcome statistics persist.  Signatures already
    identified in the current world are excluded when alternatives exist,
    which is the smallest compositional prior expressible without a world ID.
    """

    prototypes = state["slow_state"]["effect_prototypes"]
    if not prototypes:
        return _empty_prediction()
    observed = [
        _effect_signature(
            {
                "energy": float(row["energy_mean"]),
                "safety": float(row["safety_mean"]),
            }
        )
        for row in state["fast_state"]["token_stats"].values()
    ]
    # Counts are learned from the first public interaction with each token in a
    # world.  Their ratios therefore estimate repeated family multiplicity
    # (for example two distinct negative/negative effects) without seeing a
    # mapping or world identifier.  Removing one observed occurrence avoids
    # the earlier, false one-family-one-token assumption.
    minimum_count = min(int(row["count"]) for row in prototypes.values())
    observed_counts: dict[str, int] = {}
    for signature in observed:
        observed_counts[signature] = observed_counts.get(signature, 0) + 1
    remaining: list[tuple[str, Mapping[str, Any]]] = []
    all_weighted: list[tuple[str, Mapping[str, Any]]] = []
    for signature, row in sorted(prototypes.items()):
        multiplicity = max(1, round(int(row["count"]) / minimum_count))
        all_weighted.extend((signature, row) for _ in range(multiplicity))
        residual = max(0, multiplicity - observed_counts.get(signature, 0))
        remaining.extend((signature, row) for _ in range(residual))
    selected = remaining or all_weighted
    family_count = len(selected)
    total_samples = sum(int(row["count"]) for _signature, row in selected)
    outcome_totals: dict[str, float] = {}
    for _signature, row in selected:
        for outcome, count in row["outcome_counts"].items():
            outcome_totals[str(outcome)] = outcome_totals.get(str(outcome), 0.0) + (
                float(count) / float(row["count"])
            )
    return {
        "count": total_samples,
        "predicted_delta": {
            key: _round(
                sum(float(row[f"{key}_mean"]) for _signature, row in selected)
                / family_count
            )
            for key in PUBLIC_ORGANISM_FIELDS
        },
        "terminal_risk": _round(
            sum(
                float(row["terminal_count"]) / float(row["count"])
                for _signature, row in selected
            )
            / family_count
        ),
        "uncertainty": _round(
            min(1.0, 1.0 / math.sqrt(total_samples + 1.0) + 0.10 * (family_count - 1))
        ),
        "outcome_probabilities": {
            outcome: _round(value / family_count)
            for outcome, value in sorted(outcome_totals.items())
        },
        "source": "slow_effect_family_prior",
        "remaining_effect_signatures": [signature for signature, _row in selected],
    }


def _predictions(
    state: Mapping[str, Any], observation: Mapping[str, Any], posterior_mode: str
) -> dict[str, dict[str, Any]]:
    front = _front_token(observation)
    action_stats = state["slow_state"]["action_stats"]
    result: dict[str, dict[str, Any]] = {}
    for action in microworld.ACTIONS:
        row = action_stats.get(action)
        result[action] = (
            _empty_prediction()
            if row is None
            else _prediction_from_row(row, "slow_action_consequence")
        )
    if posterior_mode in {"canonical", "two_timescale"} and front in microworld.TOKENS:
        token_row = state["fast_state"]["token_stats"].get(front)
        if token_row is not None:
            result["interact"] = _prediction_from_row(
                token_row, "current_world_token_interaction"
            )
        elif posterior_mode == "two_timescale":
            result["interact"] = _slow_effect_prior(state)
        else:
            result["interact"] = _empty_prediction()
    return result


def _drive(organism: Mapping[str, float], target_level: float, drive_mode: str) -> dict[str, float]:
    if drive_mode == "off":
        return {"energy": 0.0, "safety": 0.0}
    return {
        key: _round(max(0.0, target_level - float(organism[key])))
        for key in PUBLIC_ORGANISM_FIELDS
    }


def _token_prediction(
    state: Mapping[str, Any], token: str, posterior_mode: str
) -> dict[str, Any]:
    row = (
        state["fast_state"]["token_stats"].get(token)
        if posterior_mode in {"canonical", "two_timescale"}
        else None
    )
    if row is not None:
        return _prediction_from_row(row, "current_world_token_interaction")
    return (
        _slow_effect_prior(state)
        if posterior_mode == "two_timescale"
        else _empty_prediction()
    )


def _token_value(
    prediction: Mapping[str, Any],
    *,
    drive: Mapping[str, float],
    organism: Mapping[str, float],
    distance: int,
) -> float:
    if int(prediction["count"]) == 0:
        safe_margin = max(0.0, min(float(organism["energy"]), float(organism["safety"])) - 0.12)
        information_value = 0.04 + min(0.04, safe_margin * 0.10)
        return _round(information_value - 0.004 * distance)
    delta = prediction["predicted_delta"]
    deficit_reduction = sum(float(drive[key]) * float(delta[key]) for key in PUBLIC_ORGANISM_FIELDS)
    uncertainty_value = 0.05 * float(prediction["uncertainty"])
    if prediction["source"] == "slow_effect_family_prior":
        safe_margin = max(
            0.0,
            min(float(organism["energy"]), float(organism["safety"])) - 0.12,
        )
        uncertainty_value += 0.02 + min(0.03, safe_margin * 0.05)
    terminal_penalty = 0.50 * float(prediction["terminal_risk"])
    return _round(deficit_reduction + uncertainty_value - terminal_penalty - 0.004 * distance)


def _deterministic_tie(state: Mapping[str, Any], action: str, sequence: int) -> float:
    digest = hashlib.sha256(
        _canonical_json(
            {
                "state": state_hash(state),
                "action": action,
                "sequence": sequence,
            }
        ).encode("utf-8")
    ).digest()
    return _round(int.from_bytes(digest[:8], "big") / float(2**64 - 1) * 1e-9)


def plan_action(
    state: Mapping[str, Any],
    *,
    public_input: Mapping[str, Any],
    sequence: int,
    mode: str,
    drive_mode: str,
    action_costs: Mapping[str, float],
    target_level: float,
    posterior_mode: str = "canonical",
) -> dict[str, Any]:
    validate_state(state)
    scan = scan_public_input(public_input)
    if not scan["clean"]:
        raise HomeostaticTransferInvariantError("public input failed leakage/schema scan")
    if mode != "public_bayes" or drive_mode not in DRIVE_MODES or posterior_mode not in POSTERIOR_MODES:
        raise HomeostaticTransferInvariantError("homeostatic plan mode is invalid")
    if type(sequence) is not int or sequence <= 0:
        raise HomeostaticTransferInvariantError("sequence must be positive")
    if set(action_costs) != set(microworld.ACTIONS) or any(
        type(action_costs[action]) is not float or action_costs[action] < 0.0
        for action in microworld.ACTIONS
    ):
        raise HomeostaticTransferInvariantError("action costs are invalid")
    if type(target_level) is not float or not 0.0 < target_level <= 1.0:
        raise HomeostaticTransferInvariantError("target_level is invalid")

    observation = public_input["observation"]
    organism = public_input["organism"]
    drive = _drive(organism, target_level, drive_mode)
    predictions = _predictions(state, observation, posterior_mode)
    visible = _visible_tokens(observation)
    ranked_tokens = []
    for token, relative_x, relative_y in visible:
        prediction = _token_prediction(state, token, posterior_mode)
        distance = abs(relative_x) + abs(relative_y)
        ranked_tokens.append(
            {
                "token": token,
                "relative_x": relative_x,
                "relative_y": relative_y,
                "distance": distance,
                "known": bool(
                    posterior_mode in {"canonical", "two_timescale"}
                    and token in state["fast_state"]["token_stats"]
                ),
                "prediction_source": prediction["source"],
                "predicted_delta": deepcopy(prediction["predicted_delta"]),
                "terminal_risk": prediction["terminal_risk"],
                "uncertainty": prediction["uncertainty"],
                "drive_value": _token_value(
                    prediction,
                    drive=drive,
                    organism=organism,
                    distance=distance,
                ),
            }
        )
    ranked_tokens.sort(
        key=lambda row: (-float(row["drive_value"]), int(row["distance"]), str(row["token"]))
    )
    selected_target = ranked_tokens[0] if ranked_tokens else None
    front = _front_token(observation)
    if front in microworld.TOKENS:
        front_row = next(row for row in ranked_tokens if row["token"] == front)
        unobserved_without_prior = (
            not front_row["known"]
            and front_row["prediction_source"] == "unobserved_public_prior"
        )
        if unobserved_without_prior or float(front_row["drive_value"]) > 0.0:
            selected_action, reason = "interact", "front_token_probe_or_homeostatic_use"
            selected_target = front_row
        else:
            selected_action, reason = "turn_right", "front_token_predicted_risk_or_deficit_harm"
    elif selected_target is not None:
        relative_x = int(selected_target["relative_x"])
        relative_y = int(selected_target["relative_y"])
        front_cell = str(observation["visual"][1][2])
        if relative_y < 0 and front_cell == "empty":
            selected_action, reason = "move_forward", "approach_front_half_homeostatic_target"
        elif relative_x < 0:
            selected_action, reason = "turn_left", "orient_homeostatic_target"
        elif relative_x > 0:
            selected_action, reason = "turn_right", "orient_homeostatic_target"
        elif relative_y == -1:
            selected_action, reason = "interact", "front_homeostatic_target"
        else:
            selected_action, reason = "turn_right", "rotate_to_rear_homeostatic_target"
    else:
        front_cell = str(observation["visual"][1][2])
        if front_cell == "wall":
            selected_action, reason = "turn_right", "public_wall_follow_turn"
        elif sequence % 5 == 0:
            selected_action, reason = "turn_right", "public_sweep_turn"
        else:
            selected_action, reason = "move_forward", "public_sweep_forward"

    if int(state["fast_state"]["escape_steps_remaining"]) > 0:
        front_cell = str(observation["visual"][1][2])
        selected_action = (
            "turn_right" if front_cell in {"wall", *microworld.TOKENS} else "move_forward"
        )
        selected_target = None
        reason = "public_harm_escape_macro"

    base_values = {}
    for action in microworld.ACTIONS:
        prediction = predictions[action]
        delta = prediction["predicted_delta"]
        value = sum(float(drive[key]) * float(delta[key]) for key in PUBLIC_ORGANISM_FIELDS)
        value -= 0.50 * float(prediction["terminal_risk"])
        value += 0.02 * float(prediction["uncertainty"])
        value -= float(action_costs[action])
        value += _deterministic_tie(state, action, sequence)
        base_values[action] = _round(value)
    navigation_value = 0.0 if selected_target is None else float(selected_target["drive_value"])
    action_values = {
        action: _round(base_values[action] + (navigation_value + 1.0 if action == selected_action else 0.0))
        for action in microworld.ACTIONS
    }

    return {
        "schema_version": PLAN_SCHEMA_VERSION,
        "mode": mode,
        "public_input_clean": True,
        "public_input_hash": scan["input_hash"],
        "public_input_fields": list(PUBLIC_INPUT_FIELDS),
        "state_hash_before": state_hash(state),
        "slow_state_hash": slow_state_hash(state),
        "fast_state_hash": fast_state_hash(state),
        "posterior_hash": posterior_hash(state),
        "predictions_hash": canonical_hash(predictions),
        "predictions_by_action": predictions,
        "drive_mode": drive_mode,
        "drive": drive,
        "posterior_mode": posterior_mode,
        "slow_prior_applied": any(
            prediction["source"] == "slow_effect_family_prior"
            for prediction in predictions.values()
        ),
        "slow_effect_prototype_hash": canonical_hash(
            state["slow_state"]["effect_prototypes"]
        ),
        "escape_steps_remaining": int(
            state["fast_state"]["escape_steps_remaining"]
        ),
        "ranked_tokens": ranked_tokens,
        "selected_target": None if selected_target is None else selected_target["token"],
        "selected_action": selected_action,
        "selection_reason": reason,
        "action_values": action_values,
    }


def _updated_stat(
    prior: Mapping[str, Any] | None,
    *,
    actual_delta: Mapping[str, float],
    terminal: bool,
    outcome_type: str,
) -> dict[str, Any]:
    row = (
        {
            "count": 0,
            "energy_mean": 0.0,
            "safety_mean": 0.0,
            "terminal_count": 0,
            "outcome_counts": {},
        }
        if prior is None
        else deepcopy(dict(prior))
    )
    count = int(row["count"]) + 1
    for key in PUBLIC_ORGANISM_FIELDS:
        row[f"{key}_mean"] = _round(
            float(row[f"{key}_mean"])
            + (float(actual_delta[key]) - float(row[f"{key}_mean"])) / count
        )
    row["count"] = count
    row["terminal_count"] = int(row["terminal_count"]) + (1 if terminal else 0)
    counts = dict(row["outcome_counts"])
    counts[outcome_type] = int(counts.get(outcome_type, 0)) + 1
    row["outcome_counts"] = {key: counts[key] for key in sorted(counts)}
    return row


def _effect_signature(actual_delta: Mapping[str, float]) -> str:
    def sign(value: float) -> str:
        return "+" if value > 1e-9 else "-" if value < -1e-9 else "0"

    return f"energy:{sign(float(actual_delta['energy']))}|safety:{sign(float(actual_delta['safety']))}"


def update_after_transition(
    state: Mapping[str, Any],
    *,
    public_input: Mapping[str, Any],
    selected_action: str,
    observed_outcome_type: str,
    actual_delta: Mapping[str, float],
    terminal: bool,
    updates_enabled: bool,
    feedback_mode: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_state(state)
    scan = scan_public_input(public_input)
    if not scan["clean"]:
        raise HomeostaticTransferInvariantError("public update input failed leakage/schema scan")
    if selected_action not in microworld.ACTIONS or type(observed_outcome_type) is not str or not observed_outcome_type:
        raise HomeostaticTransferInvariantError("public transition action/outcome is invalid")
    if not isinstance(actual_delta, Mapping) or set(actual_delta) != set(PUBLIC_ORGANISM_FIELDS):
        raise HomeostaticTransferInvariantError("public actual_delta schema mismatch")
    values = {key: float(actual_delta[key]) for key in PUBLIC_ORGANISM_FIELDS}
    if any(not math.isfinite(value) for value in values.values()):
        raise HomeostaticTransferInvariantError("public actual_delta must be finite")
    if type(terminal) is not bool or type(updates_enabled) is not bool or feedback_mode not in FEEDBACK_MODES:
        raise HomeostaticTransferInvariantError("public update controls are invalid")

    before_hash = state_hash(state)
    updated = deepcopy(dict(state))
    observed_token = _front_token(public_input["observation"])
    token_for_update: str | None = None
    applied = bool(updates_enabled)
    if applied:
        slow = updated["slow_state"]
        slow["action_stats"][selected_action] = _updated_stat(
            slow["action_stats"].get(selected_action),
            actual_delta=values,
            terminal=terminal,
            outcome_type=observed_outcome_type,
        )
        slow["update_count"] = int(slow["update_count"]) + 1
        signature = _effect_signature(values)
        slow["effect_family_stats"][signature] = int(
            slow["effect_family_stats"].get(signature, 0)
        ) + 1

        token_was_known = bool(
            observed_token in updated["fast_state"]["token_stats"]
        )
        if (
            selected_action == "interact"
            and observed_outcome_type == "interacted"
            and not token_was_known
        ):
            slow["effect_prototypes"][signature] = _updated_stat(
                slow["effect_prototypes"].get(signature),
                actual_delta=values,
                terminal=terminal,
                outcome_type=observed_outcome_type,
            )

        if (
            selected_action == "interact"
            and observed_outcome_type == "interacted"
            and observed_token in microworld.TOKENS
        ):
            token_for_update = observed_token
            if feedback_mode == "shuffle":
                index = microworld.TOKENS.index(observed_token)
                token_for_update = microworld.TOKENS[(index + 1) % len(microworld.TOKENS)]
            fast = updated["fast_state"]
            fast["token_stats"][token_for_update] = _updated_stat(
                fast["token_stats"].get(token_for_update),
                actual_delta=values,
                terminal=terminal,
                outcome_type=observed_outcome_type,
            )
            fast["interaction_count"] = int(fast["interaction_count"]) + 1
            fast["active_target"] = None
            fast["escape_steps_remaining"] = 0

        fast = updated["fast_state"]
        front_stats = fast["token_stats"].get(observed_token)
        if (
            selected_action in {"turn_left", "turn_right"}
            and observed_token in microworld.TOKENS
            and front_stats is not None
        ):
            drive = _drive(
                public_input["organism"], HOMEOSTATIC_TARGET_LEVEL, "canonical"
            )
            prediction = _prediction_from_row(
                front_stats, "current_world_token_interaction"
            )
            if _token_value(
                prediction,
                drive=drive,
                organism=public_input["organism"],
                distance=1,
            ) <= 0.0:
                fast["escape_steps_remaining"] = 3
                fast["escape_trigger_count"] = int(fast["escape_trigger_count"]) + 1
        elif int(fast["escape_steps_remaining"]) > 0:
            fast["escape_steps_remaining"] = max(
                0, int(fast["escape_steps_remaining"]) - 1
            )

        history = list(updated["fast_state"]["short_history"])
        history.append(
            {
                "action": selected_action,
                "outcome_type": observed_outcome_type,
                "actual_delta": {key: _round(values[key]) for key in PUBLIC_ORGANISM_FIELDS},
                "terminal": terminal,
                "public_input_hash": scan["input_hash"],
            }
        )
        updated["fast_state"]["short_history"] = history[-SHORT_HISTORY_LIMIT:]
        updated["rng_state"]["counter"] = int(updated["rng_state"]["counter"]) + 1

    validate_state(updated)
    return updated, {
        "schema_version": UPDATE_SCHEMA_VERSION,
        "producer_function": "ego_life_playground_v0.homeostatic_transfer.update_after_transition",
        "applied": applied,
        "reason": "legal_public_feedback_update" if applied else "updates_frozen",
        "feedback_mode": feedback_mode,
        "public_input_clean": True,
        "public_input_hash": scan["input_hash"],
        "selected_action": selected_action,
        "observed_outcome_type": observed_outcome_type,
        "observed_token": observed_token if observed_token in microworld.TOKENS else None,
        "updated_token": token_for_update,
        "actual_delta": {key: _round(values[key]) for key in PUBLIC_ORGANISM_FIELDS},
        "terminal": terminal,
        "state_hash_before": before_hash,
        "state_hash_after": state_hash(updated),
        "slow_state_hash_after": slow_state_hash(updated),
        "fast_state_hash_after": fast_state_hash(updated),
        "posterior_hash_after": posterior_hash(updated),
        "update_count_after": int(updated["slow_state"]["update_count"]),
        "effect_prototype_hash_after": canonical_hash(
            updated["slow_state"]["effect_prototypes"]
        ),
        "escape_steps_remaining_after": int(
            updated["fast_state"]["escape_steps_remaining"]
        ),
    }


def reset_for_respawn(state: Mapping[str, Any]) -> dict[str, Any]:
    validate_state(state)
    updated = deepcopy(dict(state))
    fast = updated["fast_state"]
    fast["active_target"] = None
    fast["short_history"] = []
    fast["escape_steps_remaining"] = 0
    fast["respawn_count"] = int(fast["respawn_count"]) + 1
    validate_state(updated)
    return updated


def reset_for_world(state: Mapping[str, Any]) -> dict[str, Any]:
    validate_state(state)
    updated = deepcopy(dict(state))
    old_fast = updated["fast_state"]
    updated["fast_state"] = _empty_fast_state(
        world_epoch=int(old_fast["world_epoch"]) + 1,
        respawn_count=int(old_fast["respawn_count"]),
    )
    # Resetting a world is not a learning event.  The slow learned structure is
    # byte-stable; the fast world epoch is the auditable reset counter.
    validate_state(updated)
    return updated


def reset_fast_state(state: Mapping[str, Any]) -> dict[str, Any]:
    """Ablation/reset alias with the same semantics as entering a new world."""

    return reset_for_world(state)


def reset_slow_state(state: Mapping[str, Any]) -> dict[str, Any]:
    """Clear cross-world structure while preserving current-world evidence."""

    validate_state(state)
    updated = deepcopy(dict(state))
    updated["slow_state"] = _empty_slow_state()
    validate_state(updated)
    return updated


__all__ = [
    "DRIVE_MODES",
    "FEEDBACK_MODES",
    "MODES",
    "POSTERIOR_MODES",
    "HomeostaticTransferInvariantError",
    "empty_state",
    "fast_state_hash",
    "hyperparameters",
    "plan_action",
    "posterior_hash",
    "reset_for_respawn",
    "reset_for_world",
    "reset_fast_state",
    "reset_slow_state",
    "scan_public_input",
    "slow_state_hash",
    "state_hash",
    "update_after_transition",
    "validate_state",
]
