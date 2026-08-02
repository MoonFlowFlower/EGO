"""Clean exact hierarchical learner for the featured V2 product successor.

This module owns only the public hypothesis family, Bayesian learner state, and
fixed homeostatic planner. It contains no product-world truth, packet assignment,
diagnostic arm, or evaluator wrapper.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping, MutableMapping, Sequence


FEATURE_COUNT = 5
SLOT_COUNT = 3
TARGET = 0.72
ENERGY_SCALE = 0.035
SAFETY_SCALE = 0.03
PASSIVE_ENERGY_DECAY = 0.008
INTERACTION_ENERGY_COST = 0.004
REST_ENERGY_COST = 0.002
REST_SAFETY_GAIN = 0.015
TERMINAL_PENALTY = 2.0
INFORMATION_VALUE_PER_BIT = 0.08
ENERGY_NOISE_VALUES = (-0.14, -0.07, 0.0, 0.07, 0.14)
SAFETY_NOISE_VALUES = (-0.12, -0.06, 0.0, 0.06, 0.12)
NOISE_PROBABILITIES = (0.10, 0.20, 0.40, 0.20, 0.10)
LOCAL_MULTIPLIERS = (1, -1)
LOCAL_PRIOR = (0.75, 0.25)
LOCAL_NAMES = ("normal", "full_reverse")
ACTIONS = ("interact_0", "interact_1", "interact_2", "rest")
FORBIDDEN_CANDIDATE_FIELDS = (
    "token_id",
    "combo_id",
    "permutation",
    "mapping",
    "world_id",
    "layout_id",
    "seed",
    "split",
    "global_mechanism",
    "local_mode",
    "oracle_action",
    "future",
)


@dataclass(frozen=True)
class Mechanism:
    energy_weights: tuple[int, ...]
    safety_weights: tuple[int, ...]


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _rotate(values: Sequence[int], amount: int) -> tuple[int, ...]:
    amount %= len(values)
    return tuple(values[amount:]) + tuple(values[:amount])


def mechanism_family() -> tuple[Mechanism, ...]:
    energy_base = (2, 1, -1, -2, 1)
    safety_base = (-1, 2, 1, -1, -2)
    result: list[Mechanism] = []
    for swap in (False, True):
        first, second = (
            (safety_base, energy_base) if swap else (energy_base, safety_base)
        )
        for rotation in range(FEATURE_COUNT):
            rotated_energy = _rotate(first, rotation)
            rotated_safety = _rotate(second, rotation)
            for energy_sign in (1, -1):
                for safety_sign in (1, -1):
                    result.append(
                        Mechanism(
                            tuple(energy_sign * value for value in rotated_energy),
                            tuple(safety_sign * value for value in rotated_safety),
                        )
                    )
    if len(result) != 40 or len(set(result)) != 40:
        raise RuntimeError("shared mechanism construction is not 40-way unique")
    return tuple(result)


MECHANISMS = mechanism_family()


def _feature_tuple(features: Sequence[Any]) -> tuple[int, ...]:
    if len(features) != FEATURE_COUNT:
        raise ValueError(f"features must contain exactly {FEATURE_COUNT} entries")
    converted = tuple(int(value) for value in features)
    if any(value not in (0, 1) for value in converted):
        raise ValueError("feature entries must be binary")
    return converted


def latent_effect(
    mechanism: Mechanism, features: Sequence[Any], mode: str
) -> tuple[float, float]:
    feature_tuple = _feature_tuple(features)
    try:
        multiplier = LOCAL_MULTIPLIERS[LOCAL_NAMES.index(mode)]
    except ValueError as exc:
        raise ValueError("unknown local nuisance mode") from exc
    centered = tuple(2 * value - 1 for value in feature_tuple)
    energy = ENERGY_SCALE * sum(
        weight * value
        for weight, value in zip(mechanism.energy_weights, centered)
    )
    safety = SAFETY_SCALE * sum(
        weight * value
        for weight, value in zip(mechanism.safety_weights, centered)
    )
    return multiplier * energy, multiplier * safety


def _clamp01(value: float) -> float:
    return min(1.0, max(0.0, value))


def transition_delta(
    mechanism: Mechanism,
    features: Sequence[Any],
    mode: str,
    energy_before: float,
    safety_before: float,
    noise_energy: float,
    noise_safety: float,
) -> tuple[float, float]:
    latent_energy, latent_safety = latent_effect(mechanism, features, mode)
    energy_after = _clamp01(
        float(energy_before)
        + latent_energy
        - PASSIVE_ENERGY_DECAY
        - INTERACTION_ENERGY_COST
        + float(noise_energy)
    )
    safety_after = _clamp01(
        float(safety_before) + latent_safety + float(noise_safety)
    )
    return energy_after - float(energy_before), safety_after - float(safety_before)


def rest_delta(energy_before: float, safety_before: float) -> tuple[float, float]:
    energy_after = _clamp01(
        float(energy_before) - PASSIVE_ENERGY_DECAY - REST_ENERGY_COST
    )
    safety_after = _clamp01(float(safety_before) + REST_SAFETY_GAIN)
    return energy_after - float(energy_before), safety_after - float(safety_before)


def _scan_keys(payload: Any, path: str = "$") -> None:
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            lowered = str(key).lower()
            if lowered in FORBIDDEN_CANDIDATE_FIELDS:
                raise ValueError(f"private candidate field at {path}.{key}")
            _scan_keys(value, f"{path}.{key}")
    elif isinstance(payload, (list, tuple)):
        for index, value in enumerate(payload):
            _scan_keys(value, f"{path}[{index}]")


def validate_public_payload(payload: Any) -> None:
    _scan_keys(payload)
    if not isinstance(payload, Mapping):
        raise ValueError("public observation must be a mapping")
    if set(payload) != {"organism", "slots", "previous"}:
        raise ValueError("public observation schema mismatch")
    organism = payload.get("organism")
    slots = payload.get("slots")
    if not isinstance(organism, Mapping) or set(organism) != {
        "energy",
        "safety",
        "target",
    }:
        raise ValueError("public organism state missing")
    for name in ("energy", "safety", "target"):
        if not isinstance(organism[name], (int, float)):
            raise ValueError(f"public organism {name} missing")
    if not isinstance(slots, list) or len(slots) != SLOT_COUNT:
        raise ValueError(f"public observation must expose {SLOT_COUNT} slots")
    for slot in slots:
        if not isinstance(slot, Mapping) or set(slot) != {"features"}:
            raise ValueError("each public slot must expose only features")
        _feature_tuple(slot["features"])
    previous = payload["previous"]
    if previous is not None and not isinstance(previous, Mapping):
        raise ValueError("previous public transition must be null or an object")


def _normalise_joint(joint: Sequence[Sequence[float]]) -> list[list[float]]:
    total = sum(float(value) for row in joint for value in row)
    if total <= 0.0 or not math.isfinite(total):
        raise ValueError("posterior has zero or non-finite mass")
    return [[float(value) / total for value in row] for row in joint]


def new_learner_state(global_prior: Sequence[float] | None = None) -> dict[str, Any]:
    if global_prior is None:
        global_prior = [1.0 / len(MECHANISMS)] * len(MECHANISMS)
    if len(global_prior) != len(MECHANISMS):
        raise ValueError("shared prior length mismatch")
    joint = [
        [float(probability) * LOCAL_PRIOR[0], float(probability) * LOCAL_PRIOR[1]]
        for probability in global_prior
    ]
    state = {
        "joint": _normalise_joint(joint),
        "update_count": 0,
        "world_update_count": 0,
        "public_history_hash": canonical_hash([]),
    }
    validate_learner_state(state)
    return state


def validate_learner_state(state: Any) -> None:
    _scan_keys(state)
    if not isinstance(state, Mapping) or set(state) != {
        "joint",
        "update_count",
        "world_update_count",
        "public_history_hash",
    }:
        raise ValueError("learner state schema mismatch")
    joint = state.get("joint")
    if not isinstance(joint, list) or len(joint) != len(MECHANISMS):
        raise ValueError("learner joint shape mismatch")
    if any(
        not isinstance(row, list) or len(row) != len(LOCAL_NAMES) for row in joint
    ):
        raise ValueError("learner joint local shape mismatch")
    values = [float(value) for row in joint for value in row]
    if any(value < 0.0 or not math.isfinite(value) for value in values):
        raise ValueError("learner joint contains invalid probability")
    if not math.isclose(sum(values), 1.0, abs_tol=1e-9):
        raise ValueError("learner joint must sum to one")
    for field in ("update_count", "world_update_count"):
        if type(state.get(field)) is not int or int(state[field]) < 0:
            raise ValueError(f"learner {field} invalid")
    history_hash = state.get("public_history_hash")
    if not isinstance(history_hash, str) or len(history_hash) != 64:
        raise ValueError("learner public history hash invalid")


def state_hash(state: Mapping[str, Any]) -> str:
    validate_learner_state(state)
    return canonical_hash(state)


def shared_marginal(state: Mapping[str, Any]) -> list[float]:
    validate_learner_state(state)
    return [sum(float(value) for value in row) for row in state["joint"]]


def slow_state_hash(state: Mapping[str, Any]) -> str:
    return canonical_hash(
        {
            "shared_marginal": shared_marginal(state),
            "update_count": int(state["update_count"]),
        }
    )


def fast_state_hash(state: Mapping[str, Any]) -> str:
    validate_learner_state(state)
    return canonical_hash(
        {
            "local_marginal": [
                sum(float(row[index]) for row in state["joint"])
                for index in range(len(LOCAL_NAMES))
            ],
            "world_update_count": int(state["world_update_count"]),
        }
    )


def posterior_entropy(state: Mapping[str, Any]) -> float:
    validate_learner_state(state)
    return -sum(
        probability * math.log2(probability)
        for row in state["joint"]
        for probability in row
        if probability > 0.0
    )


def reset_for_world(state: MutableMapping[str, Any]) -> dict[str, Any]:
    before = state_hash(state)
    replacement = new_learner_state(shared_marginal(state))
    replacement["update_count"] = int(state["update_count"])
    state.clear()
    state.update(replacement)
    return {
        "state_hash_before": before,
        "state_hash_after": state_hash(state),
        "slow_state_hash_after": slow_state_hash(state),
        "fast_state_hash_after": fast_state_hash(state),
    }


def _feedback_values(feedback: Mapping[str, Any]) -> tuple[float, float, float, float]:
    _scan_keys(feedback)
    required = {
        "energy_before",
        "safety_before",
        "energy_after",
        "safety_after",
        "died",
    }
    if not isinstance(feedback, Mapping) or set(feedback) != required:
        raise ValueError("public transition feedback incomplete")
    return (
        float(feedback["energy_before"]),
        float(feedback["safety_before"]),
        float(feedback["energy_after"]),
        float(feedback["safety_after"]),
    )


def _outcome_key(energy_after: float, safety_after: float) -> tuple[float, float]:
    return round(float(energy_after), 12), round(float(safety_after), 12)


def _likelihood_for(
    mechanism_index: int,
    mode_index: int,
    features: Sequence[Any],
    energy_before: float,
    safety_before: float,
    energy_after: float,
    safety_after: float,
) -> float:
    likelihood = 0.0
    for noise_energy, probability_energy in zip(
        ENERGY_NOISE_VALUES, NOISE_PROBABILITIES
    ):
        for noise_safety, probability_safety in zip(
            SAFETY_NOISE_VALUES, NOISE_PROBABILITIES
        ):
            delta_energy, delta_safety = transition_delta(
                MECHANISMS[mechanism_index],
                features,
                LOCAL_NAMES[mode_index],
                energy_before,
                safety_before,
                noise_energy,
                noise_safety,
            )
            predicted = _outcome_key(
                energy_before + delta_energy, safety_before + delta_safety
            )
            if predicted == _outcome_key(energy_after, safety_after):
                likelihood += probability_energy * probability_safety
    return likelihood


def update_after_transition(
    state: MutableMapping[str, Any],
    observation: Mapping[str, Any],
    action: str,
    feedback: Mapping[str, Any],
) -> dict[str, Any]:
    validate_learner_state(state)
    validate_public_payload(observation)
    energy_before, safety_before, energy_after, safety_after = _feedback_values(
        feedback
    )
    before_hash = state_hash(state)
    if action == "rest":
        expected_delta = rest_delta(energy_before, safety_before)
        predicted = _outcome_key(
            energy_before + expected_delta[0], safety_before + expected_delta[1]
        )
        if predicted != _outcome_key(energy_after, safety_after):
            raise ValueError("rest feedback is inconsistent with public grammar")
        likelihood_joint = [list(row) for row in state["joint"]]
        public_features: list[int] | None = None
    elif action.startswith("interact_"):
        try:
            slot_index = int(action.rsplit("_", 1)[1])
        except (ValueError, IndexError) as exc:
            raise ValueError("invalid public interaction action") from exc
        if not 0 <= slot_index < SLOT_COUNT:
            raise ValueError("public interaction slot outside observation")
        public_features = list(
            _feature_tuple(observation["slots"][slot_index]["features"])
        )
        likelihood_joint = []
        for mechanism_index, row in enumerate(state["joint"]):
            likelihood_joint.append(
                [
                    float(row[mode_index])
                    * _likelihood_for(
                        mechanism_index,
                        mode_index,
                        public_features,
                        energy_before,
                        safety_before,
                        energy_after,
                        safety_after,
                    )
                    for mode_index in range(len(LOCAL_NAMES))
                ]
            )
    else:
        raise ValueError("action is outside public action semantics")
    state["joint"] = _normalise_joint(likelihood_joint)
    state["update_count"] = int(state["update_count"]) + 1
    state["world_update_count"] = int(state["world_update_count"]) + 1
    public_event = {
        "previous_hash": state.get("public_history_hash"),
        "action": action,
        "features": public_features,
        "feedback": {
            name: feedback[name]
            for name in (
                "energy_before",
                "safety_before",
                "energy_after",
                "safety_after",
                "died",
            )
        },
    }
    state["public_history_hash"] = canonical_hash(public_event)
    validate_learner_state(state)
    return {
        "applied": True,
        "state_hash_before": before_hash,
        "state_hash_after": state_hash(state),
        "slow_state_hash_after": slow_state_hash(state),
        "fast_state_hash_after": fast_state_hash(state),
        "posterior_entropy_bits": posterior_entropy(state),
        "public_input_receipt": canonical_hash(
            {"observation": observation, "action": action, "feedback": feedback}
        ),
    }


def _deficit(energy: float, safety: float, target: float) -> float:
    return max(0.0, target - energy) + max(0.0, target - safety)


def _predict_interaction(
    state: Mapping[str, Any],
    features: Sequence[Any],
    energy: float,
    safety: float,
    target: float,
) -> dict[str, Any]:
    outcomes: dict[tuple[float, float], dict[str, Any]] = {}
    for mechanism_index, row in enumerate(state["joint"]):
        for mode_index, hypothesis_probability in enumerate(row):
            if hypothesis_probability <= 0.0:
                continue
            for noise_energy, probability_energy in zip(
                ENERGY_NOISE_VALUES, NOISE_PROBABILITIES
            ):
                for noise_safety, probability_safety in zip(
                    SAFETY_NOISE_VALUES, NOISE_PROBABILITIES
                ):
                    delta_energy, delta_safety = transition_delta(
                        MECHANISMS[mechanism_index],
                        features,
                        LOCAL_NAMES[mode_index],
                        energy,
                        safety,
                        noise_energy,
                        noise_safety,
                    )
                    energy_after = energy + delta_energy
                    safety_after = safety + delta_safety
                    key = _outcome_key(energy_after, safety_after)
                    probability = (
                        float(hypothesis_probability)
                        * probability_energy
                        * probability_safety
                    )
                    entry = outcomes.setdefault(
                        key,
                        {
                            "probability": 0.0,
                            "hypothesis_mass": [
                                0.0
                            ]
                            * (len(MECHANISMS) * len(LOCAL_NAMES)),
                        },
                    )
                    entry["probability"] += probability
                    entry["hypothesis_mass"][mechanism_index * 2 + mode_index] += (
                        probability
                    )
    expected_deficit = 0.0
    terminal_risk = 0.0
    expected_entropy = 0.0
    expected_energy = 0.0
    expected_safety = 0.0
    for (energy_after, safety_after), entry in outcomes.items():
        probability = float(entry["probability"])
        expected_energy += probability * energy_after
        expected_safety += probability * safety_after
        expected_deficit += probability * _deficit(
            energy_after, safety_after, target
        )
        if energy_after <= 0.0 or safety_after <= 0.0:
            terminal_risk += probability
        conditional = [
            mass / probability
            for mass in entry["hypothesis_mass"]
            if mass > 0.0
        ]
        entropy = -sum(value * math.log2(value) for value in conditional)
        expected_entropy += probability * entropy
    information_gain = max(0.0, posterior_entropy(state) - expected_entropy)
    return {
        "expected_energy": expected_energy,
        "expected_safety": expected_safety,
        "expected_deficit": expected_deficit,
        "terminal_risk": terminal_risk,
        "information_gain_bits": information_gain,
        "outcome_count": len(outcomes),
    }


def action_predictions(
    state: Mapping[str, Any], observation: Mapping[str, Any]
) -> dict[str, dict[str, Any]]:
    validate_learner_state(state)
    validate_public_payload(observation)
    organism = observation["organism"]
    energy = float(organism["energy"])
    safety = float(organism["safety"])
    target = float(organism["target"])
    result: dict[str, dict[str, Any]] = {}
    for slot_index, slot in enumerate(observation["slots"]):
        result[f"interact_{slot_index}"] = _predict_interaction(
            state, slot["features"], energy, safety, target
        )
    delta_energy, delta_safety = rest_delta(energy, safety)
    rest_energy = energy + delta_energy
    rest_safety = safety + delta_safety
    result["rest"] = {
        "expected_energy": rest_energy,
        "expected_safety": rest_safety,
        "expected_deficit": _deficit(rest_energy, rest_safety, target),
        "terminal_risk": float(rest_energy <= 0.0 or rest_safety <= 0.0),
        "information_gain_bits": 0.0,
        "outcome_count": 1,
    }
    for prediction in result.values():
        prediction["score"] = (
            prediction["expected_deficit"]
            + TERMINAL_PENALTY * prediction["terminal_risk"]
            - INFORMATION_VALUE_PER_BIT * prediction["information_gain_bits"]
        )
        for key, value in tuple(prediction.items()):
            if isinstance(value, float):
                prediction[key] = round(value, 12)
    return result


def plan_action(state: Mapping[str, Any], observation: Mapping[str, Any]) -> dict[str, Any]:
    predictions = action_predictions(state, observation)
    ranking = sorted(
        ACTIONS, key=lambda action: (predictions[action]["score"], action)
    )
    organism = observation["organism"]
    energy_deficit = max(
        0.0, float(organism["target"]) - float(organism["energy"])
    )
    safety_deficit = max(
        0.0, float(organism["target"]) - float(organism["safety"])
    )
    primary = (
        "energy"
        if energy_deficit > safety_deficit
        else "safety"
        if safety_deficit > energy_deficit
        else "tied"
    )
    return {
        "action": ranking[0],
        "ranking": ranking,
        "predictions": predictions,
        "reason": {
            "primary_deficit": primary,
            "energy_deficit": energy_deficit,
            "safety_deficit": safety_deficit,
            "selected_score": predictions[ranking[0]]["score"],
            "uncertainty_entropy_bits": posterior_entropy(state),
        },
    }


def hyperparameters() -> dict[str, Any]:
    return {
        "schema_version": "ego.life_playground.public_featured_learner_hparams.v1",
        "hypothesis_count": len(MECHANISMS),
        "feature_count": FEATURE_COUNT,
        "slot_count": SLOT_COUNT,
        "actions": list(ACTIONS),
        "local_prior": list(LOCAL_PRIOR),
        "target": TARGET,
        "terminal_penalty": TERMINAL_PENALTY,
        "information_value_per_bit": INFORMATION_VALUE_PER_BIT,
    }
