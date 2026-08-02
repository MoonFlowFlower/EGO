"""Private product-world primitives for the public-featured successor.

The environment owns realized truth and deterministic private entropy. Public
observations and receipts deliberately exclude those fields. State mutation and
trace assembly remain owned by ``engine.compute_step``.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import math
from typing import Any, Mapping, Sequence

from . import public_featured_hierarchical as learner


ENVIRONMENT_SCHEMA_VERSION = "ego.life_playground.public_featured_environment.v1"
PRODUCT_STATE_SCHEMA_VERSION = "ego.life_playground.public_featured_product_state.v1"
PRIVATE_SHARED_RULE_INDEX = 17
INITIAL_ENERGY = 0.5
INITIAL_SAFETY = 0.5
_WEIGHTED_NOISE_INDICES = (0, 1, 1, 2, 2, 2, 2, 3, 3, 4)


def _stable_int(*parts: Any) -> int:
    digest = hashlib.sha256(
        "|".join(str(part) for part in parts).encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big")


def combo_bits(index: int) -> tuple[int, ...]:
    if type(index) is not int or not 0 <= index < 2**learner.FEATURE_COUNT:
        raise ValueError("feature combination index must be in [0, 31]")
    return tuple(
        (index >> (learner.FEATURE_COUNT - 1 - axis)) & 1
        for axis in range(learner.FEATURE_COUNT)
    )


def _local_mode(entropy_hash: str, world_epoch: int) -> str:
    return "full_reverse" if _stable_int(entropy_hash, world_epoch, "mode") % 4 == 0 else "normal"


def _slot_indices(entropy_hash: str, world_epoch: int, step: int) -> list[int]:
    selected: list[int] = []
    cursor = 0
    while len(selected) < learner.SLOT_COUNT:
        value = _stable_int(entropy_hash, world_epoch, step, "slot", cursor) % (
            2**learner.FEATURE_COUNT
        )
        if value not in selected:
            selected.append(value)
        cursor += 1
    return selected


def initial_environment(private_entropy: Any) -> dict[str, Any]:
    entropy_hash = hashlib.sha256(str(private_entropy).encode("utf-8")).hexdigest()
    environment = {
        "schema_version": ENVIRONMENT_SCHEMA_VERSION,
        "private_entropy_hash": entropy_hash,
        "world_epoch": 0,
        "step": 0,
        "local_mode": _local_mode(entropy_hash, 0),
        "slot_indices": _slot_indices(entropy_hash, 0, 0),
    }
    validate_environment(environment)
    return environment


def validate_environment(environment: Any) -> None:
    required = {
        "schema_version",
        "private_entropy_hash",
        "world_epoch",
        "step",
        "local_mode",
        "slot_indices",
    }
    if not isinstance(environment, Mapping) or set(environment) != required:
        raise ValueError("featured environment schema mismatch")
    if environment["schema_version"] != ENVIRONMENT_SCHEMA_VERSION:
        raise ValueError("featured environment version mismatch")
    entropy_hash = environment["private_entropy_hash"]
    if not isinstance(entropy_hash, str) or len(entropy_hash) != 64:
        raise ValueError("featured environment entropy receipt invalid")
    for field in ("world_epoch", "step"):
        if type(environment[field]) is not int or int(environment[field]) < 0:
            raise ValueError(f"featured environment {field} invalid")
    if environment["local_mode"] not in learner.LOCAL_NAMES:
        raise ValueError("featured environment local mode invalid")
    indices = environment["slot_indices"]
    if (
        not isinstance(indices, list)
        or len(indices) != learner.SLOT_COUNT
        or len(set(indices)) != learner.SLOT_COUNT
        or any(type(value) is not int or not 0 <= value < 32 for value in indices)
    ):
        raise ValueError("featured environment slot indices invalid")
    expected = _slot_indices(
        entropy_hash, int(environment["world_epoch"]), int(environment["step"])
    )
    if indices != expected:
        raise ValueError("featured environment slots do not match private entropy")
    if environment["local_mode"] != _local_mode(
        entropy_hash, int(environment["world_epoch"])
    ):
        raise ValueError("featured environment nuisance does not match private entropy")


def public_observation(
    environment: Mapping[str, Any],
    organism: Mapping[str, float],
    *,
    previous: Mapping[str, Any] | None,
) -> dict[str, Any]:
    validate_environment(environment)
    observation = {
        "organism": {
            "energy": float(organism["energy"]),
            "safety": float(organism["safety"]),
            "target": float(organism.get("target", learner.TARGET)),
        },
        "slots": [
            {"features": list(combo_bits(index))}
            for index in environment["slot_indices"]
        ],
        "previous": None if previous is None else deepcopy(dict(previous)),
    }
    learner.validate_public_payload(observation)
    return observation


def _noise_value(values: Sequence[float], *parts: Any) -> float:
    bucket = _stable_int(*parts) % len(_WEIGHTED_NOISE_INDICES)
    return float(values[_WEIGHTED_NOISE_INDICES[bucket]])


def apply_action(
    environment: Mapping[str, Any],
    observation: Mapping[str, Any],
    action: str,
    *,
    private_step_entropy: Any,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    validate_environment(environment)
    learner.validate_public_payload(observation)
    expected_slots = public_observation(
        environment, observation["organism"], previous=observation["previous"]
    )["slots"]
    if learner.canonical_json(observation["slots"]) != learner.canonical_json(
        expected_slots
    ):
        raise ValueError("public slots do not match current featured environment")
    energy_before = float(observation["organism"]["energy"])
    safety_before = float(observation["organism"]["safety"])
    selected_features: list[int] | None
    if action == "rest":
        delta_energy, delta_safety = learner.rest_delta(energy_before, safety_before)
        selected_features = None
    elif action.startswith("interact_"):
        try:
            slot_index = int(action.rsplit("_", 1)[1])
        except (ValueError, IndexError) as exc:
            raise ValueError("featured action invalid") from exc
        if not 0 <= slot_index < learner.SLOT_COUNT:
            raise ValueError("featured action slot invalid")
        selected_features = list(observation["slots"][slot_index]["features"])
        entropy_parts = (
            environment["private_entropy_hash"],
            environment["world_epoch"],
            environment["step"],
            action,
            private_step_entropy,
        )
        noise_energy = _noise_value(
            learner.ENERGY_NOISE_VALUES, *entropy_parts, "energy"
        )
        noise_safety = _noise_value(
            learner.SAFETY_NOISE_VALUES, *entropy_parts, "safety"
        )
        delta_energy, delta_safety = learner.transition_delta(
            learner.MECHANISMS[PRIVATE_SHARED_RULE_INDEX],
            selected_features,
            str(environment["local_mode"]),
            energy_before,
            safety_before,
            noise_energy,
            noise_safety,
        )
    else:
        raise ValueError("featured action outside public grammar")
    energy_after = energy_before + delta_energy
    safety_after = safety_before + delta_safety
    if not all(math.isfinite(value) for value in (energy_after, safety_after)):
        raise ValueError("featured transition produced non-finite organism state")
    died = energy_after <= 0.0 or safety_after <= 0.0
    feedback = {
        "energy_before": energy_before,
        "safety_before": safety_before,
        "energy_after": energy_after,
        "safety_after": safety_after,
        "died": died,
    }
    next_environment = deepcopy(dict(environment))
    next_environment["step"] = int(environment["step"]) + 1
    next_environment["slot_indices"] = _slot_indices(
        str(environment["private_entropy_hash"]),
        int(environment["world_epoch"]),
        int(next_environment["step"]),
    )
    validate_environment(next_environment)
    public_receipt = {
        "action": action,
        "selected_features": selected_features,
        "actual_delta": {
            "energy": energy_after - energy_before,
            "safety": safety_after - safety_before,
        },
        "died": died,
    }
    public_receipt["receipt_hash"] = learner.canonical_hash(public_receipt)
    return next_environment, feedback, public_receipt


def reset_environment_for_world(environment: Mapping[str, Any]) -> dict[str, Any]:
    validate_environment(environment)
    entropy_hash = str(environment["private_entropy_hash"])
    world_epoch = int(environment["world_epoch"]) + 1
    replacement = {
        "schema_version": ENVIRONMENT_SCHEMA_VERSION,
        "private_entropy_hash": entropy_hash,
        "world_epoch": world_epoch,
        "step": 0,
        "local_mode": _local_mode(entropy_hash, world_epoch),
        "slot_indices": _slot_indices(entropy_hash, world_epoch, 0),
    }
    validate_environment(replacement)
    return replacement


def new_product_state(*, active: bool, private_entropy: Any) -> dict[str, Any]:
    state = {
        "schema_version": PRODUCT_STATE_SCHEMA_VERSION,
        "active": bool(active),
        "learner": learner.new_learner_state(),
        "environment": initial_environment(private_entropy),
        "previous": None,
        "world_switch_count": 0,
    }
    validate_product_state(state)
    return state


def validate_product_state(state: Any) -> None:
    required = {
        "schema_version",
        "active",
        "learner",
        "environment",
        "previous",
        "world_switch_count",
    }
    if not isinstance(state, Mapping) or set(state) != required:
        raise ValueError("featured product state schema mismatch")
    if state["schema_version"] != PRODUCT_STATE_SCHEMA_VERSION:
        raise ValueError("featured product state version mismatch")
    if type(state["active"]) is not bool:
        raise ValueError("featured product active flag invalid")
    learner.validate_learner_state(state["learner"])
    validate_environment(state["environment"])
    if state["previous"] is not None:
        learner._scan_keys(state["previous"])
        if not isinstance(state["previous"], Mapping):
            raise ValueError("featured previous public result invalid")
    if type(state["world_switch_count"]) is not int or state["world_switch_count"] < 0:
        raise ValueError("featured world switch count invalid")
    if int(state["environment"]["world_epoch"]) != state["world_switch_count"]:
        raise ValueError("featured world switch count mismatch")


def product_state_hash(state: Mapping[str, Any]) -> str:
    validate_product_state(state)
    return learner.canonical_hash(state)


def reset_product_for_world(state: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    validate_product_state(state)
    replacement = deepcopy(dict(state))
    slow_before = learner.slow_state_hash(replacement["learner"])
    reset_receipt = learner.reset_for_world(replacement["learner"])
    replacement["environment"] = reset_environment_for_world(
        replacement["environment"]
    )
    replacement["previous"] = None
    replacement["world_switch_count"] = int(state["world_switch_count"]) + 1
    validate_product_state(replacement)
    receipt = {
        "slow_state_preserved": learner.slow_state_hash(replacement["learner"])
        == slow_before,
        "fast_state_reset": True,
        "world_switch_count": replacement["world_switch_count"],
        "learner_reset": reset_receipt,
        "state_hash_after": product_state_hash(replacement),
    }
    return replacement, receipt


def hyperparameters() -> dict[str, Any]:
    return {
        "schema_version": "ego.life_playground.public_featured_world_hparams.v1",
        "environment_schema": ENVIRONMENT_SCHEMA_VERSION,
        "product_state_schema": PRODUCT_STATE_SCHEMA_VERSION,
        "initial_energy": INITIAL_ENERGY,
        "initial_safety": INITIAL_SAFETY,
        "learner": learner.hyperparameters(),
    }
